from uuid import uuid4

from sqlalchemy.orm import Session

from api.database.models import User
from api.services.auth_service import AuthService
from api.services.location_service import LocationService


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
        country: str | None = None,
        pincode: str | None = None,
        phone_number: str | None = None,
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
        # Resolve location from PIN code if provided
        # ----------------------------------------------------

        resolved_city = city
        resolved_state = state
        resolved_country = country
        resolved_latitude = latitude
        resolved_longitude = longitude

        if pincode and address:
            try:
                r_city, r_state, r_country, r_lat, r_lon = (
                    LocationService.resolve_from_postal_code(
                        address, pincode
                    )
                )
                # Override with resolved values when available
                resolved_city = r_city or resolved_city
                resolved_state = r_state or resolved_state
                resolved_country = r_country or resolved_country
                resolved_latitude = r_lat if r_lat is not None else resolved_latitude
                resolved_longitude = r_lon if r_lon is not None else resolved_longitude
            except ValueError as exc:
                # Do not store incorrect location
                raise ValueError(f"Location lookup failed: {str(exc)}")

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
            city=resolved_city,
            state=resolved_state,
            country=resolved_country,
            pincode=pincode,
            phone_number=phone_number,
            latitude=resolved_latitude,
            longitude=resolved_longitude,
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
        country: str | None = None,
        pincode: str | None = None,
        phone_number: str | None = None,
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

        if country is not None:
            user.country = country

        if pincode is not None:
            user.pincode = pincode

        if phone_number is not None:
            user.phone_number = phone_number

        if latitude is not None:
            user.latitude = latitude

        if longitude is not None:
            user.longitude = longitude

        db.commit()
        db.refresh(user)

        return user

    # ========================================================
    # CHANGE PASSWORD
    # ========================================================

    def change_password(
        self,
        db: Session,
        user_id: str,
        old_password: str,
        new_password: str
    ):

        user = self.get_user_by_id(db, user_id)

        if not user:
            raise ValueError(f"User not found: {user_id}")

        if not AuthService.verify_password(old_password, user.password_hash):
            raise ValueError("Current password is incorrect.")

        user.password_hash = AuthService.hash_password(new_password)
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
