from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.database.database import get_db

from api.database.models import (
    Batch,
    Destination
)

from api.schemas.optimization import (
    OptimizationRequest,
    OptimizationResponse,
    OptimizedRoute
)

from api.services.genetic_optimizer import (
    GeneticOptimizer
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/api/v1/optimization",
    tags=["Genetic Optimization"]
)


# ============================================================
# OPTIMIZATION ENDPOINT
# ============================================================

@router.post(
    "/run",
    response_model=OptimizationResponse
)
def run_optimization(
    request: OptimizationRequest,
    db: Session = Depends(get_db)
):

    # ========================================================
    # 1. LOAD BATCHES
    # ========================================================

    batches_db = (
        db.query(Batch)
        .filter(
            Batch.batch_id.in_(
                request.batch_ids
            )
        )
        .all()
    )

    if not batches_db:

        raise HTTPException(
            status_code=404,
            detail="No requested batches were found."
        )

    # ========================================================
    # CHECK MISSING BATCHES
    # ========================================================

    found_batch_ids = {
        batch.batch_id
        for batch in batches_db
    }

    missing_batches = [
        batch_id
        for batch_id in request.batch_ids
        if batch_id not in found_batch_ids
    ]

    if missing_batches:

        raise HTTPException(
            status_code=404,
            detail={
                "message": "Some batches were not found.",
                "missing_batches": missing_batches
            }
        )

    # ========================================================
    # 2. CHECK BATCH ELIGIBILITY
    # ========================================================

    eligible_batches = []

    for batch in batches_db:

        if batch.batch_status in [
            "AVAILABLE",
            "FEFO_SELECTED",
            "ROUTE_RECOMMENDED"
        ]:

            eligible_batches.append(batch)

    if not eligible_batches:

        raise HTTPException(
            status_code=400,
            detail=(
                "None of the requested batches are "
                "currently eligible for optimization."
            )
        )

    # ========================================================
    # 3. LOAD ACTIVE DESTINATIONS
    # ========================================================

    destinations_db = (
        db.query(Destination)
        .filter(
            Destination.status == "ACTIVE"
        )
        .all()
    )

    if not destinations_db:

        raise HTTPException(
            status_code=400,
            detail="No active destinations are available."
        )

    # ========================================================
    # 4. PREPARE BATCH DATA
    # ========================================================

    batches = []

    for batch in eligible_batches:

        batches.append({

            "batch_id": batch.batch_id,

            "fruit": batch.fruit,

            "shelf_life_prediction": (
                batch.shelf_life_prediction
            ),

            "freshness_prediction": (
                batch.freshness_prediction
            ),

            "risk_level": batch.risk_level,

            # Quantity is not currently stored
            # in Batch model, so use 1 for now.
            "quantity_kg": 1,

            "distances": {},

            "durations": {}
        })

    # ========================================================
    # 5. PREPARE DESTINATION DATA
    # ========================================================

    destinations = []

    for destination in destinations_db:

        destinations.append({

            "destination_id": (
                destination.destination_id
            ),

            "name": destination.name,

            "destination_type": (
                destination.destination_type
            ),

            "address": destination.address,

            "latitude": destination.latitude,

            "longitude": destination.longitude,

            "capacity_kg": (
                destination.capacity_kg
            ),

            "available_capacity_kg": (
                destination.available_capacity_kg
            ),

            "accepted_fruit": (
                destination.accepted_fruit
            )
        })

    # ========================================================
    # 6. ROUTE DATA
    # ========================================================
    #
    # IMPORTANT:
    #
    # The Genetic Algorithm requires:
    #
    # batch -> destination
    # distance
    # duration
    #
    # For now we initialize these values.
    #
    # We will connect Google Routes API in the next step.
    #
    # ========================================================

    for batch in batches:

        for destination in destinations:

            destination_id = (
                destination["destination_id"]
            )

            batch["distances"][
                destination_id
            ] = 0.0

            batch["durations"][
                destination_id
            ] = 0.0

    # ========================================================
    # 7. RUN GENETIC ALGORITHM
    # ========================================================

    optimizer = GeneticOptimizer(
        population_size=50,
        generations=100,
        mutation_rate=0.10,
        crossover_rate=0.80
    )

    try:

        best_solution, best_fitness = (
            optimizer.optimize(
                batches=batches,
                destinations=destinations
            )
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Optimization failed: {str(e)}"
        )

    # ========================================================
    # 8. BUILD RESPONSE
    # ========================================================

    optimized_routes = []

    total_distance = 0.0

    total_duration = 0.0

    for batch_index, destination_index in enumerate(
        best_solution
    ):

        batch = batches[
            batch_index
        ]

        destination = destinations[
            destination_index
        ]

        destination_id = (
            destination["destination_id"]
        )

        distance = batch[
            "distances"
        ][destination_id]

        duration = batch[
            "durations"
        ][destination_id]

        # ----------------------------------------------------
        # Reason
        # ----------------------------------------------------

        reason = (
            "Destination selected by the "
            "Genetic Algorithm based on the "
            "current optimization fitness."
        )

        optimized_routes.append(

            OptimizedRoute(

                batch_id=batch["batch_id"],

                destination_id=destination_id,

                destination_name=(
                    destination["name"]
                ),

                destination_type=(
                    destination["destination_type"]
                ),

                destination_address=(
                    destination["address"]
                ),

                distance_km=distance,

                duration_minutes=duration,

                score=float(best_fitness),

                reason=reason
            )
        )

        total_distance += distance

        total_duration += duration

    # ========================================================
    # 9. RETURN RESULT
    # ========================================================

    return OptimizationResponse(

        success=True,

        message=(
            "Genetic Algorithm optimization "
            "completed successfully."
        ),

        total_batches=len(
            optimized_routes
        ),

        total_destinations=len(
            destinations
        ),

        optimized_routes=optimized_routes,

        total_distance_km=(
            total_distance
        ),

        total_duration_minutes=(
            total_duration
        ),

        optimization_score=float(
            best_fitness
        )
    )