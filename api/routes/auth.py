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
    UserRegister,
    UserLogin,
    TokenResponse,
    UserResponse
)
from api.services.user_service import (
    UserService
)
from api.services.auth_service import (
    AuthService
)
from api.auth.dependencies import (
    get_current_user
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


# ============================================================
# SERVICE
# ============================================================

user_service = UserService()


# ============================================================
# REGISTER
# ============================================================

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
def register_user(
    data: UserRegister,
    db: Session = Depends(get_db)
):

    try:

        user = user_service.register_user(
            db=db,
            name=data.name,
            email=data.email,
            password=data.password,
            address=data.address,
            city=data.city,
            state=data.state,
            pincode=data.pincode,
            latitude=data.latitude,
            longitude=data.longitude
        )

        return user

    except ValueError as exc:

        raise HTTPException(
            status_code=(
                status.HTTP_409_CONFLICT
            ),
            detail=str(exc)
        )

    except Exception as exc:

        db.rollback()

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "Registration failed: "
                f"{str(exc)}"
            )
        )


# ============================================================
# LOGIN
# ============================================================

@router.post(
    "/login",
    response_model=TokenResponse
)
def login_user(
    data: UserLogin,
    db: Session = Depends(get_db)
):

    user = user_service.authenticate_user(
        db=db,
        email=data.email,
        password=data.password
    )

    if not user:

        raise HTTPException(
            status_code=(
                status.HTTP_401_UNAUTHORIZED
            ),
            detail=(
                "Invalid email or password."
            )
        )

    access_token = (
        AuthService.create_access_token(
            data={
                "sub": user.user_id,
                "email": user.email,
                "role": user.role
            }
        )
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=user.user_id,
        name=user.name,
        email=user.email,
        role=user.role
    )


# ============================================================
# GET CURRENT USER PROFILE
# ============================================================

@router.get(
    "/me",
    response_model=UserResponse
)
def get_me(
    current_user: User = Depends(
        get_current_user
    )
):

    return current_user
