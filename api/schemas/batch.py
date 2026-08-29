from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


# ============================================================
# BATCH CREATE SCHEMA
# ============================================================

class BatchCreate(BaseModel):

    batch_id: str

    fruit: str = "apple"

    origin: str

    current_address: str | None = None


# ============================================================
# BATCH RESPONSE SCHEMA
# ============================================================

class BatchImageResponse(BaseModel):
    id: int
    filename: str
    url: str
    model_config = ConfigDict(from_attributes=True)


class BatchResponse(BaseModel):

    id: int

    batch_id: str

    fruit: str

    origin: str

    current_address: str | None = None

    # --------------------------------------------------------
    # IMAGE & DETECTION COUNTS
    # --------------------------------------------------------

    number_of_images: int | None = None

    total_apples_detected: int | None = None

    # --------------------------------------------------------
    # AI PREDICTIONS
    # --------------------------------------------------------

    freshness_prediction: str

    freshness_confidence: float

    shelf_life_prediction: str

    shelf_life_confidence: float

    # --------------------------------------------------------
    # LLM ASSESSMENT
    # --------------------------------------------------------

    quality_status: str

    risk_level: str

    ai_summary: str | None = None

    recommended_action: str | None = None

    # --------------------------------------------------------
    # DIGITAL BIRTH CERTIFICATE
    # --------------------------------------------------------

    certificate_id: str | None = None

    # --------------------------------------------------------
    # LOGISTICS
    # --------------------------------------------------------

    batch_status: str

    # --------------------------------------------------------
    # TIMESTAMPS
    # --------------------------------------------------------

    inspection_date: datetime

    created_at: datetime

    updated_at: datetime

    # --------------------------------------------------------
    # SQLAlchemy → Pydantic
    # --------------------------------------------------------

    model_config = ConfigDict(
        from_attributes=True
    )


class BatchDetailsResponse(BatchResponse):
    images: List[BatchImageResponse] = []