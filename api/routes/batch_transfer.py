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
from api.schemas.transfer import (
    TransferCreate,
    TransferStatusUpdate,
    TransferResponse,
    TransferHistoryResponse
)
from api.services.transfer_service import (
    TransferService
)
from api.services.batch_service import (
    BatchService
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/batches",
    tags=["Batch Transfer & Tracking"]
)


# ============================================================
# SERVICES
# ============================================================

transfer_service = TransferService()

batch_service = BatchService()


# ============================================================
# TRANSFER A BATCH
# ============================================================

@router.post(
    "/{batch_id}/transfer",
    response_model=TransferResponse,
    summary="Transfer a batch to a destination"
)
def transfer_batch(
    batch_id: str,
    request: TransferCreate,
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
    # Perform transfer
    # ----------------------------------------------------

    try:
        transfer = (
            transfer_service.transfer_batch(
                db=db,
                batch_id=batch_id,
                destination_id=(
                    request.destination_id
                ),
                notes=request.notes,
                planned_dispatch_date=(
                    request.planned_dispatch_date
                ),
                actor=current_user.user_id
            )
        )

        return transfer

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )


# ============================================================
# GET TRANSFER HISTORY
# ============================================================

@router.get(
    "/{batch_id}/transfer-history",
    response_model=TransferHistoryResponse,
    summary="Get transfer history for a batch"
)
def get_transfer_history(
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
            transfer_service
            .get_transfer_history(
                db, batch_id
            )
        )

        return history

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )


# ============================================================
# UPDATE TRANSFER STATUS
# ============================================================

@router.patch(
    "/{batch_id}/transfer-status/{transfer_id}",
    response_model=TransferResponse,
    summary=(
        "Update transfer status "
        "(IN_TRANSIT or DELIVERED)"
    )
)
def update_transfer_status(
    batch_id: str,
    transfer_id: str,
    request: TransferStatusUpdate,
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
    # Update status
    # ----------------------------------------------------

    try:
        transfer = (
            transfer_service
            .update_transfer_status(
                db=db,
                transfer_id=transfer_id,
                new_status=(
                    request.new_status
                ),
                notes=request.notes,
                actor=current_user.user_id
            )
        )

        return transfer

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )
