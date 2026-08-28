from datetime import datetime

from sqlalchemy.orm import Session

from api.database.models import (
    Batch,
    BatchStatusHistory
)


# ============================================================
# VALID STATUS TRANSITIONS
#
# Defines which status transitions are allowed.
# This prevents invalid state changes.
# ============================================================

VALID_TRANSITIONS = {

    "CREATED": [
        "DETECTED"
    ],

    "DETECTED": [
        "SHELF_LIFE_PREDICTED",
        "RECOMMENDED",
        "ANALYZED"
    ],

    "SHELF_LIFE_PREDICTED": [
        "RECOMMENDED",
        "ANALYZED"
    ],

    "ANALYZED": [
        "RECOMMENDED",
        "READY_FOR_TRANSFER"
    ],

    "RECOMMENDED": [
        "ASSIGNED_TO_BUYER",
        "READY_FOR_TRANSFER"
    ],

    "ASSIGNED_TO_BUYER": [
        "READY_FOR_DISPATCH",
        "READY_FOR_TRANSFER"
    ],

    "READY_FOR_DISPATCH": [
        "DISPATCHED"
    ],

    "READY_FOR_TRANSFER": [
        "TRANSFERRED"
    ],

    "TRANSFERRED": [
        "IN_TRANSIT",
        "DELIVERED"
    ],

    "DISPATCHED": [
        "IN_TRANSIT",
        "DELIVERED"
    ],

    "IN_TRANSIT": [
        "DELIVERED",
        "REROUTING_REQUIRED"
    ],

    "DELIVERED": [
        "COMPLETED"
    ],

    "COMPLETED": [],

    "REROUTING_REQUIRED": [
        "RECOMMENDED",
        "DISPATCHED"
    ],

    # Legacy statuses - allow transitions from these
    "AVAILABLE": [
        "RECOMMENDED",
        "ASSIGNED_TO_BUYER",
        "DISPATCHED",
        "READY_FOR_TRANSFER"
    ],

    "FEFO_SELECTED": [
        "RECOMMENDED",
        "ASSIGNED_TO_BUYER",
        "DISPATCHED",
        "READY_FOR_TRANSFER"
    ],

    "ROUTE_RECOMMENDED": [
        "ASSIGNED_TO_BUYER",
        "DISPATCHED",
        "READY_FOR_TRANSFER"
    ],

    "REROUTED": [
        "DISPATCHED",
        "IN_TRANSIT"
    ],

    "RISK_INCREASED": [
        "REROUTING_REQUIRED",
        "DISPATCHED"
    ]
}


# ============================================================
# STATUS MANAGEMENT SERVICE
# ============================================================


class StatusService:

    # ========================================================
    # TRANSITION STATUS
    # ========================================================

    def transition_status(
        self,
        db: Session,
        batch_id: str,
        new_status: str,
        action: str | None = None,
        actor: str | None = None
    ):

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

        previous_status = (
            batch.batch_status
        )

        new_status = new_status.upper().strip()

        # ----------------------------------------------------
        # Validate transition
        # ----------------------------------------------------

        allowed = (
            VALID_TRANSITIONS.get(
                previous_status, []
            )
        )

        if new_status not in allowed:

            raise ValueError(
                f"Invalid status transition: "
                f"{previous_status} -> "
                f"{new_status}. "
                f"Allowed: {allowed}"
            )

        # ----------------------------------------------------
        # Update batch status
        # ----------------------------------------------------

        batch.batch_status = (
            new_status
        )

        batch.updated_at = (
            datetime.utcnow()
        )

        # ----------------------------------------------------
        # Record history
        # ----------------------------------------------------

        history = BatchStatusHistory(
            batch_id=batch_id,
            previous_status=previous_status,
            new_status=new_status,
            action=action,
            actor=actor
        )

        db.add(history)

        db.commit()
        db.refresh(batch)

        return batch

    # ========================================================
    # FORCE STATUS (admin / system override)
    # ========================================================

    def force_status(
        self,
        db: Session,
        batch_id: str,
        new_status: str,
        action: str | None = None,
        actor: str | None = None
    ):

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

        previous_status = (
            batch.batch_status
        )

        new_status = new_status.upper().strip()

        # ----------------------------------------------------
        # Update batch status
        # ----------------------------------------------------

        batch.batch_status = (
            new_status
        )

        batch.updated_at = (
            datetime.utcnow()
        )

        # ----------------------------------------------------
        # Record history
        # ----------------------------------------------------

        history = BatchStatusHistory(
            batch_id=batch_id,
            previous_status=previous_status,
            new_status=new_status,
            action=action or "ADMIN_OVERRIDE",
            actor=actor or "SYSTEM"
        )

        db.add(history)

        db.commit()
        db.refresh(batch)

        return batch

    # ========================================================
    # GET STATUS HISTORY
    # ========================================================

    def get_status_history(
        self,
        db: Session,
        batch_id: str
    ):

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

        history = (
            db.query(BatchStatusHistory)
            .filter(
                BatchStatusHistory.batch_id
                == batch_id
            )
            .order_by(
                BatchStatusHistory
                .created_at.asc()
            )
            .all()
        )

        return {

            "batch_id": batch_id,

            "current_status":
                batch.batch_status,

            "history": [

                {
                    "previous_status":
                        h.previous_status,

                    "new_status":
                        h.new_status,

                    "action":
                        h.action,

                    "actor":
                        h.actor,

                    "timestamp":
                        h.created_at
                        .isoformat()
                }

                for h in history
            ]
        }

    # ========================================================
    # GET VALID NEXT STATUSES
    # ========================================================

    def get_valid_next_statuses(
        self,
        db: Session,
        batch_id: str
    ):

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

        current = (
            batch.batch_status
        )

        allowed = (
            VALID_TRANSITIONS.get(
                current, []
            )
        )

        return {

            "batch_id": batch_id,

            "current_status": current,

            "valid_next_statuses": allowed
        }
