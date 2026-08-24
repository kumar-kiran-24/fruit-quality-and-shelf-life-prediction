from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from api.database.database import get_db
from api.database.models import User
from api.auth.dependencies import (
    get_current_user
)
from api.services.buyer_recommendation_service import (
    BuyerRecommendationService
)
from api.services.batch_service import (
    BatchService
)
from api.services.status_service import (
    StatusService
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/recommendations",
    tags=["Buyer Recommendations"]
)


# ============================================================
# SERVICES
# ============================================================

recommendation_service = (
    BuyerRecommendationService()
)

batch_service = BatchService()


# ============================================================
# REQUEST SCHEMA
# ============================================================


class AssignBuyerRequest(BaseModel):

    destination_id: str = Field(
        ...,
        description="Destination/buyer ID"
    )


# ============================================================
# GET BUYER RECOMMENDATIONS
# ============================================================

@router.get(
    "/buyer/{batch_id}",
    summary=(
        "Get buyer recommendations for a batch"
    )
)
def get_buyer_recommendations(
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
            recommendation_service
            .recommend_buyers(
                db, batch_id
            )
        )

        return {

            "success": True,

            **result
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
                "Recommendation failed: "
                f"{str(exc)}"
            )
        )


# ============================================================
# ASSIGN BATCH TO BUYER
# ============================================================

@router.post(
    "/assign/{batch_id}",
    summary=(
        "Assign a batch to a recommended buyer"
    )
)
def assign_batch_to_buyer(
    batch_id: str,
    request: AssignBuyerRequest,
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

    # ----------------------------------------------------
    # Update batch status
    # ----------------------------------------------------

    status_svc = StatusService()

    try:

        status_svc.transition_status(
            db=db,
            batch_id=batch_id,
            new_status="ASSIGNED_TO_BUYER",
            action=(
                f"Assigned to buyer "
                f"{request.destination_id}"
            ),
            actor=current_user.user_id
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )

    return {

        "success": True,

        "message": (
            f"Batch {batch_id} assigned to "
            f"destination {request.destination_id}."
        ),

        "batch_id": batch_id,

        "destination_id": request.destination_id,

        "batch_status":
            "ASSIGNED_TO_BUYER"
    }
