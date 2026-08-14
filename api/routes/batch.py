from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)

from sqlalchemy.orm import Session

from api.database.database import get_db

from api.schemas.batch import (
    BatchResponse
)

from api.services.batch_service import (
    BatchService
)

from api.services.fefo_service import (
    FEFOService
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(

    prefix="/batches",

    tags=["Batch Management"]
)


# ============================================================
# SERVICES
# ============================================================

batch_service = BatchService()

fefo_service = FEFOService()


# ============================================================
# GET ALL BATCHES
# ============================================================

@router.get(
    "",
    response_model=list[BatchResponse]
)
def get_all_batches(

    db: Session = Depends(
        get_db
    )

):

    return batch_service.get_all_batches(
        db
    )


# ============================================================
# GET SINGLE BATCH
# ============================================================

@router.get(
    "/{batch_id}",
    response_model=BatchResponse
)
def get_batch(

    batch_id: str,

    db: Session = Depends(
        get_db
    )

):

    batch = batch_service.get_batch(
        db,
        batch_id
    )

    if not batch:

        raise HTTPException(

            status_code=404,

            detail=(
                f"Batch not found: "
                f"{batch_id}"
            )
        )

    return batch


# ============================================================
# FEFO QUEUE
# ============================================================

@router.get(
    "/fefo/queue"
)
def get_fefo_queue(

    db: Session = Depends(
        get_db
    )

):

    queue = fefo_service.get_fefo_queue(
        db
    )

    return {

        "success": True,

        "queue": queue
    }