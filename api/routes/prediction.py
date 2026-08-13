from pathlib import Path
import tempfile

from fastapi import (
    APIRouter,
    UploadFile,
    File,
    HTTPException
)

from api.schemas.prediction import (
    ApplePredictionResponse
)

from api.services.prediction_service import (
    PredictionService
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/predict",
    tags=["Prediction"]
)


# ============================================================
# SERVICE
# ============================================================

prediction_service = (
    PredictionService()
)


# ============================================================
# APPLE PREDICTION
# ============================================================

@router.post(
    "/apple",
    response_model=ApplePredictionResponse
)
async def predict_apple(
    file: UploadFile = File(...)
):

    # ========================================================
    # VALIDATE CONTENT TYPE
    # ========================================================

    allowed_content_types = {

        "image/jpeg",

        "image/png",

        "image/webp"
    }

    if file.content_type not in (
        allowed_content_types
    ):

        raise HTTPException(

            status_code=400,

            detail=(
                "Invalid image format. "
                "Supported formats: "
                "JPEG, PNG, WEBP."
            )
        )

    # ========================================================
    # READ IMAGE
    # ========================================================

    contents = await file.read()

    if not contents:

        raise HTTPException(

            status_code=400,

            detail="Uploaded image is empty."
        )

    # ========================================================
    # CREATE TEMPORARY FILE
    # ========================================================

    suffix = (
        Path(
            file.filename
            or "apple.jpg"
        ).suffix
        or ".jpg"
    )

    temporary_path = None

    try:

        with tempfile.NamedTemporaryFile(
            suffix=suffix,
            delete=False
        ) as temporary_file:

            temporary_file.write(
                contents
            )

            temporary_path = (
                temporary_file.name
            )

        # ====================================================
        # RUN AI
        # ====================================================

        prediction = (
            prediction_service.predict_apple(
                temporary_path
            )
        )

        # ====================================================
        # RESPONSE
        # ====================================================

        return {

            "success": True,

            "fruit":
                prediction["fruit"],

            "freshness":
                prediction["freshness"],

            "shelf_life":
                prediction["shelf_life"]
        }

    except FileNotFoundError as exc:

        raise HTTPException(

            status_code=500,

            detail=str(exc)
        )

    except Exception as exc:

        raise HTTPException(

            status_code=500,

            detail=(
                "Apple prediction failed: "
                f"{str(exc)}"
            )
        )

    finally:

        # ====================================================
        # DELETE TEMPORARY IMAGE
        # ====================================================

        if temporary_path:

            temporary_file = Path(
                temporary_path
            )

            if temporary_file.exists():

                temporary_file.unlink()