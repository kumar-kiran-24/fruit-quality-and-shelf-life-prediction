from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)

from sqlalchemy.orm import Session

from api.database.database import get_db

from api.schemas.destination import (
    DestinationCreate,
    DestinationResponse
)

from api.services.destination_service import (
    DestinationService
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/destinations",
    tags=["Destination Management"]
)


# ============================================================
# SERVICE
# ============================================================

destination_service = DestinationService()


# ============================================================
# CREATE DESTINATION
# ============================================================

@router.post(
    "",
    response_model=DestinationResponse
)
def create_destination(
    data: DestinationCreate,
    db: Session = Depends(get_db)
):

    try:

        return destination_service.create_destination(
            db,
            data
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=409,
            detail=str(exc)
        )


# ============================================================
# GET ALL DESTINATIONS
# ============================================================

@router.get(
    "",
    response_model=list[DestinationResponse]
)
def get_destinations(
    db: Session = Depends(get_db)
):

    return destination_service.get_all_destinations(
        db
    )


# ============================================================
# GET SINGLE DESTINATION
# ============================================================

@router.get(
    "/{destination_id}",
    response_model=DestinationResponse
)
def get_destination(
    destination_id: str,
    db: Session = Depends(get_db)
):

    destination = (
        destination_service.get_destination(
            db,
            destination_id
        )
    )

    if not destination:

        raise HTTPException(
            status_code=404,
            detail=(
                f"Destination not found: "
                f"{destination_id}"
            )
        )

    return destination