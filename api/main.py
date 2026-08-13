from fastapi import FastAPI

from api.routes.prediction import (
    router as prediction_router
)


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(

    title="AI Fruit Quality System",

    description=(
        "AI-based Apple freshness "
        "and shelf-life prediction system."
    ),

    version="1.0.0"
)


# ============================================================
# ROUTES
# ============================================================

app.include_router(
    prediction_router,
    prefix="/api/v1"
)


# ============================================================
# ROOT
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