from typing import List

from pydantic import BaseModel, Field


# ============================================================
# OPTIMIZATION REQUEST
# ============================================================

class OptimizationRequest(BaseModel):

    batch_ids: List[str] = Field(
        ...,
        min_length=1,
        description="Batch IDs to optimize"
    )


# ============================================================
# OPTIMIZED ROUTE
# ============================================================

class OptimizedRoute(BaseModel):

    batch_id: str

    destination_id: str

    destination_name: str

    destination_type: str

    destination_address: str

    distance_km: float

    duration_minutes: float

    score: float

    reason: str


# ============================================================
# OPTIMIZATION RESPONSE
# ============================================================

class OptimizationResponse(BaseModel):

    success: bool

    message: str

    total_batches: int

    total_destinations: int

    optimized_routes: List[OptimizedRoute]

    total_distance_km: float

    total_duration_minutes: float

    optimization_score: float