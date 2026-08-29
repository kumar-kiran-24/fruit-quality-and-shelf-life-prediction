from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy.orm import Session

from api.database.models import (
    Batch,
    Destination,
    RouteRecommendation,
    Dispatch,
    BatchStatusHistory
)


# ============================================================
# DISPATCH SERVICE
# ============================================================

class DispatchService:

    # ========================================================
    # CREATE DISPATCH
    # ========================================================

    @staticmethod
    def create_dispatch(
        db: Session,
        batch_id: str,
        destination_id: str
    ):

        # ----------------------------------------------------
        # Find batch
        # ----------------------------------------------------

        batch = (
            db.query(Batch)
            .filter(
                Batch.batch_id == batch_id
            )
            .first()
        )

        if not batch:
            raise ValueError(
                f"Batch not found: {batch_id}"
            )

        # ----------------------------------------------------
        # Check batch status
        # ----------------------------------------------------

        if batch.batch_status not in [
            "AVAILABLE",
            "FEFO_SELECTED",
            "ROUTE_RECOMMENDED"
        ]:
            raise ValueError(
                f"Batch {batch_id} cannot be dispatched "
                f"because its current status is "
                f"{batch.batch_status}"
            )

        # ----------------------------------------------------
        # Find destination
        # ----------------------------------------------------

        destination = (
            db.query(Destination)
            .filter(
                Destination.destination_id == destination_id
            )
            .first()
        )

        if not destination:
            raise ValueError(
                f"Destination not found: {destination_id}"
            )

        # ----------------------------------------------------
        # Find selected route recommendation
        # ----------------------------------------------------

        route = (
            db.query(RouteRecommendation)
            .filter(
                RouteRecommendation.batch_id == batch_id,
                RouteRecommendation.destination_id == destination_id,
                RouteRecommendation.is_selected == True
            )
            .order_by(
                RouteRecommendation.created_at.desc()
            )
            .first()
        )

        # ----------------------------------------------------
        # If selected route doesn't exist,
        # try latest route recommendation
        # ----------------------------------------------------

        if not route:

            route = (
                db.query(RouteRecommendation)
                .filter(
                    RouteRecommendation.batch_id == batch_id,
                    RouteRecommendation.destination_id == destination_id
                )
                .order_by(
                    RouteRecommendation.created_at.desc()
                )
                .first()
            )

        if not route:
            raise ValueError(
                f"No route recommendation found for "
                f"batch {batch_id} and destination "
                f"{destination_id}"
            )

        # ----------------------------------------------------
        # Prevent duplicate active dispatch
        # ----------------------------------------------------

        existing_dispatch = (
            db.query(Dispatch)
            .filter(
                Dispatch.batch_id == batch_id,
                Dispatch.dispatch_status.in_([
                    "DISPATCHED",
                    "IN_TRANSIT"
                ])
            )
            .first()
        )

        if existing_dispatch:
            raise ValueError(
                f"Batch {batch_id} already has an active "
                f"dispatch: {existing_dispatch.dispatch_id}"
            )

        # ----------------------------------------------------
        # Generate dispatch ID
        # ----------------------------------------------------

        dispatch_id = (
            f"DSP-{datetime.utcnow().strftime('%Y%m%d')}-"
            f"{uuid4().hex[:8].upper()}"
        )

        # ----------------------------------------------------
        # Calculate estimated delivery
        # ----------------------------------------------------

        now = datetime.utcnow()

        estimated_delivery = (
            now +
            timedelta(
                minutes=route.duration_minutes
            )
        )

        # ----------------------------------------------------
        # Create dispatch
        # ----------------------------------------------------

        dispatch = Dispatch(

            dispatch_id=dispatch_id,

            batch_id=batch.batch_id,

            origin_address=(
                batch.current_address
                or batch.origin
            ),

            destination_id=destination.destination_id,

            destination_name=destination.name,

            destination_address=destination.address,

            distance_km=route.distance_km,

            duration_minutes=route.duration_minutes,

            dispatch_status="DISPATCHED",

            dispatched_at=now,

            estimated_delivery_at=estimated_delivery
        )

        db.add(dispatch)

        # ----------------------------------------------------
        # Update batch status
        # ----------------------------------------------------

        previous_status = batch.batch_status
        batch.batch_status = "DISPATCHED"
        batch.updated_at = now

        # ----------------------------------------------------
        # Record status history
        # ----------------------------------------------------

        history = BatchStatusHistory(
            batch_id=batch.batch_id,
            previous_status=previous_status,
            new_status="DISPATCHED",
            action=(
                f"Batch dispatched to "
                f"{destination.name}"
            ),
            actor=None
        )

        db.add(history)

        db.commit()

        db.refresh(dispatch)

        return dispatch

    # ========================================================
    # GET DISPATCH
    # ========================================================

    @staticmethod
    def get_dispatch(
        db: Session,
        dispatch_id: str
    ):

        dispatch = (
            db.query(Dispatch)
            .filter(
                Dispatch.dispatch_id == dispatch_id
            )
            .first()
        )

        if not dispatch:
            raise ValueError(
                f"Dispatch not found: {dispatch_id}"
            )

        return dispatch

    # ========================================================
    # GET ALL DISPATCHES
    # ========================================================

    @staticmethod
    def get_all_dispatches(
        db: Session
    ):

        return (
            db.query(Dispatch)
            .order_by(
                Dispatch.created_at.desc()
            )
            .all()
        )

    # ========================================================
    # UPDATE STATUS
    # ========================================================

    @staticmethod
    def update_status(
        db: Session,
        dispatch_id: str,
        status: str
    ):

        dispatch = (
            db.query(Dispatch)
            .filter(
                Dispatch.dispatch_id == dispatch_id
            )
            .first()
        )

        if not dispatch:
            raise ValueError(
                f"Dispatch not found: {dispatch_id}"
            )

        status = status.upper()

        allowed_statuses = {
            "DISPATCHED",
            "IN_TRANSIT",
            "DELIVERED",
            "RISK_INCREASED",
            "REROUTING_REQUIRED",
            "REROUTED"
        }

        if status not in allowed_statuses:
            raise ValueError(
                f"Invalid dispatch status: {status}"
            )

        now = datetime.utcnow()

        dispatch.dispatch_status = status
        dispatch.updated_at = now

        # ----------------------------------------------------
        # Update batch status
        # ----------------------------------------------------

        batch = (
            db.query(Batch)
            .filter(
                Batch.batch_id == dispatch.batch_id
            )
            .first()
        )

        if batch:

            previous_batch_status = (
                batch.batch_status
            )

            if status == "DISPATCHED":
                batch.batch_status = "DISPATCHED"

            elif status == "IN_TRANSIT":
                batch.batch_status = "IN_TRANSIT"

            elif status == "DELIVERED":
                batch.batch_status = "DELIVERED"

            elif status == "RISK_INCREASED":
                batch.batch_status = "RISK_INCREASED"

            elif status == "REROUTING_REQUIRED":
                batch.batch_status = "REROUTING_REQUIRED"

            elif status == "REROUTED":
                batch.batch_status = "REROUTED"

            batch.updated_at = now

            # ------------------------------------------------
            # Record status history
            # ------------------------------------------------

            if (
                batch.batch_status
                != previous_batch_status
            ):

                history = BatchStatusHistory(
                    batch_id=dispatch.batch_id,
                    previous_status=(
                        previous_batch_status
                    ),
                    new_status=batch.batch_status,
                    action=(
                        f"Dispatch status updated: "
                        f"{status}"
                    ),
                    actor=None
                )

                db.add(history)

            # ------------------------------------------------
            # Auto-transition DELIVERED -> COMPLETED
            # ------------------------------------------------

            if status == "DELIVERED":

                if (
                    batch.batch_status
                    == "DELIVERED"
                ):

                    batch.batch_status = "COMPLETED"
                    batch.updated_at = now

                    completion_history = (
                        BatchStatusHistory(
                            batch_id=(
                                dispatch.batch_id
                            ),
                            previous_status=(
                                "DELIVERED"
                            ),
                            new_status=(
                                "COMPLETED"
                            ),
                            action=(
                                "Batch delivery "
                                "confirmed and "
                                "completed"
                            ),
                            actor=None
                        )
                    )

                    db.add(completion_history)

        # ----------------------------------------------------
        # Delivery timestamp
        # ----------------------------------------------------

        if status == "DELIVERED":
            dispatch.delivered_at = now

        db.commit()

        db.refresh(dispatch)

        return dispatch