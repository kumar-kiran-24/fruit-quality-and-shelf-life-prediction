from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, EmailStr


# ============================================================
# USER REGISTRATION
# ============================================================


class UserRegister(BaseModel):

    name: str = Field(
        ...,
        min_length=2,
        max_length=255,
        description="Full name of the user"
    )

    email: EmailStr = Field(
        ...,
        description="Email address"
    )

    password: str = Field(
        ...,
        min_length=6,
        max_length=128,
        description="Password"
    )

    address: Optional[str] = Field(
        default=None,
        description="Full address"
    )

    city: Optional[str] = Field(
        default=None,
        description="City"
    )

    state: Optional[str] = Field(
        default=None,
        description="State"
    )

    pincode: Optional[str] = Field(
        default=None,
        description="Pincode / ZIP code"
    )

    latitude: Optional[float] = Field(
        default=None,
        description="Latitude coordinate"
    )

    longitude: Optional[float] = Field(
        default=None,
        description="Longitude coordinate"
    )


# ============================================================
# USER LOGIN
# ============================================================


class UserLogin(BaseModel):

    email: EmailStr = Field(
        ...,
        description="Email address"
    )

    password: str = Field(
        ...,
        description="Password"
    )


# ============================================================
# TOKEN RESPONSE
# ============================================================


class TokenResponse(BaseModel):

    access_token: str

    token_type: str = "bearer"

    user_id: str

    name: str

    email: str

    role: str


# ============================================================
# USER PROFILE UPDATE
# ============================================================


class UserProfileUpdate(BaseModel):

    name: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=255
    )

    address: Optional[str] = None

    city: Optional[str] = None

    state: Optional[str] = None

    pincode: Optional[str] = None

    latitude: Optional[float] = None

    longitude: Optional[float] = None


# ============================================================
# USER RESPONSE
# ============================================================


class UserResponse(BaseModel):

    id: int

    user_id: str

    name: str

    email: str

    address: Optional[str] = None

    city: Optional[str] = None

    state: Optional[str] = None

    pincode: Optional[str] = None

    latitude: Optional[float] = None

    longitude: Optional[float] = None

    role: str

    is_active: bool

    created_at: datetime

    updated_at: datetime
