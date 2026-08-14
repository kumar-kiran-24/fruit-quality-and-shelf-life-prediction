from sqlalchemy.orm import Session

from api.database.models import Batch


class BatchService:

    # ========================================================
    # CREATE BATCH
    # ========================================================

    def create_batch(
        self,
        db: Session,
        certificate: dict
    ):

        batch_id = (
            certificate["batch_id"]
        )

        # ----------------------------------------------------
        # Check whether batch already exists
        # ----------------------------------------------------

        existing_batch = (

            db.query(Batch)

            .filter(
                Batch.batch_id == batch_id
            )

            .first()
        )

        if existing_batch:

            raise ValueError(
                f"Batch already exists: {batch_id}"
            )

        # ----------------------------------------------------
        # Create new batch
        # ----------------------------------------------------

        new_batch = Batch(

            # Batch information
            batch_id=batch_id,

            fruit=certificate.get(
                "fruit",
                "apple"
            ),

            origin=certificate[
                "origin"
            ],

            # Location
            current_address=certificate.get(
                "current_address"
            ),

            # ------------------------------------------------
            # AI prediction
            # ------------------------------------------------

            freshness_prediction=certificate[
                "freshness_prediction"
            ],

            freshness_confidence=certificate[
                "freshness_confidence"
            ],

            shelf_life_prediction=certificate[
                "shelf_life_prediction"
            ],

            shelf_life_confidence=certificate[
                "shelf_life_confidence"
            ],

            # ------------------------------------------------
            # LLM assessment
            # ------------------------------------------------

            quality_status=certificate[
                "quality_status"
            ],

            risk_level=certificate[
                "risk_level"
            ],

            ai_summary=certificate.get(
                "summary"
            ),

            recommended_action=certificate.get(
                "recommended_action"
            ),

            # ------------------------------------------------
            # Certificate
            # ------------------------------------------------

            certificate_id=certificate.get(
                "certificate_id"
            ),

            # ------------------------------------------------
            # Logistics
            # ------------------------------------------------

            batch_status="AVAILABLE"
        )

        # ----------------------------------------------------
        # Save
        # ----------------------------------------------------

        db.add(
            new_batch
        )

        db.commit()

        db.refresh(
            new_batch
        )

        return new_batch


    # ========================================================
    # GET ALL BATCHES
    # ========================================================

    def get_all_batches(
        self,
        db: Session
    ):

        return (

            db.query(Batch)

            .order_by(
                Batch.created_at.desc()
            )

            .all()
        )


    # ========================================================
    # GET BATCH BY BATCH ID
    # ========================================================

    def get_batch(
        self,
        db: Session,
        batch_id: str
    ):

        return (

            db.query(Batch)

            .filter(
                Batch.batch_id == batch_id
            )

            .first()
        )


    # ========================================================
    # UPDATE CURRENT ADDRESS
    # ========================================================

    def update_address(
        self,
        db: Session,
        batch_id: str,
        current_address: str
    ):

        batch = self.get_batch(
            db,
            batch_id
        )

        if not batch:

            raise ValueError(
                f"Batch not found: {batch_id}"
            )

        batch.current_address = (
            current_address
        )

        db.commit()

        db.refresh(
            batch
        )

        return batch


    # ========================================================
    # UPDATE BATCH STATUS
    # ========================================================

    def update_status(
        self,
        db: Session,
        batch_id: str,
        status: str
    ):

        batch = self.get_batch(
            db,
            batch_id
        )

        if not batch:

            raise ValueError(
                f"Batch not found: {batch_id}"
            )

        batch.batch_status = (
            status
        )

        db.commit()

        db.refresh(
            batch
        )

        return batch