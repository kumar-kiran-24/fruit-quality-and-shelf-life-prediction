from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field, ConfigDict


# ============================================================
# TRANSFER CREATE SCHEMA
# ============================================================

class TransferCreate(BaseModel):

    destination_id: str = Field(
        ...,
        description="Destination/location ID to transfer to"
    )

    notes: Optional[str] = Field(
        default=None,
        description="Optional transfer notes"
    )

    planned_dispatch_date: Optional[datetime] = Field(
        default=None,
        description="Optional planned dispatch date"
    )


# ============================================================
# TRANSFER STATUS UPDATE SCHEMA
# ============================================================

class TransferStatusUpdate(BaseModel):

    new_status: str = Field(
        ...,
        description=(
            "New transfer status: "
            "IN_TRANSIT or DELIVERED"
        )
    )

    notes: Optional[str] = Field(
        default=None,
        description="Optional status update notes"
    )


# ============================================================
# TRANSFER RESPONSE SCHEMA
# ============================================================

class TransferResponse(BaseModel):

    id: int
    transfer_id: str
    batch_id: str
    destination_id: str
    destination_name: str
    destination_address: Optional[str] = None
    transfer_status: str
    notes: Optional[str] = None
    planned_dispatch_date: Optional[datetime] = None
    transferred_at: Optional[datetime] = None
    in_transit_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )


# ============================================================
# TRANSFER HISTORY RESPONSE SCHEMA
# ============================================================

class TransferHistoryEntry(BaseModel):

    transfer_id: str
    destination_id: str
    destination_name: str
    transfer_status: str
    notes: Optional[str] = None
    transferred_at: Optional[datetime] = None
    in_transit_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class TransferHistoryResponse(BaseModel):

    batch_id: str
    current_status: str
    transfers: List[TransferHistoryEntry] = []
    status_history: List[dict] = []
