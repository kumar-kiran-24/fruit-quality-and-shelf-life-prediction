from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)
from sqlalchemy.orm import Session

from api.database.database import get_db
from api.database.models import User
from api.auth.dependencies import (
    get_current_user
)
from api.services.shelf_life_service import (
    ShelfLifeService
)
from api.services.batch_service import (
    BatchService
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/shelf-life",
    tags=["Shelf-Life Prediction"]
)


# ============================================================
# SERVICES
# ============================================================

shelf_life_service = ShelfLifeService()

batch_service = BatchService()


# ============================================================
# PREDICT SHELF LIFE
# ============================================================

@router.get(
    "/predict/{batch_id}",
    summary=(
        "Get shelf-life prediction for a batch"
    )
)
def predict_shelf_life(
    batch_id: str,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db)
):

    # ----------------------------------------------------
    # Verify batch ownership
    # ----------------------------------------------------

    batch = batch_service.get_batch(
        db, batch_id
    )

    if not batch:

        raise HTTPException(
            status_code=404,
            detail=(
                f"Batch not found: {batch_id}"
            )
        )

    if (
        batch.user_id
        != current_user.user_id
    ):

        raise HTTPException(
            status_code=403,
            detail=(
                "Access denied. "
                "This batch belongs to "
                "another user."
            )
        )

    try:

        result = (
            shelf_life_service
            .predict_shelf_life(
                db, batch_id
            )
        )

        return {

            "success": True,

            "prediction": result
        }

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                "Shelf-life prediction failed: "
                f"{str(exc)}"
            )
        )
