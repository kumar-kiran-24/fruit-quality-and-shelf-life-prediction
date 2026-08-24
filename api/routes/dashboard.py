from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)
from sqlalchemy.orm import Session

from api.database.database import get_db
from api.database.models import (
    User,
    Batch,
    RouteRecommendation,
    Dispatch
)
from api.auth.dependencies import (
    get_current_user
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/dashboard",
    tags=["User Dashboard"]
)


# ============================================================
# GET MY BATCHES
# ============================================================

@router.get(
    "/batches",
    summary="Get all batches for the logged-in user"
)
def get_my_batches(
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db)
):

    batches = (
        db.query(Batch)
        .filter(
            Batch.user_id
            == current_user.user_id
        )
        .order_by(
            Batch.created_at.desc()
        )
        .all()
    )

    result = []

    for batch in batches:

        # --------------------------------------------
        # Get recommendation for this batch
        # --------------------------------------------

        recommendation = (
            db.query(RouteRecommendation)
            .filter(
                RouteRecommendation.batch_id
                == batch.batch_id,
                RouteRecommendation.is_selected
                == True
            )
            .order_by(
                RouteRecommendation
                .created_at.desc()
            )
            .first()
        )

        # --------------------------------------------
        # Get dispatch for this batch
        # --------------------------------------------

        dispatch = (
            db.query(Dispatch)
            .filter(
                Dispatch.batch_id
                == batch.batch_id
            )
            .order_by(
                Dispatch.created_at.desc()
            )
            .first()
        )

        batch_info = {

            "id": batch.id,
            "batch_id": batch.batch_id,
            "fruit": batch.fruit,
            "origin": batch.origin,
            "current_address":
                batch.current_address,

            # Detection info
            "number_of_images":
                batch.number_of_images,
            "total_apples_detected":
                batch.total_apples_detected,

            # AI predictions
            "freshness_prediction":
                batch.freshness_prediction,
            "freshness_confidence":
                batch.freshness_confidence,
            "shelf_life_prediction":
                batch.shelf_life_prediction,
            "shelf_life_confidence":
                batch.shelf_life_confidence,

            # Quality
            "quality_status":
                batch.quality_status,
            "risk_level":
                batch.risk_level,
            "ai_summary":
                batch.ai_summary,
            "recommended_action":
                batch.recommended_action,

            # Certificate
            "certificate_id":
                batch.certificate_id,

            # Status
            "batch_status":
                batch.batch_status,

            # Recommended buyer
            "recommended_buyer": None,
            "recommended_destination_id":
                None,
            "distance_km": None,
            "duration_minutes": None,

            # Dispatch
            "dispatch_id": None,
            "dispatch_status": None,

            # Timestamps
            "inspection_date":
                batch.inspection_date
                .isoformat()
                if batch.inspection_date
                else None,
            "created_at":
                batch.created_at
                .isoformat(),
            "updated_at":
                batch.updated_at
                .isoformat()
        }

        if recommendation:

            batch_info[
                "recommended_buyer"
            ] = (
                recommendation.destination_name
            )

            batch_info[
                "recommended_destination_id"
            ] = (
                recommendation.destination_id
            )

            batch_info[
                "distance_km"
            ] = (
                recommendation.distance_km
            )

            batch_info[
                "duration_minutes"
            ] = (
                recommendation.duration_minutes
            )

        if dispatch:

            batch_info[
                "dispatch_id"
            ] = dispatch.dispatch_id

            batch_info[
                "dispatch_status"
            ] = (
                dispatch.dispatch_status
            )

        result.append(batch_info)

    return {

        "success": True,

        "total_batches": len(result),

        "batches": result
    }


# ============================================================
# GET MY BATCH DETAIL
# ============================================================

@router.get(
    "/batches/{batch_id}",
    summary="Get details of a specific batch"
)
def get_my_batch_detail(
    batch_id: str,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db)
):

    batch = (
        db.query(Batch)
        .filter(
            Batch.batch_id == batch_id,
            Batch.user_id
            == current_user.user_id
        )
        .first()
    )

    if not batch:

        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                "Batch not found or "
                "you do not have access."
            )
        )

    # ------------------------------------------------
    # Get recommendation
    # ------------------------------------------------

    recommendation = (
        db.query(RouteRecommendation)
        .filter(
            RouteRecommendation.batch_id
            == batch.batch_id
        )
        .order_by(
            RouteRecommendation
            .created_at.desc()
        )
        .all()
    )

    # ------------------------------------------------
    # Get dispatch
    # ------------------------------------------------

    dispatch = (
        db.query(Dispatch)
        .filter(
            Dispatch.batch_id
            == batch.batch_id
        )
        .order_by(
            Dispatch.created_at.desc()
        )
        .first()
    )

    return {

        "batch": {

            "id": batch.id,
            "batch_id": batch.batch_id,
            "fruit": batch.fruit,
            "origin": batch.origin,
            "current_address":
                batch.current_address,
            "number_of_images":
                batch.number_of_images,
            "total_apples_detected":
                batch.total_apples_detected,

            "freshness_prediction":
                batch.freshness_prediction,
            "freshness_confidence":
                batch.freshness_confidence,
            "shelf_life_prediction":
                batch.shelf_life_prediction,
            "shelf_life_confidence":
                batch.shelf_life_confidence,

            "quality_status":
                batch.quality_status,
            "risk_level":
                batch.risk_level,
            "ai_summary":
                batch.ai_summary,
            "recommended_action":
                batch.recommended_action,

            "certificate_id":
                batch.certificate_id,
            "batch_status":
                batch.batch_status,

            "inspection_date":
                batch.inspection_date
                .isoformat()
                if batch.inspection_date
                else None,
            "created_at":
                batch.created_at
                .isoformat(),
            "updated_at":
                batch.updated_at
                .isoformat()
        },

        "recommendations": [

            {

                "destination_id":
                    r.destination_id,

                "destination_name":
                    r.destination_name,

                "destination_type":
                    r.destination_type,

                "destination_address":
                    r.destination_address,

                "distance_km":
                    r.distance_km,

                "duration_minutes":
                    r.duration_minutes,

                "total_score":
                    r.total_score,

                "is_selected":
                    r.is_selected,

                "status":
                    r.recommendation_status,

                "reason":
                    r.recommendation_reason
            }

            for r in recommendation
        ],

        "dispatch": {

            "dispatch_id":
                dispatch.dispatch_id
                if dispatch else None,

            "destination_name":
                dispatch.destination_name
                if dispatch else None,

            "destination_address":
                dispatch.destination_address
                if dispatch else None,

            "distance_km":
                dispatch.distance_km
                if dispatch else None,

            "duration_minutes":
                dispatch.duration_minutes
                if dispatch else None,

            "dispatch_status":
                dispatch.dispatch_status
                if dispatch else None,

            "dispatched_at":
                dispatch.dispatched_at
                .isoformat()
                if dispatch
                and dispatch.dispatched_at
                else None,

            "estimated_delivery_at":
                dispatch.estimated_delivery_at
                .isoformat()
                if dispatch
                and dispatch.estimated_delivery_at
                else None,

            "delivered_at":
                dispatch.delivered_at
                .isoformat()
                if dispatch
                and dispatch.delivered_at
                else None
        }
    }


# ============================================================
# GET MY DASHBOARD SUMMARY
# ============================================================

@router.get(
    "/summary",
    summary="Get dashboard summary stats"
)
def get_dashboard_summary(
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db)
):

    batches = (
        db.query(Batch)
        .filter(
            Batch.user_id
            == current_user.user_id
        )
        .all()
    )

    total_batches = len(batches)

    total_apples = sum(
        b.total_apples_detected or 0
        for b in batches
    )

    status_counts = {}

    for batch in batches:

        s = batch.batch_status

        status_counts[s] = (
            status_counts.get(s, 0) + 1
        )

    return {

        "success": True,

        "user_id":
            current_user.user_id,

        "user_name":
            current_user.name,

        "total_batches":
            total_batches,

        "total_apples_detected":
            total_apples,

        "status_summary":
            status_counts
    }
