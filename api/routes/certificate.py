from pathlib import Path
import tempfile

from fastapi import (
    APIRouter,
    UploadFile,
    File,
    Form,
    HTTPException,
    Depends
)

from sqlalchemy.orm import Session

from api.database.database import get_db

from api.services.prediction_service import (
    PredictionService
)

from api.services.llm_service import (
    LLMService
)

from api.services.certificate_service import (
    CertificateService
)

from api.services.batch_service import (
    BatchService
)



router = APIRouter(
    prefix="/certificate",
    tags=["Digital Birth Certificate"]
)




prediction_service = PredictionService()

llm_service = LLMService()

certificate_service = CertificateService(
    llm_service=llm_service
)

batch_service = BatchService()




@router.post("/apple")
async def create_apple_certificate(

    file: UploadFile = File(...),

    batch_id: str = Form(...),

    origin: str = Form(...),

    current_address: str | None = Form(
        default=None
    ),

    db: Session = Depends(get_db)
):


    allowed_content_types = {
        "image/jpeg",
        "image/png",
        "image/webp"
    }

    if file.content_type not in allowed_content_types:

        raise HTTPException(

            status_code=400,

            detail=(
                "Invalid image format. "
                "Supported formats: "
                "JPEG, PNG and WEBP."
            )
        )




    batch_id = batch_id.strip()

    if not batch_id:

        raise HTTPException(

            status_code=400,

            detail="Batch ID cannot be empty."
        )


    

    origin = origin.strip()

    if not origin:

        raise HTTPException(

            status_code=400,

            detail="Origin cannot be empty."
        )



    existing_batch = (
        batch_service.get_batch(
            db,
            batch_id
        )
    )

    if existing_batch:

        raise HTTPException(

            status_code=409,

            detail=(
                f"Batch '{batch_id}' "
                "already exists."
            )
        )


    

    contents = await file.read()

    if not contents:

        raise HTTPException(

            status_code=400,

            detail="Uploaded image is empty."
        )


  

    suffix = (

        Path(
            file.filename or "apple.jpg"
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


   

        prediction = (
            prediction_service.predict_apple(
                temporary_path
            )
        )



        certificate = (
            certificate_service.create_certificate(

                prediction=prediction,

                batch_id=batch_id,

                origin=origin
            )
        )


       
        certificate["current_address"] = (
            current_address.strip()
            if current_address
            else None
        )


       

        batch = (
            batch_service.create_batch(
                db,
                certificate
            )
        )


        return {

            "success": True,

            "message": (
                "Digital Birth Certificate "
                "created and batch saved "
                "successfully."
            ),

            "certificate": certificate,

            "batch": {

                "id":
                    batch.id,

                "batch_id":
                    batch.batch_id,

                "status":
                    batch.batch_status,

                "current_address":
                    batch.current_address
            }
        }


    except ValueError as exc:

        db.rollback()

        raise HTTPException(

            status_code=409,

            detail=str(exc)
        )


    except FileNotFoundError as exc:

        db.rollback()

        raise HTTPException(

            status_code=500,

            detail=str(exc)
        )


    except Exception as exc:

        db.rollback()

        raise HTTPException(

            status_code=500,

            detail=(
                "Certificate and batch "
                "creation failed: "
                f"{str(exc)}"
            )
        )


    finally:

      

        if temporary_path:

            temporary_file = Path(
                temporary_path
            )

            if temporary_file.exists():

                temporary_file.unlink()