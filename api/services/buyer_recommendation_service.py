from sqlalchemy.orm import Session

from api.database.models import (
    Batch,
    Destination,
    RouteRecommendation
)
from api.services.shelf_life_service import (
    ShelfLifeService
)


# ============================================================
# BUYER RECOMMENDATION SERVICE
#
# Recommends the best buyer/destination for an
# apple batch based on:
#
# - Shelf-life urgency
# - Distance to buyer
# - Buyer capacity
# - Fruit compatibility
#
# Modular design allows replacing with AI/ML
# optimization later.
# ============================================================


class BuyerRecommendationService:

    def __init__(self):

        self.shelf_life_service = (
            ShelfLifeService()
        )

    # ========================================================
    # SHELF-LIFE URGENCY SCORE
    # ========================================================

    @staticmethod
    def shelf_life_urgency_score(
        estimated_days: int
    ) -> float:

        if estimated_days <= 3:

            return 100.0

        if estimated_days <= 7:

            return 70.0

        if estimated_days <= 10:

            return 40.0

        return 20.0

    # ========================================================
    # DISTANCE SCORE (closer is better)
    # ========================================================

    @staticmethod
    def distance_score(
        distance_km: float,
        max_distance: float
    ) -> float:

        if max_distance <= 0:

            return 100.0

        normalized = (
            1.0 - (distance_km / max_distance)
        )

        return max(
            0.0,
            normalized * 100.0
        )

    # ========================================================
    # CAPACITY SCORE
    # ========================================================

    @staticmethod
    def capacity_score(
        available_capacity_kg: float
    ) -> float:

        if available_capacity_kg <= 0:

            return 0.0

        return min(
            available_capacity_kg / 10000.0,
            1.0
        ) * 100.0

    # ========================================================
    # RECOMMEND BUYERS
    # ========================================================

    def recommend_buyers(
        self,
        db: Session,
        batch_id: str
    ):

        batch = (
            db.query(Batch)
            .filter(
                Batch.batch_id == batch_id
            )
            .first()
        )

        if not batch:

            raise ValueError(
                f"Batch not found: {batch_id}"
            )

        # ----------------------------------------------------
        # Get shelf-life prediction
        # ----------------------------------------------------

        shelf_life_result = (
            self.shelf_life_service
            .predict_shelf_life(
                db, batch_id
            )
        )

        estimated_days = (
            shelf_life_result[
                "estimated_shelf_life_days"
            ]
        )

        urgency = (
            shelf_life_result["urgency"]
        )

        # ----------------------------------------------------
        # Get active destinations that accept this fruit
        # ----------------------------------------------------

        destinations = (
            db.query(Destination)
            .filter(
                Destination.status == "ACTIVE"
            )
            .all()
        )

        eligible_destinations = []

        for dest in destinations:

            accepted = (
                dest.accepted_fruit
                .lower()
                .split(",")
            )

            if (
                batch.fruit.lower()
                not in [
                    v.strip()
                    for v in accepted
                ]
            ):

                continue

            if (
                dest.available_capacity_kg <= 0
            ):

                continue

            eligible_destinations.append(
                dest
            )

        if not eligible_destinations:

            return {

                "batch_id":
                    batch.batch_id,

                "recommendations": [],

                "best_buyer": None,

                "message": (
                    "No eligible buyers "
                    "found for this batch."
                )
            }

        # ----------------------------------------------------
        # Try ML recommendation first (placeholder)
        # ----------------------------------------------------

        ml_result = (
            self._recommend_with_ml(
                batch,
                eligible_destinations,
                shelf_life_result
            )
        )

        if ml_result is not None:

            return ml_result

        # ----------------------------------------------------
        # Score each destination
        # ----------------------------------------------------

        recommendations = []

        # Find max distance for normalization
        max_distance = 1.0

        for dest in eligible_destinations:

            # Check if we have route data
            route = (
                db.query(RouteRecommendation)
                .filter(
                    RouteRecommendation.batch_id
                    == batch.batch_id,
                    RouteRecommendation
                    .destination_id
                    == dest.destination_id
                )
                .order_by(
                    RouteRecommendation
                    .created_at.desc()
                )
                .first()
            )

            if route:

                if (
                    route.distance_km
                    > max_distance
                ):

                    max_distance = (
                        route.distance_km
                    )

        for dest in eligible_destinations:

            # ----------------------------------------
            # Route data
            # ----------------------------------------

            route = (
                db.query(RouteRecommendation)
                .filter(
                    RouteRecommendation.batch_id
                    == batch.batch_id,
                    RouteRecommendation
                    .destination_id
                    == dest.destination_id
                )
                .order_by(
                    RouteRecommendation
                    .created_at.desc()
                )
                .first()
            )

            distance_km = (
                route.distance_km
                if route else 50.0
            )

            duration_minutes = (
                route.duration_minutes
                if route else 120.0
            )

            # ----------------------------------------
            # Calculate scores
            # ----------------------------------------

            urgency_score = (
                self.shelf_life_urgency_score(
                    estimated_days
                )
            )

            dist_score = (
                self.distance_score(
                    distance_km,
                    max_distance
                )
            )

            cap_score = (
                self.capacity_score(
                    dest.available_capacity_kg
                )
            )

            # ----------------------------------------
            # TOTAL SCORE
            #
            # Weights:
            # Urgency (distance weight)  40%
            # Distance                   30%
            # Capacity                   20%
            # Urgency bonus              10%
            # ----------------------------------------

            total_score = (
                dist_score * 0.40
                + urgency_score * 0.30
                + cap_score * 0.20
                + (
                    100.0
                    if urgency == "CRITICAL"
                    else 50.0
                    if urgency == "MODERATE"
                    else 20.0
                ) * 0.10
            )

            # ----------------------------------------
            # Reason
            # ----------------------------------------

            reason_parts = []

            if urgency == "CRITICAL":

                reason_parts.append(
                    "Urgent shelf-life "
                    "(short remaining days)"
                )

            if dist_score > 70:

                reason_parts.append(
                    "Close proximity to buyer"
                )

            elif dist_score > 40:

                reason_parts.append(
                    "Moderate distance "
                    "to buyer"
                )

            if cap_score > 50:

                reason_parts.append(
                    "Sufficient buyer capacity"
                )

            reason = (
                "; ".join(reason_parts)
                if reason_parts
                else (
                    "Best overall match "
                    "based on scoring"
                )
            )

            recommendations.append({

                "destination_id":
                    dest.destination_id,

                "destination_name":
                    dest.name,

                "destination_type":
                    dest.destination_type,

                "destination_address":
                    dest.address,

                "latitude":
                    dest.latitude,

                "longitude":
                    dest.longitude,

                "distance_km":
                    round(
                        distance_km, 2
                    ),

                "duration_minutes":
                    round(
                        duration_minutes, 2
                    ),

                "available_capacity_kg":
                    dest.available_capacity_kg,

                "scores": {

                    "distance_score":
                        round(dist_score, 2),

                    "urgency_score":
                        round(
                            urgency_score, 2
                        ),

                    "capacity_score":
                        round(cap_score, 2),

                    "total_score":
                        round(
                            total_score, 2
                        )
                },

                "reason": reason
            })

        # ----------------------------------------------------
        # Sort by total score
        # ----------------------------------------------------

        recommendations.sort(
            key=lambda r: (
                r["scores"]["total_score"]
            ),
            reverse=True
        )

        # ----------------------------------------------------
        # Best buyer
        # ----------------------------------------------------

        best_buyer = (
            recommendations[0]
            if recommendations
            else None
        )

        return {

            "batch_id":
                batch.batch_id,

            "shelf_life": {
                "estimated_days":
                    estimated_days,
                "urgency": urgency,
                "expiry_date":
                    shelf_life_result[
                        "predicted_expiry_date"
                    ],
                "confidence":
                    shelf_life_result[
                        "confidence"
                    ]
            },

            "best_buyer": best_buyer,

            "recommendations":
                recommendations,

            "total_eligible_buyers":
                len(recommendations),

            "message": (
                f"Found "
                f"{len(recommendations)} "
                f"eligible buyers."
            )
        }

    # ========================================================
    # ML RECOMMENDATION PLACEHOLDER
    #
    # Replace this with a trained AI/ML
    # recommendation model for production.
    #
    # Return None to fall back to
    # rule-based recommendation.
    # ========================================================

    def _recommend_with_ml(
        self,
        batch,
        destinations,
        shelf_life_result
    ) -> dict | None:

        # ----------------------------------------------------
        # TODO: Integrate AI/ML recommendation here.
        #
        # Example:
        #
        #   model = load_recommendation_model()
        #   features = extract_features(
        #       batch, destinations,
        #       shelf_life_result
        #   )
        #   recommendation = model.predict(features)
        #   return format_recommendation(
        #       recommendation
        #   )
        #
        # For now, return None to use
        # rule-based recommendation.
        # ----------------------------------------------------

        return None
