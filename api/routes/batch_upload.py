from pathlib import Path
from datetime import datetime
import tempfile

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File,
    Form,
    status
)
from sqlalchemy.orm import Session

from api.database.database import get_db
from api.database.models import (
    User,
    BatchStatusHistory,
    BatchImage
)
from api.auth.dependencies import (
    get_current_user
)
from api.services.batch_service import (
    BatchService
)
from api.services.yolo_services import (
    YOLOService
)
from api.services.status_service import (
    StatusService
)

from api.services.prediction_service import (
    PredictionService
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/batch-upload",
    tags=["Batch Upload & Detection"]
)


# ============================================================
# SERVICES
# ============================================================

batch_service = BatchService()

status_service = StatusService()

prediction_service = PredictionService()

# Lazy-load YOLO to avoid startup delay
_yolo_service = None


def get_yolo_service():
    global _yolo_service
    if _yolo_service is None:
        _yolo_service = YOLOService()
    return _yolo_service


# ============================================================
# UPLOAD BATCH WITH YOLO DETECTION
# ============================================================

@router.post(
    "",
    summary=(
        "Upload multiple images for apple "
        "detection and batch creation"
    ),
    status_code=status.HTTP_201_CREATED
)
async def upload_batch(
    batch_id: str = Form(
        ...,
        description="Unique batch identifier"
    ),
    origin: str = Form(
        ...,
        description="Origin address"
    ),
    current_address: str | None = Form(
        default=None,
        description="Current address"
    ),
    files: list[UploadFile] = File(
        ...,
        description=(
            "Multiple image files "
            "(JPEG, PNG, WEBP)"
        )
    ),
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db)
):

    # ----------------------------------------------------
    # Validate batch_id
    # ----------------------------------------------------

    batch_id = batch_id.strip()

    if not batch_id:

        raise HTTPException(
            status_code=400,
            detail="Batch ID cannot be empty."
        )

    # ----------------------------------------------------
    # Check duplicate batch
    # ----------------------------------------------------

    existing = (
        batch_service.get_batch(
            db, batch_id
        )
    )

    if existing:

        raise HTTPException(
            status_code=409,
            detail=(
                f"Batch '{batch_id}' "
                "already exists."
            )
        )

    # ----------------------------------------------------
    # Validate files
    # ----------------------------------------------------

    if not files:

        raise HTTPException(
            status_code=400,
            detail="No files uploaded."
        )

    allowed_content_types = {
        "image/jpeg",
        "image/png",
        "image/webp"
    }

    for file in files:

        if (
            file.content_type
            not in allowed_content_types
        ):

            raise HTTPException(
                status_code=400,
                detail=(
                    f"Invalid image format: "
                    f"{file.filename}. "
                    "Supported: JPEG, PNG, WEBP."
                )
            )

    # ----------------------------------------------------
    # Process each image with YOLO
    # ----------------------------------------------------

    yolo = get_yolo_service()

    # Prepare persistent storage for images
    project_root = Path(__file__).resolve().parents[2]
    uploads_base = project_root / "uploads" / "batches" / batch_id
    original_dir = uploads_base / "original"
    annotated_dir = uploads_base / "annotated"
    original_dir.mkdir(parents=True, exist_ok=True)
    annotated_dir.mkdir(parents=True, exist_ok=True)

    total_apples = 0
    image_results = []
    freshness_preds = []
    freshness_confs = []
    shelf_life_preds = []
    shelf_life_confs = []

    try:

        for file in files:

            contents = await file.read()

            if not contents:
                continue

            suffix = (
                Path(file.filename or "apple.jpg").suffix or ".jpg"
            )
            # Save original image permanently
            safe_name = f"{Path(file.filename or 'apple.jpg').stem}_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}{suffix}"
            save_path = original_dir / safe_name
            with open(save_path, 'wb') as f:
                f.write(contents)

            # ------------------------------------
            # Run YOLO detection
            # ------------------------------------

            apples = yolo.detect_apples(
                image_path=str(save_path),
                confidence_threshold=0.25
            )

            apple_count = len(apples)

            # Per-image detection logging
            confidences = [a["confidence"] for a in apples]
            print(f"[YOLO Batch Detection] Image: {file.filename}, Apple count: {apple_count}, Confidences: {[round(c,4) for c in confidences]}")

            # Run freshness and shelf-life prediction per image
            try:
                pred = prediction_service.predict_apple(str(save_path))
                freshness_preds.append(pred["freshness"]["prediction"])
                freshness_confs.append(pred["freshness"]["confidence"])
                shelf_life_preds.append(pred["shelf_life"]["prediction"])
                shelf_life_confs.append(pred["shelf_life"]["confidence"])
            except Exception as e:
                print(f"[Prediction Error] Image {file.filename}: {e}")

            total_apples += apple_count

            avg_confidence = 0.0

            if apples:

                avg_confidence = (
                    sum(
                        a["confidence"]
                        for a in apples
                    ) / len(apples)
                )

            image_results.append({

                "image_name":
                    safe_name,

                "apple_count":
                    apple_count,

                "average_confidence":
                    round(
                        avg_confidence, 4
                    ),
                "original_path": str(save_path)
            })

    except Exception:
        pass

    # Batch detection summary logging
    print(f"[YOLO Batch Detection] Batch ID: {batch_id}, Total images: {len(files)}, Total apples detected: {total_apples}")

    # Aggregate predictions across images
    if freshness_preds:
        from collections import Counter
        freshness_counter = Counter(freshness_preds)
        freshness_prediction = freshness_counter.most_common(1)[0][0]
        freshness_confidence = sum(freshness_confs) / len(freshness_confs)
    else:
        freshness_prediction = "N/A"
        freshness_confidence = 0.0

    if shelf_life_preds:
        from collections import Counter
        shelf_life_counter = Counter(shelf_life_preds)
        shelf_life_prediction = shelf_life_counter.most_common(1)[0][0]
        shelf_life_confidence = sum(shelf_life_confs) / len(shelf_life_confs)
    else:
        shelf_life_prediction = "N/A"
        shelf_life_confidence = 0.0

    # ----------------------------------------------------
    # Create batch record
    # ----------------------------------------------------

    batch_dict = {

        "batch_id": batch_id,
        "fruit": "apple",
        "origin": origin,
        "current_address": current_address,
        "freshness_prediction": freshness_prediction,
        "freshness_confidence": freshness_confidence,
        "shelf_life_prediction": shelf_life_prediction,
        "shelf_life_confidence": shelf_life_confidence,
        "quality_status": "PENDING",
        "risk_level": "PENDING",
        "batch_status": "DETECTED",

        # New fields
        "user_id": current_user.user_id,
        "number_of_images": len(files),
        "total_apples_detected": total_apples
    }

    try:

        new_batch = (
            batch_service.create_batch(
                db, batch_dict
            )
        )

    except ValueError as exc:

        db.rollback()

        raise HTTPException(
            status_code=409,
            detail=str(exc)
        )

    except Exception as exc:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                "Batch creation failed: "
                f"{str(exc)}"
            )
        )

    # ----------------------------------------------------
    # Save image records
    # ----------------------------------------------------
    for img in image_results:
        batch_image = BatchImage(
            batch_id=batch_id,
            filename=img["image_name"],
            original_path=img.get("original_path", ""),
            apple_count=img["apple_count"],
            average_confidence=img["average_confidence"]
        )
        db.add(batch_image)
    db.commit()

    # ----------------------------------------------------
    # Record status in history
    # ----------------------------------------------------

    history = BatchStatusHistory(
        batch_id=batch_id,
        previous_status=None,
        new_status="DETECTED",
        action="YOLO detection completed",
        actor=current_user.user_id
    )

    db.add(history)
    db.commit()

    return {

        "success": True,

        "message": (
            "Batch created with "
            "YOLO detection results."
        ),

        "batch": {

            "id": new_batch.id,
            "batch_id": new_batch.batch_id,
            "user_id":
                current_user.user_id,
            "batch_status":
                new_batch.batch_status,
            "number_of_images":
                len(files),
            "total_apples_detected":
                total_apples
        },

        "detection_results": {

            "total_images": len(files),
            "total_apples_detected":
                total_apples,
            "average_apples_per_image":
                round(
                    total_apples / len(files),
                    2
                ) if files else 0,
            "images": image_results
        }
    }
