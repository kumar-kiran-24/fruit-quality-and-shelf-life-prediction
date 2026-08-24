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
    BatchStatusHistory
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

    total_apples = 0

    image_results = []

    temporary_paths = []

    try:

        for file in files:

            contents = await file.read()

            if not contents:
                continue

            suffix = (
                Path(
                    file.filename or "apple.jpg"
                ).suffix
                or ".jpg"
            )

            with tempfile.NamedTemporaryFile(
                suffix=suffix,
                delete=False
            ) as tmp:

                tmp.write(contents)

                tmp_path = tmp.name

            temporary_paths.append(tmp_path)

            # ------------------------------------
            # Run YOLO detection
            # ------------------------------------

            apples = (
                yolo.detect_apples(
                    image_path=tmp_path,
                    confidence_threshold=0.25
                )
            )

            apple_count = len(apples)

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
                    file.filename,

                "apple_count":
                    apple_count,

                "average_confidence":
                    round(
                        avg_confidence, 4
                    )
            })

    finally:

        for path in temporary_paths:

            p = Path(path)

            if p.exists():
                p.unlink()

    # ----------------------------------------------------
    # Create batch record
    # ----------------------------------------------------

    batch_dict = {

        "batch_id": batch_id,
        "fruit": "apple",
        "origin": origin,
        "current_address": current_address,
        "freshness_prediction": "N/A",
        "freshness_confidence": 0.0,
        "shelf_life_prediction": "N/A",
        "shelf_life_confidence": 0.0,
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
