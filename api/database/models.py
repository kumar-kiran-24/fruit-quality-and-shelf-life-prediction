from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Text,
    Boolean
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


# ============================================================
# DESTINATION MODEL
# ============================================================

class Destination(Base):

    __tablename__ = "destinations"

    # ========================================================
    # PRIMARY KEY
    # ========================================================

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # ========================================================
    # DESTINATION INFORMATION
    # ========================================================

    destination_id = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True
    )

    name = Column(
        String(255),
        nullable=False
    )

    destination_type = Column(
        String(50),
        nullable=False
    )

    address = Column(
        String(500),
        nullable=False
    )

    # ========================================================
    # LOCATION
    # ========================================================

    latitude = Column(
        Float,
        nullable=False
    )

    longitude = Column(
        Float,
        nullable=False
    )

    # ========================================================
    # CAPACITY
    # ========================================================

    capacity_kg = Column(
        Float,
        nullable=False,
        default=0
    )

    available_capacity_kg = Column(
        Float,
        nullable=False,
        default=0
    )

    # ========================================================
    # FRUIT COMPATIBILITY
    # ========================================================

    accepted_fruit = Column(
        String(255),
        nullable=False,
        default="apple"
    )

    # ========================================================
    # STATUS
    # ========================================================

    status = Column(
        String(50),
        nullable=False,
        default="ACTIVE"
    )

    # ========================================================
    # TIMESTAMPS
    # ========================================================

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


# ============================================================
# ROUTE RECOMMENDATION MODEL
# ============================================================

class RouteRecommendation(Base):

    __tablename__ = "route_recommendations"

    # ========================================================
    # PRIMARY KEY
    # ========================================================

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # ========================================================
    # BATCH
    # ========================================================

    batch_id = Column(
        String(100),
        nullable=False,
        index=True
    )

    # ========================================================
    # DESTINATION
    # ========================================================

    destination_id = Column(
        String(100),
        nullable=False,
        index=True
    )

    destination_name = Column(
        String(255),
        nullable=False
    )

    destination_type = Column(
        String(50),
        nullable=False
    )

    destination_address = Column(
        String(500),
        nullable=False
    )

    # ========================================================
    # ORIGIN
    # ========================================================

    origin_address = Column(
        String(500),
        nullable=False
    )

    # ========================================================
    # ROUTE INFORMATION
    # ========================================================

    distance_km = Column(
        Float,
        nullable=False
    )

    duration_minutes = Column(
        Float,
        nullable=False
    )

    # ========================================================
    # SCORING
    # ========================================================

    distance_score = Column(
        Float,
        nullable=False
    )

    duration_score = Column(
        Float,
        nullable=False
    )

    shelf_life_score = Column(
        Float,
        nullable=False
    )

    capacity_score = Column(
        Float,
        nullable=False
    )

    suitability_score = Column(
        Float,
        nullable=False
    )

    total_score = Column(
        Float,
        nullable=False
    )

    # ========================================================
    # DECISION
    # ========================================================

    is_selected = Column(
        Boolean,
        nullable=False,
        default=False
    )

    recommendation_status = Column(
        String(50),
        nullable=False,
        default="EVALUATED"
    )

    recommendation_reason = Column(
        Text,
        nullable=True
    )

    # ========================================================
    # TIMESTAMP
    # ========================================================

    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow
    )