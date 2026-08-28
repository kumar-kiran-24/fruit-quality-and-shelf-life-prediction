from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)
from sqlalchemy.orm import Session

from api.database.database import get_db
from api.database.models import User
from api.schemas.user import (
    UserProfileUpdate,
    UserResponse,
    PasswordChange
)
from api.services.user_service import (
    UserService
)
from api.auth.dependencies import (
    get_current_user
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/users",
    tags=["User Management"]
)


# ============================================================
# SERVICE
# ============================================================

user_service = UserService()


# ============================================================
# GET MY PROFILE
# ============================================================

@router.get(
    "/me",
    response_model=UserResponse
)
def get_my_profile(
    current_user: User = Depends(
        get_current_user
    )
):

    return current_user


# ============================================================
# UPDATE MY PROFILE
# ============================================================

@router.patch(
    "/me",
    response_model=UserResponse
)
def update_my_profile(
    data: UserProfileUpdate,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db)
):

    try:

        updated = (
            user_service.update_user_profile(
                db=db,
                user_id=current_user.user_id,
                name=data.name,
                address=data.address,
                city=data.city,
                state=data.state,
                country=data.country,
                pincode=data.pincode,
                phone_number=data.phone_number,
                latitude=data.latitude,
                longitude=data.longitude
            )
        )

        return updated

    except ValueError as exc:

        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=str(exc)
        )


# ============================================================
# CHANGE PASSWORD
# ============================================================

@router.patch(
    "/me/password",
    response_model=UserResponse
)
def change_password(
    data: PasswordChange,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db)
):

    try:

        updated = (
            user_service.change_password(
                db=db,
                user_id=current_user.user_id,
                old_password=data.old_password,
                new_password=data.new_password
            )
        )

        return updated

    except ValueError as exc:

        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=str(exc)
        )
