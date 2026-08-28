from datetime import datetime
from uuid import uuid4

from sqlalchemy.orm import Session

from api.database.models import (
    Batch,
    BatchTransfer,
    BatchStatusHistory,
    Destination
)


# ============================================================
# VALID TRANSFER STATUS TRANSITIONS
# ============================================================

VALID_TRANSFER_TRANSITIONS = {

    "TRANSFERRED": [
        "IN_TRANSIT",
        "DELIVERED"
    ],

    "IN_TRANSIT": [
        "DELIVERED"
    ],

    "DELIVERED": []
}


# ============================================================
# TRANSFER SERVICE
# ============================================================

class TransferService:

    # ========================================================
    # TRANSFER A BATCH
    # ========================================================

    @staticmethod
    def transfer_batch(
        db: Session,
        batch_id: str,
        destination_id: str,
        notes: str | None = None,
        planned_dispatch_date: datetime | None = None,
        actor: str | None = None
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
        # Validate batch is eligible for transfer
        #
        # Allow transfer from these statuses:
        #   ANALYZED, RECOMMENDED, ASSIGNED_TO_BUYER,
        #   READY_FOR_TRANSFER, AVAILABLE, FEFO_SELECTED,
        #   ROUTE_RECOMMENDED, SHELF_LIFE_PREDICTED
        #
        # Block transfer if already transferred
        # (TRANSFERRED, IN_TRANSIT, DELIVERED, COMPLETED,
        #  DISPATCHED)
        # ----------------------------------------------------

        eligible_statuses = {
            "CREATED",
            "DETECTED",
            "ANALYZED",
            "SHELF_LIFE_PREDICTED",
            "RECOMMENDED",
            "ASSIGNED_TO_BUYER",
            "READY_FOR_TRANSFER",
            "AVAILABLE",
            "FEFO_SELECTED",
            "ROUTE_RECOMMENDED"
        }

        if (
            batch.batch_status
            not in eligible_statuses
        ):
            raise ValueError(
                f"Batch {batch_id} cannot be "
                f"transferred because its current "
                f"status is '{batch.batch_status}'. "
                f"Eligible statuses: "
                f"{sorted(eligible_statuses)}"
            )

        # ----------------------------------------------------
        # Check for existing active transfer
        # ----------------------------------------------------

        existing_transfer = (
            db.query(BatchTransfer)
            .filter(
                BatchTransfer.batch_id == batch_id,
                BatchTransfer.transfer_status.in_([
                    "TRANSFERRED",
                    "IN_TRANSIT"
                ])
            )
            .first()
        )

        if existing_transfer:
            raise ValueError(
                f"Batch {batch_id} already has an "
                f"active transfer: "
                f"{existing_transfer.transfer_id} "
                f"(status: "
                f"{existing_transfer.transfer_status})"
            )

        # ----------------------------------------------------
        # Find destination
        # ----------------------------------------------------

        destination = (
            db.query(Destination)
            .filter(
                Destination.destination_id
                == destination_id
            )
            .first()
        )

        if not destination:
            raise ValueError(
                f"Destination not found: "
                f"{destination_id}"
            )

        # ----------------------------------------------------
        # Generate transfer ID
        # ----------------------------------------------------

        transfer_id = (
            f"TRF-{datetime.utcnow().strftime('%Y%m%d')}-"
            f"{uuid4().hex[:8].upper()}"
        )

        # ----------------------------------------------------
        # Create transfer record
        # ----------------------------------------------------

        now = datetime.utcnow()

        transfer = BatchTransfer(
            transfer_id=transfer_id,
            batch_id=batch_id,
            destination_id=destination.destination_id,
            destination_name=destination.name,
            destination_address=destination.address,
            transfer_status="TRANSFERRED",
            notes=notes,
            planned_dispatch_date=planned_dispatch_date,
            transferred_at=now,
            created_at=now,
            updated_at=now
        )

        db.add(transfer)

        # ----------------------------------------------------
        # Update batch status
        # ----------------------------------------------------

        previous_status = batch.batch_status
        batch.batch_status = "TRANSFERRED"
        batch.updated_at = now

        # ----------------------------------------------------
        # Record status history
        # ----------------------------------------------------

        history = BatchStatusHistory(
            batch_id=batch_id,
            previous_status=previous_status,
            new_status="TRANSFERRED",
            action=(
                f"Batch transferred to "
                f"{destination.name}"
                + (f" ({notes})" if notes else "")
            ),
            actor=actor
        )

        db.add(history)

        db.commit()
        db.refresh(transfer)

        return transfer

    # ========================================================
    # GET TRANSFER HISTORY
    # ========================================================

    @staticmethod
    def get_transfer_history(
        db: Session,
        batch_id: str
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
        # Get all transfers for this batch
        # ----------------------------------------------------

        transfers = (
            db.query(BatchTransfer)
            .filter(
                BatchTransfer.batch_id == batch_id
            )
            .order_by(
                BatchTransfer.created_at.asc()
            )
            .all()
        )

        # ----------------------------------------------------
        # Get status history
        # ----------------------------------------------------

        status_history = (
            db.query(BatchStatusHistory)
            .filter(
                BatchStatusHistory.batch_id
                == batch_id
            )
            .order_by(
                BatchStatusHistory.created_at.asc()
            )
            .all()
        )

        return {
            "batch_id": batch_id,
            "current_status": batch.batch_status,
            "transfers": [
                {
                    "transfer_id":
                        t.transfer_id,
                    "destination_id":
                        t.destination_id,
                    "destination_name":
                        t.destination_name,
                    "destination_address":
                        t.destination_address,
                    "transfer_status":
                        t.transfer_status,
                    "notes":
                        t.notes,
                    "planned_dispatch_date":
                        t.planned_dispatch_date
                        .isoformat()
                        if t.planned_dispatch_date
                        else None,
                    "transferred_at":
                        t.transferred_at
                        .isoformat()
                        if t.transferred_at
                        else None,
                    "in_transit_at":
                        t.in_transit_at
                        .isoformat()
                        if t.in_transit_at
                        else None,
                    "delivered_at":
                        t.delivered_at
                        .isoformat()
                        if t.delivered_at
                        else None,
                    "created_at":
                        t.created_at.isoformat(),
                    "updated_at":
                        t.updated_at.isoformat()
                }
                for t in transfers
            ],
            "status_history": [
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
                        h.created_at.isoformat()
                }
                for h in status_history
            ]
        }

    # ========================================================
    # UPDATE TRANSFER STATUS
    # ========================================================

    @staticmethod
    def update_transfer_status(
        db: Session,
        transfer_id: str,
        new_status: str,
        notes: str | None = None,
        actor: str | None = None
    ):

        # ----------------------------------------------------
        # Find transfer
        # ----------------------------------------------------

        transfer = (
            db.query(BatchTransfer)
            .filter(
                BatchTransfer.transfer_id
                == transfer_id
            )
            .first()
        )

        if not transfer:
            raise ValueError(
                f"Transfer not found: {transfer_id}"
            )

        # ----------------------------------------------------
        # Validate status transition
        # ----------------------------------------------------

        new_status = new_status.upper().strip()

        allowed = (
            VALID_TRANSFER_TRANSITIONS.get(
                transfer.transfer_status, []
            )
        )

        if new_status not in allowed:
            raise ValueError(
                f"Invalid transfer status "
                f"transition: "
                f"{transfer.transfer_status} "
                f"-> {new_status}. "
                f"Allowed: {allowed}"
            )

        # ----------------------------------------------------
        # Update transfer
        # ----------------------------------------------------

        now = datetime.utcnow()
        previous_status = transfer.transfer_status

        transfer.transfer_status = new_status
        transfer.updated_at = now

        # Update timestamps
        if new_status == "IN_TRANSIT":
            transfer.in_transit_at = now

        elif new_status == "DELIVERED":
            transfer.delivered_at = now

        # Append notes if provided
        if notes:
            if transfer.notes:
                transfer.notes = (
                    f"{transfer.notes}\n"
                    f"[{new_status}] {notes}"
                )
            else:
                transfer.notes = (
                    f"[{new_status}] {notes}"
                )

        # ----------------------------------------------------
        # Update batch status
        # ----------------------------------------------------

        batch = (
            db.query(Batch)
            .filter(
                Batch.batch_id
                == transfer.batch_id
            )
            .first()
        )

        if batch:
            batch.batch_status = new_status
            batch.updated_at = now

            # Record status history
            history = BatchStatusHistory(
                batch_id=transfer.batch_id,
                previous_status=previous_status,
                new_status=new_status,
                action=(
                    f"Transfer status updated: "
                    f"{previous_status} -> "
                    f"{new_status}"
                    + (f" ({notes})" if notes else "")
                ),
                actor=actor
            )

            db.add(history)

        db.commit()
        db.refresh(transfer)

        return transfer
