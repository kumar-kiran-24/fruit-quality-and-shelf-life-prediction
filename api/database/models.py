from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Text
)

from api.database.database import Base


# ============================================================
# BATCH MODEL
# ============================================================

class Batch(Base):

    __tablename__ = "batches"

    # ========================================================
    # PRIMARY KEY
    # ========================================================

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # ========================================================
    # BATCH INFORMATION
    # ========================================================

    batch_id = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True
    )

    fruit = Column(
        String(50),
        nullable=False,
        default="apple"
    )

    origin = Column(
        String(255),
        nullable=False
    )

    # ========================================================
    # CURRENT LOCATION
    # ========================================================

    current_address = Column(
        String(500),
        nullable=True
    )

    # ========================================================
    # AI FRESHNESS PREDICTION
    # ========================================================

    freshness_prediction = Column(
        String(50),
        nullable=False
    )

    freshness_confidence = Column(
        Float,
        nullable=False
    )

    # ========================================================
    # AI SHELF-LIFE PREDICTION
    # ========================================================

    shelf_life_prediction = Column(
        String(50),
        nullable=False
    )

    shelf_life_confidence = Column(
        Float,
        nullable=False
    )

    # ========================================================
    # LLM QUALITY ASSESSMENT
    # ========================================================

    quality_status = Column(
        String(50),
        nullable=False
    )

    risk_level = Column(
        String(50),
        nullable=False
    )

    ai_summary = Column(
        Text,
        nullable=True
    )

    recommended_action = Column(
        Text,
        nullable=True
    )

    # ========================================================
    # DIGITAL BIRTH CERTIFICATE
    # ========================================================

    certificate_id = Column(
        String(100),
        nullable=True,
        index=True
    )

    # ========================================================
    # LOGISTICS STATUS
    # ========================================================

    batch_status = Column(
        String(50),
        nullable=False,
        default="AVAILABLE"
    )

    # ========================================================
    # TIMESTAMPS
    # ========================================================

    inspection_date = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )