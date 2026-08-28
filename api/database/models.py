from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Text,
    Boolean,
    ForeignKey
)

from sqlalchemy.orm import relationship

from api.database.database import Base


# ============================================================
# USER MODEL
# ============================================================

class User(Base):

    __tablename__ = "users"

    # ========================================================
    # PRIMARY KEY
    # ========================================================

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # ========================================================
    # USER IDENTIFICATION
    # ========================================================

    user_id = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True
    )

    name = Column(
        String(255),
        nullable=False
    )

    email = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )

    password_hash = Column(
        String(255),
        nullable=False
    )

    # ========================================================
    # ADDRESS & LOCATION
    # ========================================================

    address = Column(
        String(500),
        nullable=True
    )

    city = Column(
        String(100),
        nullable=True
    )

    state = Column(
        String(100),
        nullable=True
    )

    country = Column(
        String(100),
        nullable=True
    )

    pincode = Column(
        String(20),
        nullable=True
    )

    phone_number = Column(
        String(50),
        nullable=True
    )

    latitude = Column(
        Float,
        nullable=True
    )

    longitude = Column(
        Float,
        nullable=True
    )

    # ========================================================
    # ROLE
    # ========================================================

    role = Column(
        String(50),
        nullable=False,
        default="USER"
    )

    # ========================================================
    # STATUS
    # ========================================================

    is_active = Column(
        Boolean,
        nullable=False,
        default=True
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

    # ========================================================
    # USER OWNERSHIP
    # ========================================================

    user_id = Column(
        String(100),
        nullable=True,
        index=True
    )

    # ========================================================
    # IMAGE & DETECTION COUNTS
    # ========================================================

    number_of_images = Column(
        Integer,
        nullable=True,
        default=0
    )

    total_apples_detected = Column(
        Integer,
        nullable=True,
        default=0
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
        default="CREATED"
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

    # ========================================================
    # RELATIONSHIPS
    #
    # Note: user_id is a plain string column
    # (not a SQLAlchemy FK). Ownership is
    # resolved via direct queries in services.
    # ========================================================

    status_history = relationship(
        "BatchStatusHistory",
        back_populates="batch",
        foreign_keys="BatchStatusHistory.batch_id",
        primaryjoin="Batch.batch_id == BatchStatusHistory.batch_id",
        lazy="dynamic"
    )

    transfers = relationship(
        "BatchTransfer",
        back_populates="batch",
        foreign_keys="BatchTransfer.batch_id",
        primaryjoin="Batch.batch_id == BatchTransfer.batch_id",
        lazy="dynamic"
    )


# ============================================================
# BATCH STATUS HISTORY MODEL
# ============================================================

class BatchStatusHistory(Base):

    __tablename__ = "batch_status_history"

    # ========================================================
    # PRIMARY KEY
    # ========================================================

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # ========================================================
    # BATCH REFERENCE
    # ========================================================

    batch_id = Column(
        String(100),
        nullable=False,
        index=True
    )

    # ========================================================
    # STATUS TRANSITION
    # ========================================================

    previous_status = Column(
        String(50),
        nullable=True
    )

    new_status = Column(
        String(50),
        nullable=False
    )

    # ========================================================
    # ACTION / ACTOR
    # ========================================================

    action = Column(
        String(255),
        nullable=True
    )

    actor = Column(
        String(100),
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

    # ========================================================
    # RELATIONSHIPS
    # ========================================================

    batch = relationship(
        "Batch",
        back_populates="status_history",
        foreign_keys=[batch_id],
        primaryjoin="BatchStatusHistory.batch_id == Batch.batch_id",
        lazy="joined"
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
    
    
# ============================================================
# DISPATCH MODEL
# ============================================================

class Dispatch(Base):

    __tablename__ = "dispatches"

    # ========================================================
    # PRIMARY KEY
    # ========================================================

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # ========================================================
    # DISPATCH IDENTIFICATION
    # ========================================================

    dispatch_id = Column(
        String(100),
        unique=True,
        nullable=False,
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
    # ORIGIN
    # ========================================================

    origin_address = Column(
        String(500),
        nullable=False
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

    destination_address = Column(
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
    # DISPATCH STATUS
    # ========================================================

    dispatch_status = Column(
        String(50),
        nullable=False,
        default="DISPATCHED"
    )

    # ========================================================
    # TIMESTAMPS
    # ========================================================

    dispatched_at = Column(
        DateTime,
        nullable=True
    )

    estimated_delivery_at = Column(
        DateTime,
        nullable=True
    )

    delivered_at = Column(
        DateTime,
        nullable=True
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
# BATCH IMAGE MODEL
# ============================================================

class BatchImage(Base):

    __tablename__ = "batch_images"

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(String(100), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    original_path = Column(String(500), nullable=False)
    annotated_path = Column(String(500), nullable=True)
    apple_count = Column(Integer, default=0)
    average_confidence = Column(Float, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


# ============================================================
# BATCH TRANSFER MODEL
# ============================================================

class BatchTransfer(Base):

    __tablename__ = "batch_transfers"

    # ========================================================
    # PRIMARY KEY
    # ========================================================

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # ========================================================
    # TRANSFER IDENTIFICATION
    # ========================================================

    transfer_id = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True
    )

    # ========================================================
    # BATCH REFERENCE
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

    destination_address = Column(
        String(500),
        nullable=True
    )

    # ========================================================
    # TRANSFER STATUS
    # ========================================================

    transfer_status = Column(
        String(50),
        nullable=False,
        default="TRANSFERRED"
    )

    # ========================================================
    # NOTES
    # ========================================================

    notes = Column(
        Text,
        nullable=True
    )

    # ========================================================
    # PLANNED DISPATCH
    # ========================================================

    planned_dispatch_date = Column(
        DateTime,
        nullable=True
    )

    # ========================================================
    # TIMESTAMPS
    # ========================================================

    transferred_at = Column(
        DateTime,
        nullable=True
    )

    in_transit_at = Column(
        DateTime,
        nullable=True
    )

    delivered_at = Column(
        DateTime,
        nullable=True
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

    # ========================================================
    # RELATIONSHIPS
    # ========================================================

    batch = relationship(
        "Batch",
        back_populates="transfers",
        foreign_keys=[batch_id],
        primaryjoin="BatchTransfer.batch_id == Batch.batch_id",
        lazy="joined"
    )