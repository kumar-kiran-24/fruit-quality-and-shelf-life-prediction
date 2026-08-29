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
from api.services.status_service import (
    StatusService
)
from api.services.batch_service import (
    BatchService
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/batch-status",
    tags=["Batch Status Management"]
)


# ============================================================
# SERVICES
# ============================================================

status_service = StatusService()

batch_service = BatchService()


# ============================================================
# REQUEST SCHEMA
# ============================================================


class StatusUpdateRequest(BaseModel):

    new_status: str = Field(
        ...,
        description="New status to set"
    )

    action: str | None = Field(
        default=None,
        description="Action description"
    )


# ============================================================
# UPDATE BATCH STATUS
# ============================================================

@router.patch(
    "/{batch_id}",
    summary="Update batch status"
)
def update_batch_status(
    batch_id: str,
    request: StatusUpdateRequest,
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
    # Transition status
    # ----------------------------------------------------

    try:

        previous_status = (
            batch.batch_status
        )

        updated = (
            status_service.transition_status(
                db=db,
                batch_id=batch_id,
                new_status=request.new_status,
                action=request.action,
                actor=current_user.user_id
            )
        )

        return {

            "success": True,

            "message": (
                f"Batch status updated to "
                f"{request.new_status}."
            ),

            "batch_id": batch_id,

            "previous_status":
                previous_status,

            "new_status":
                updated.batch_status
        }

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )


# ============================================================
# GET STATUS HISTORY
# ============================================================

@router.get(
    "/{batch_id}/history",
    summary="Get batch status history"
)
def get_batch_status_history(
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

        history = (
            status_service
            .get_status_history(
                db, batch_id
            )
        )

        return {

            "success": True,

            **history
        }

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )


# ============================================================
# GET VALID NEXT STATUSES
# ============================================================

@router.get(
    "/{batch_id}/valid-transitions",
    summary=(
        "Get valid next statuses for a batch"
    )
)
def get_valid_transitions(
    batch_id: str,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db)
):

    try:

        result = (
            status_service
            .get_valid_next_statuses(
                db, batch_id
            )
        )

        return {

            "success": True,

            **result
        }

    except ValueError as exc:

        raise HTTPException(
            status_code=404,
            detail=str(exc)
        )
