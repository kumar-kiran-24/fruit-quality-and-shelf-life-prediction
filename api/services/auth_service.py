import os
from pathlib import Path
from datetime import datetime, timedelta

from dotenv import load_dotenv
from jose import JWTError, jwt
from passlib.context import CryptContext


# ============================================================
# LOAD ENVIRONMENT
# ============================================================

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[2]
)

load_dotenv(
    PROJECT_ROOT / ".env"
)


# ============================================================
# CONFIGURATION
# ============================================================

SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY",
    "change-me-in-production-use-a-real-secret"
)

ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv(
        "JWT_EXPIRE_MINUTES",
        "60"
    )
)


# ============================================================
# PASSWORD CONTEXT
# ============================================================

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


# ============================================================
# AUTH SERVICE
# ============================================================

class AuthService:

    # ========================================================
    # HASH PASSWORD
    # ========================================================

    @staticmethod
    def hash_password(
        password: str
    ) -> str:

        return pwd_context.hash(
            password
        )

    # ========================================================
    # VERIFY PASSWORD
    # ========================================================

    @staticmethod
    def verify_password(
        plain_password: str,
        hashed_password: str
    ) -> bool:

        return pwd_context.verify(
            plain_password,
            hashed_password
        )

    # ========================================================
    # CREATE ACCESS TOKEN
    # ========================================================

    @staticmethod
    def create_access_token(
        data: dict,
        expires_delta: timedelta | None = None
    ) -> str:

        to_encode = data.copy()

        expire = (
            datetime.utcnow()
            + (
                expires_delta
                or timedelta(
                    minutes=ACCESS_TOKEN_EXPIRE_MINUTES
                )
            )
        )

        to_encode.update({
            "exp": expire
        })

        encoded_jwt = jwt.encode(
            to_encode,
            SECRET_KEY,
            algorithm=ALGORITHM
        )

        return encoded_jwt

    # ========================================================
    # DECODE ACCESS TOKEN
    # ========================================================

    @staticmethod
    def decode_access_token(
        token: str
    ) -> dict | None:

        try:

            payload = jwt.decode(
                token,
                SECRET_KEY,
                algorithms=[ALGORITHM]
            )

            return payload

        except JWTError:

            return None
