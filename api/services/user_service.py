from uuid import uuid4

from sqlalchemy.orm import Session

from api.database.models import User
from api.services.auth_service import AuthService


# ============================================================
# USER SERVICE
# ============================================================

class UserService:

    # ========================================================
    # GENERATE USER ID
    # ========================================================

    @staticmethod
    def _generate_user_id() -> str:

        return (
            f"USR-{uuid4().hex[:10].upper()}"
        )

    # ========================================================
    # REGISTER USER
    # ========================================================

    def register_user(
        self,
        db: Session,
        name: str,
        email: str,
        password: str,
        address: str | None = None,
        city: str | None = None,
        state: str | None = None,
        pincode: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
    ):

        # ----------------------------------------------------
        # Check duplicate email
        # ----------------------------------------------------

        existing = (
            db.query(User)
            .filter(
                User.email == email.lower().strip()
            )
            .first()
        )

        if existing:

            raise ValueError(
                "A user with this email "
                "already exists."
            )

        # ----------------------------------------------------
        # Create user
        # ----------------------------------------------------

        user = User(
            user_id=self._generate_user_id(),
            name=name.strip(),
            email=email.lower().strip(),
            password_hash=(
                AuthService.hash_password(password)
            ),
            address=address,
            city=city,
            state=state,
            pincode=pincode,
            latitude=latitude,
            longitude=longitude,
            role="USER",
            is_active=True
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        return user

    # ========================================================
    # AUTHENTICATE USER
    # ========================================================

    def authenticate_user(
        self,
        db: Session,
        email: str,
        password: str
    ):

        user = (
            db.query(User)
            .filter(
                User.email == email.lower().strip()
            )
            .first()
        )

        if not user:

            return None

        if not user.is_active:

            return None

        if not AuthService.verify_password(
            password,
            user.password_hash
        ):

            return None

        return user

    # ========================================================
    # GET USER BY USER ID
    # ========================================================

    def get_user_by_id(
        self,
        db: Session,
        user_id: str
    ):

        return (
            db.query(User)
            .filter(
                User.user_id == user_id
            )
            .first()
        )

    # ========================================================
    # GET USER BY EMAIL
    # ========================================================

    def get_user_by_email(
        self,
        db: Session,
        email: str
    ):

        return (
            db.query(User)
            .filter(
                User.email == email.lower().strip()
            )
            .first()
        )

    # ========================================================
    # UPDATE USER PROFILE
    # ========================================================

    def update_user_profile(
        self,
        db: Session,
        user_id: str,
        name: str | None = None,
        address: str | None = None,
        city: str | None = None,
        state: str | None = None,
        pincode: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
    ):

        user = self.get_user_by_id(
            db, user_id
        )

        if not user:

            raise ValueError(
                f"User not found: {user_id}"
            )

        if name is not None:
            user.name = name.strip()

        if address is not None:
            user.address = address

        if city is not None:
            user.city = city

        if state is not None:
            user.state = state

        if pincode is not None:
            user.pincode = pincode

        if latitude is not None:
            user.latitude = latitude

        if longitude is not None:
            user.longitude = longitude

        db.commit()
        db.refresh(user)

        return user

    # ========================================================
    # GET ALL USERS (admin only)
    # ========================================================

    def get_all_users(
        self,
        db: Session
    ):

        return (
            db.query(User)
            .order_by(
                User.created_at.desc()
            )
            .all()
        )
