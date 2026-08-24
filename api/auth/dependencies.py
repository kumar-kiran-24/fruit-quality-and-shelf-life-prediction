from fastapi import (
    Depends,
    HTTPException,
    status
)
from fastapi.security import (
    HTTPBearer,
    HTTPAuthorizationCredentials
)
from sqlalchemy.orm import Session

from api.database.database import get_db
from api.database.models import User
from api.services.auth_service import (
    AuthService
)


# ============================================================
# BEARER SCHEME
# ============================================================

security = HTTPBearer()


# ============================================================
# GET CURRENT USER (Dependency)
#
# Extracts and validates the JWT token
# from the Authorization header.
# ============================================================


def get_current_user(
    credentials: HTTPAuthorizationCredentials = (
        Depends(security)
    ),
    db: Session = Depends(get_db)
) -> User:

    token = credentials.credentials

    payload = (
        AuthService.decode_access_token(token)
    )

    if payload is None:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=(
                "Invalid or expired token."
            ),
            headers={
                "WWW-Authenticate": "Bearer"
            }
        )

    user_id = payload.get("sub")

    if user_id is None:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=(
                "Token does not contain "
                "a user identifier."
            )
        )

    user = (
        db.query(User)
        .filter(
            User.user_id == user_id
        )
        .first()
    )

    if user is None:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=(
                "User not found."
            )
        )

    if not user.is_active:

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "User account is deactivated."
            )
        )

    return user


# ============================================================
# GET CURRENT USER (Optional)
#
# Returns None if no token is provided.
# Use for endpoints that work with or without auth.
# ============================================================


def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = (
        Depends(security)
    ),
    db: Session = Depends(get_db)
) -> User | None:

    if credentials is None:

        return None

    token = credentials.credentials

    payload = (
        AuthService.decode_access_token(token)
    )

    if payload is None:

        return None

    user_id = payload.get("sub")

    if user_id is None:

        return None

    user = (
        db.query(User)
        .filter(
            User.user_id == user_id
        )
        .first()
    )

    return user
