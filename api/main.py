from fastapi import FastAPI

# ============================================================
# DATABASE
# ============================================================

from api.database.database import (
    engine,
    Base
)

# IMPORTANT:
# Import ALL models before create_all().
from api.database.models import (
    Batch,
    Destination,
    RouteRecommendation,
    Dispatch,
    User,
    BatchStatusHistory
)


# ============================================================
# EXISTING ROUTES
# ============================================================

from api.routes.routing import (
    router as routing_router
)

from api.routes.prediction import (
    router as prediction_router
)

from api.routes.certificate import (
    router as certificate_router
)

from api.routes.batch import (
    router as batch_router
)

from api.routes.destination import (
    router as destination_router
)

from api.routes.dispatch import (
    router as dispatch_router
)

from api.routes.optimization import (
    router as optimization_router
)

# ============================================================
# NEW ROUTES (Multi-User, Dashboard, etc.)
# ============================================================

from api.routes.auth import (
    router as auth_router
)

from api.routes.user import (
    router as user_router
)

from api.routes.dashboard import (
    router as dashboard_router
)

from api.routes.batch_upload import (
    router as batch_upload_router
)

from api.routes.shelf_life import (
    router as shelf_life_router
)

from api.routes.buyer_recommendation import (
    router as recommendation_router
)

from api.routes.batch_status import (
    router as batch_status_router
)


# ============================================================
# CREATE DATABASE TABLES
# ============================================================

Base.metadata.create_all(
    bind=engine
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

    version="2.0.0"
)


# ============================================================
# EXISTING ROUTERS (unchanged)
# ============================================================

app.include_router(
    prediction_router,
    prefix="/api/v1"
)

app.include_router(
    certificate_router,
    prefix="/api/v1"
)

app.include_router(
    batch_router,
    prefix="/api/v1"
)

app.include_router(
    routing_router,
    prefix="/api/v1"
)

app.include_router(
    destination_router,
    prefix="/api/v1"
)

# NOTE: dispatch and optimization routers
# already include /api/v1 in their own prefix.

app.include_router(
    dispatch_router
)

app.include_router(
    optimization_router
)


# ============================================================
# NEW ROUTERS (Multi-User System)
# ============================================================

app.include_router(
    auth_router,
    prefix="/api/v1"
)

app.include_router(
    user_router,
    prefix="/api/v1"
)

app.include_router(
    dashboard_router,
    prefix="/api/v1"
)

app.include_router(
    batch_upload_router,
    prefix="/api/v1"
)

app.include_router(
    shelf_life_router,
    prefix="/api/v1"
)

app.include_router(
    recommendation_router,
    prefix="/api/v1"
)

app.include_router(
    batch_status_router,
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
            "2.0.0",

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
