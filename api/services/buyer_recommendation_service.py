import math
import logging

from sqlalchemy.orm import Session

from api.database.models import (
    Batch,
    Destination,
    RouteRecommendation
)
from api.services.shelf_life_service import (
    ShelfLifeService
)
from api.services.location_service import (
    LocationService
)


logger = logging.getLogger(__name__)


# ============================================================
# BUYER RECOMMENDATION SERVICE
#
# Recommends the best buyer/destination for an
# apple batch based on:
#
# - Shelf-life urgency
# - Real geographic distance from batch origin
# - Buyer capacity
# - Fruit compatibility
#
# Uses actual batch origin coordinates for distance
# calculation instead of hardcoded defaults.
# ============================================================

class BuyerRecommendationService:

    def __init__(self):

        self.shelf_life_service = (
            ShelfLifeService()
        )

    # ========================================================
    # HAVERSINE DISTANCE
    #
    # Calculate the great-circle distance between
    # two points on Earth using the Haversine formula.
    # ========================================================

    @staticmethod
    def haversine_distance(
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float
    ) -> float:
        """Return distance in km between two lat/lon points."""

        R = 6371.0  # Earth radius in km

        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)

        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)

        a = (
            math.sin(dlat / 2.0) ** 2
            + math.cos(lat1_rad)
            * math.cos(lat2_rad)
            * math.sin(dlon / 2.0) ** 2
        )

        c = 2.0 * math.atan2(
            math.sqrt(a),
            math.sqrt(1.0 - a)
        )

        return R * c

    # ========================================================
    # RESOLVE BATCH ORIGIN COORDINATES
    #
    # Attempts to resolve the batch's origin into
    # geographic coordinates using:
    # 1. Existing RouteRecommendation origin data
    # 2. LocationService geocoding from batch origin
    # 3. LocationService geocoding from current_address
    # ========================================================

    @staticmethod
    def _resolve_origin_coordinates(
        db: Session,
        batch: Batch
    ) -> tuple[float, float] | None:
        """
        Resolve the batch origin to (latitude, longitude).

        Returns None if resolution fails.
        """

        # -----------------------------------------------
        # 1. Try to extract origin from an existing
        #    RouteRecommendation (if routing was run)
        # -----------------------------------------------

        existing_route = (
            db.query(RouteRecommendation)
            .filter(
                RouteRecommendation.batch_id
                == batch.batch_id
            )
            .order_by(
                RouteRecommendation.created_at.desc()
            )
            .first()
        )

        if existing_route:
            logger.info(
                "[Routing] Found existing "
                "RouteRecommendation for batch "
                "%s with origin_address=%s",
                batch.batch_id,
                existing_route.origin_address
            )

        # -----------------------------------------------
        # 2. Geocode using LocationService
        #    Try batch.origin first (harvest location),
        #    then batch.current_address as fallback
        # -----------------------------------------------

        location_service = LocationService()

        # Try origin (harvest location)
        origin = (
            batch.origin
            if batch.origin
            else None
        )

        current_addr = (
            batch.current_address
            if batch.current_address
            else None
        )

        # Try origin first
        if origin:
            try:
                _, _, _, lat, lon = (
                    location_service
                    .resolve_from_postal_code(
                        address=origin,
                        pincode=None
                    )
                )

                if lat is not None and lon is not None:
                    logger.info(
                        "[Routing] Resolved batch "
                        "%s origin '%s' to "
                        "lat=%s, lon=%s",
                        batch.batch_id,
                        origin,
                        lat,
                        lon
                    )
                    return (lat, lon)

            except Exception as exc:
                logger.warning(
                    "[Routing] Failed to resolve "
                    "origin '%s' for batch %s: %s",
                    origin,
                    batch.batch_id,
                    exc
                )

        # Try current_address
        if current_addr:
            try:
                _, _, _, lat, lon = (
                    location_service
                    .resolve_from_postal_code(
                        address=current_addr,
                        pincode=None
                    )
                )

                if lat is not None and lon is not None:
                    logger.info(
                        "[Routing] Resolved batch "
                        "%s current_address '%s' "
                        "to lat=%s, lon=%s",
                        batch.batch_id,
                        current_addr,
                        lat,
                        lon
                    )
                    return (lat, lon)

            except Exception as exc:
                logger.warning(
                    "[Routing] Failed to resolve "
                    "current_address '%s' for "
                    "batch %s: %s",
                    current_addr,
                    batch.batch_id,
                    exc
                )

        logger.error(
            "[Routing] Could not resolve "
            "origin coordinates for batch %s "
            "(origin=%s, current_address=%s)",
            batch.batch_id,
            origin,
            current_addr
        )

        return None

    # ========================================================
    # CALCULATE DISTANCE TO DESTINATION
    #
    # Uses pre-existing RouteRecommendation data if
    # available, otherwise calculates using haversine
    # from batch origin to destination coordinates.
    # ========================================================

    def _calculate_distance(
        self,
        db: Session,
        batch: Batch,
        destination: Destination,
        origin_coords: tuple[float, float] | None
    ) -> tuple[float, float]:
        """
        Return (distance_km, duration_minutes)
        for the given batch -> destination pair.
        """

        # -----------------------------------------------
        # 1. Check for existing RouteRecommendation
        # -----------------------------------------------

        route = (
            db.query(RouteRecommendation)
            .filter(
                RouteRecommendation.batch_id
                == batch.batch_id,
                RouteRecommendation.destination_id
                == destination.destination_id
            )
            .order_by(
                RouteRecommendation.created_at.desc()
            )
            .first()
        )

        if route:
            logger.info(
                "[Routing] Using existing "
                "RouteRecommendation for "
                "batch %s -> %s: "
                "distance=%.2f km, "
                "duration=%.2f min",
                batch.batch_id,
                destination.destination_id,
                route.distance_km,
                route.duration_minutes
            )
            return (
                route.distance_km,
                route.duration_minutes
            )

        # -----------------------------------------------
        # 2. Try MapsService for actual road
        #    distance calculation (most accurate)
        # -----------------------------------------------

        try:
            from api.services.maps_service import (
                MapsService
            )

            maps_service = MapsService()

            origin_address = (
                batch.current_address
                or batch.origin
                or ""
            )

            if origin_address:

                route_results = (
                    maps_service.compute_routes(
                        origin_address=origin_address,
                        destinations=[destination]
                    )
                )

                if route_results:
                    result = route_results[0]

                    logger.info(
                        "[Routing] MapsService "
                        "computed route for "
                        "batch %s -> %s (%s): "
                        "distance=%.2f km, "
                        "duration=%.2f min",
                        batch.batch_id,
                        destination.destination_id,
                        destination.name,
                        result["distance_km"],
                        result["duration_minutes"]
                    )

                    return (
                        result["distance_km"],
                        result["duration_minutes"]
                    )

        except Exception as exc:
            logger.warning(
                "[Routing] MapsService failed "
                "for batch %s -> %s: %s",
                batch.batch_id,
                destination.destination_id,
                exc
            )

        # -----------------------------------------------
        # 3. Fallback: calculate using haversine
        #    from batch origin to destination
        # -----------------------------------------------

        if (
            origin_coords is not None
            and destination.latitude is not None
            and destination.longitude is not None
        ):

            origin_lat, origin_lon = origin_coords

            dest_lat = float(
                destination.latitude
            )
            dest_lon = float(
                destination.longitude
            )

            distance_km = (
                self.haversine_distance(
                    origin_lat,
                    origin_lon,
                    dest_lat,
                    dest_lon
                )
            )

            # Estimate duration assuming
            # avg speed of 60 km/h for road
            # (haversine is straight-line,
            # road is typically 1.3x longer)
            road_distance = distance_km * 1.3
            duration_minutes = (
                (road_distance / 60.0) * 60.0
            )

            logger.info(
                "[Routing] Calculated distance "
                "for batch %s -> %s "
                "(%s): "
                "haversine=%.2f km, "
                "est_road=%.2f km, "
                "est_duration=%.2f min",
                batch.batch_id,
                destination.destination_id,
                destination.name,
                distance_km,
                road_distance,
                duration_minutes
            )

            return (
                road_distance,
                duration_minutes
            )

        # -----------------------------------------------
        # 4. Absolute fallback
        # -----------------------------------------------

        logger.warning(
            "[Routing] Using fallback "
            "distance for batch %s -> %s (%s)",
            batch.batch_id,
                destination.destination_id,
                destination.name
        )

        return (50.0, 120.0)

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

        # -------------------------------------------
        # Log batch origin details
        # -------------------------------------------

        logger.info(
            "[Routing] ========================================"
        )
        logger.info(
            "[Routing] BUYER RECOMMENDATION for batch: %s",
            batch.batch_id
        )
        logger.info(
            "[Routing] Batch origin: %s",
            batch.origin
        )
        logger.info(
            "[Routing] Batch current_address: %s",
            batch.current_address
        )
        logger.info(
            "[Routing] ========================================"
        )

        # -------------------------------------------
        # Resolve batch origin coordinates
        # -------------------------------------------

        origin_coords = (
            self._resolve_origin_coordinates(
                db, batch
            )
        )

        if origin_coords:
            logger.info(
                "[Routing] Resolved origin "
                "coordinates: lat=%s, lon=%s",
                origin_coords[0],
                origin_coords[1]
            )
        else:
            logger.warning(
                "[Routing] Could NOT resolve "
                "origin coordinates for batch %s. "
                "Distance calculation will use "
                "fallback values.",
                batch.batch_id
            )

        # ---------------------------------------------------
        # Get shelf-life prediction
        # ---------------------------------------------------

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

        logger.info(
            "[Routing] Shelf life: %d days, "
            "urgency: %s",
            estimated_days,
            urgency
        )

        # ---------------------------------------------------
        # Get active destinations that accept this fruit
        # ---------------------------------------------------

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

            eligible_destinations.append(dest)

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

        logger.info(
            "[Routing] Found %d eligible "
            "destinations",
            len(eligible_destinations)
        )

        # ---------------------------------------------------
        # Try ML recommendation first (placeholder)
        # ---------------------------------------------------

        ml_result = (
            self._recommend_with_ml(
                batch,
                eligible_destinations,
                shelf_life_result
            )
        )

        if ml_result is not None:

            return ml_result

        # ---------------------------------------------------
        # Calculate real distances for each destination
        # ---------------------------------------------------

        distance_data = []

        for dest in eligible_destinations:

            distance_km, duration_minutes = (
                self._calculate_distance(
                    db, batch, dest,
                    origin_coords
                )
            )

            distance_data.append({
                "destination": dest,
                "distance_km": distance_km,
                "duration_minutes": (
                    duration_minutes
                )
            })

        # Find max distance for normalization
        max_distance = max(
            d["distance_km"]
            for d in distance_data
        ) if distance_data else 1.0

        if max_distance <= 0:
            max_distance = 1.0

        # ---------------------------------------------------
        # Score each destination
        # ---------------------------------------------------

        recommendations = []

        for data in distance_data:

            dest = data["destination"]
            distance_km = data["distance_km"]
            duration_minutes = (
                data["duration_minutes"]
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
            # Distance                   40%
            # Urgency (shelf-life)       30%
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

            # ----------------------------------------
            # Log routing details
            # ----------------------------------------

            logger.info(
                "[Routing] ----------------------------------------"
            )
            logger.info(
                "[Routing] Batch ID: %s",
                batch.batch_id
            )
            logger.info(
                "[Routing] Origin: %s",
                batch.origin
            )
            if origin_coords:
                logger.info(
                    "[Routing] Origin coords: "
                    "lat=%s, lon=%s",
                    origin_coords[0],
                    origin_coords[1]
                )
            logger.info(
                "[Routing] Destination: %s (%s)",
                dest.name,
                dest.destination_id
            )
            logger.info(
                "[Routing] Dest coords: "
                "lat=%s, lon=%s",
                dest.latitude,
                dest.longitude
            )
            logger.info(
                "[Routing] Distance: %.2f km",
                distance_km
            )
            logger.info(
                "[Routing] Duration: %.2f min",
                duration_minutes
            )
            logger.info(
                "[Routing] Shelf-life/FEFO "
                "priority: %d days (%s)",
                estimated_days,
                urgency
            )
            logger.info(
                "[Routing] Scores: "
                "dist=%.2f, urgency=%.2f, "
                "capacity=%.2f, total=%.2f",
                dist_score,
                urgency_score,
                cap_score,
                total_score
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

        # ---------------------------------------------------
        # Sort by total score
        # ---------------------------------------------------

        recommendations.sort(
            key=lambda r: (
                r["scores"]["total_score"]
            ),
            reverse=True
        )

        # ---------------------------------------------------
        # Best buyer
        # ---------------------------------------------------

        best_buyer = (
            recommendations[0]
            if recommendations
            else None
        )

        # ---------------------------------------------------
        # Log final ranking
        # ---------------------------------------------------

        logger.info(
            "[Routing] ========================================"
        )
        logger.info(
            "[Routing] FINAL RANKING for batch %s "
            "(origin: %s)",
            batch.batch_id,
            batch.origin
        )

        for rank, rec in enumerate(
            recommendations, 1
        ):

            logger.info(
                "[Routing] #%d: %s "
                "(distance=%.2f km, "
                "score=%.2f)%s",
                rank,
                rec["destination_name"],
                rec["distance_km"],
                rec["scores"]["total_score"],
                " *** SELECTED ***"
                if rank == 1
                else ""
            )

        logger.info(
            "[Routing] ========================================"
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

        # ---------------------------------------------------
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
        # ---------------------------------------------------

        return None
