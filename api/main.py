from fastapi import FastAPI

# ============================================================
# DATABASE
# ============================================================

from api.database.database import (
    engine,
    Base
)

from api.database.models import (
    Batch,
    Destination,
    RouteRecommendation
)

# IMPORTANT:
# Import the models before create_all().
# This registers the Batch table with SQLAlchemy.
from api.database.models import (
    Batch
)

from api.routes.routing import (
    router as routing_router
)


# ============================================================
# ROUTES
# ============================================================

from api.routes.prediction import (
    router as prediction_router
)

from api.routes.certificate import (
    router as certificate_router
)

from api.routes.batch import (
    router as batch_router
)


# ============================================================
# CREATE DATABASE TABLES
# ============================================================

Base.metadata.create_all(
    bind=engine
)

Base.metadata.create_all(
    bind=engine
)

from api.routes.destination import (
    router as destination_router
)


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(

    title="AI Fruit Quality System",

    description=(
        "AI-based Apple freshness, "
        "shelf-life prediction, "
        "Digital Birth Certificate, "
        "batch management and "
        "FEFO supply-chain system."
    ),

    version="1.0.0"
)


# ============================================================
# PREDICTION ROUTER
# ============================================================

app.include_router(

    prediction_router,

    prefix="/api/v1"
)


# ============================================================
# DIGITAL BIRTH CERTIFICATE ROUTER
# ============================================================

app.include_router(

    certificate_router,

    prefix="/api/v1"
)


# ============================================================
# BATCH MANAGEMENT ROUTER
# ============================================================

app.include_router(

    batch_router,

    prefix="/api/v1"
)


# ============================================================
# ROOT ENDPOINT
# ============================================================

@app.get("/")
def root():

    return {

        "service":
            "AI Fruit Quality System",

        "version":
            "1.0.0",

        "status":
            "running"
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():

    return {

        "status":
            "healthy"
    }
    
    
app.include_router(
    routing_router,
    prefix="/api/v1"
)

app.include_router(
    destination_router,
    prefix="/api/v1"
)