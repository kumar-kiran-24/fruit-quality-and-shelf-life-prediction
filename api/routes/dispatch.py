from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)

from sqlalchemy.orm import Session

from api.database.database import get_db

from api.schemas.dispatch import (
    DispatchCreate,
    DispatchResponse,
    DispatchStatusUpdate
)

from api.services.dispatch_service import (
    DispatchService
)


router = APIRouter(
    prefix="/api/v1/dispatch",
    tags=["Dispatch Management"]
)


# ============================================================
# CREATE DISPATCH
# ============================================================

@router.post(
    "",
    response_model=DispatchResponse
)
def create_dispatch(
    request: DispatchCreate,
    db: Session = Depends(get_db)
):

    try:

        dispatch = DispatchService.create_dispatch(
            db=db,
            batch_id=request.batch_id,
            destination_id=request.destination_id
        )

        return dispatch

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


# ============================================================
# GET ALL DISPATCHES
# ============================================================

@router.get(
    "",
    response_model=list[DispatchResponse]
)
def get_all_dispatches(
    db: Session = Depends(get_db)
):

    return DispatchService.get_all_dispatches(db)


# ============================================================
# GET SINGLE DISPATCH
# ============================================================

@router.get(
    "/{dispatch_id}",
    response_model=DispatchResponse
)
def get_dispatch(
    dispatch_id: str,
    db: Session = Depends(get_db)
):

    try:

        return DispatchService.get_dispatch(
            db=db,
            dispatch_id=dispatch_id
        )

    except ValueError as e:

        raise HTTPException(
            status_code=404,
            detail=str(e)
        )


# ============================================================
# UPDATE DISPATCH STATUS
# ============================================================

@router.patch(
    "/{dispatch_id}/status",
    response_model=DispatchResponse
)
def update_dispatch_status(
    dispatch_id: str,
    request: DispatchStatusUpdate,
    db: Session = Depends(get_db)
):

    try:

        return DispatchService.update_status(
            db=db,
            dispatch_id=dispatch_id,
            status=request.status
        )

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )