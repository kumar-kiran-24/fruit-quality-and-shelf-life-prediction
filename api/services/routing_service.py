from sqlalchemy.orm import Session

from api.database.models import (
    Batch,
    Destination,
    RouteRecommendation
)

from api.services.fefo_service import (
    FEFOService
)

from api.services.maps_service import (
    MapsService
)


class RoutingService:

    def __init__(self):

        self.maps_service = (
            MapsService()
        )

        self.fefo_service = (
            FEFOService()
        )


    # ========================================================
    # SHELF-LIFE SCORE
    # ========================================================

    @staticmethod
    def shelf_life_score(
        shelf_life: str
    ) -> float:

        values = {

            "1-5 days": 100.0,

            "5-10 days": 60.0,

            "10-14 days": 30.0
        }

        return values.get(
            shelf_life,
            0.0
        )


    # ========================================================
    # RISK SCORE
    # ========================================================

    @staticmethod
    def risk_score(
        risk_level: str
    ) -> float:

        values = {

            "HIGH": 100.0,

            "MEDIUM": 60.0,

            "LOW": 30.0
        }

        return values.get(
            risk_level.upper(),
            0.0
        )


    # ========================================================
    # CAPACITY SCORE
    # ========================================================

    @staticmethod
    def capacity_score(
        available_capacity: float
    ) -> float:

        if available_capacity <= 0:

            return 0.0

        # Prototype score:
        # More available capacity = better score.

        return min(
            available_capacity / 10000.0,
            1.0
        ) * 100.0


    # ========================================================
    # NORMALIZE DISTANCE
    # ========================================================

    @staticmethod
    def calculate_distance_scores(
        route_results
    ):

        if not route_results:

            return []


        distances = [

            item["distance_km"]

            for item in route_results

            if item["distance_km"] >= 0
        ]


        max_distance = max(
            distances
        )

        min_distance = min(
            distances
        )


        scores = []


        for item in route_results:

            distance = (
                item["distance_km"]
            )

            if max_distance == min_distance:

                score = 100.0

            else:

                score = (

                    (
                        max_distance
                        - distance
                    )

                    /

                    (
                        max_distance
                        - min_distance
                    )

                ) * 100.0


            updated = dict(item)

            updated[
                "distance_score"
            ] = score


            scores.append(
                updated
            )


        return scores


    # ========================================================
    # NORMALIZE DURATION
    # ========================================================

    @staticmethod
    def calculate_duration_scores(
        route_results
    ):

        if not route_results:

            return []


        durations = [

            item["duration_minutes"]

            for item in route_results

            if item["duration_minutes"] >= 0
        ]


        max_duration = max(
            durations
        )

        min_duration = min(
            durations
        )


        scores = []


        for item in route_results:

            duration = (
                item["duration_minutes"]
            )


            if (
                max_duration
                == min_duration
            ):

                score = 100.0

            else:

                score = (

                    (
                        max_duration
                        - duration
                    )

                    /

                    (
                        max_duration
                        - min_duration
                    )

                ) * 100.0


            updated = dict(item)

            updated[
                "duration_score"
            ] = score


            scores.append(
                updated
            )


        return scores


    # ========================================================
    # RECOMMEND DESTINATION
    # ========================================================

    def recommend(
        self,
        db: Session,
        batch_id: str
    ):

        # ----------------------------------------------------
        # Get batch
        # ----------------------------------------------------

        batch = (

            db.query(Batch)

            .filter(
                Batch.batch_id
                == batch_id
            )

            .first()
        )


        if not batch:

            raise ValueError(
                f"Batch not found: {batch_id}"
            )


        if not batch.current_address:

            raise ValueError(
                "Batch does not have a "
                "current_address."
            )


        # ----------------------------------------------------
        # Get active apple destinations
        # ----------------------------------------------------

        destinations = (

            db.query(Destination)

            .filter(
                Destination.status
                == "ACTIVE"
            )

            .all()
        )


        eligible_destinations = []


        for destination in destinations:

            accepted = (

                destination
                .accepted_fruit
                .lower()
                .split(",")
            )


            if (
                batch.fruit.lower()
                not in [
                    value.strip()
                    for value in accepted
                ]
            ):

                continue


            if (
                destination
                .available_capacity_kg
                <= 0
            ):

                continue


            eligible_destinations.append(
                destination
            )


        if not eligible_destinations:

            raise ValueError(
                "No eligible destinations "
                "are currently available."
            )


        # ----------------------------------------------------
        # Google route calculation
        # ----------------------------------------------------

        route_results = (
            self.maps_service.compute_routes(

                origin_address=
                    batch.current_address,

                destinations=
                    eligible_destinations
            )
        )


        if not route_results:

            raise ValueError(
                "Google Routes API returned "
                "no route results."
            )


        route_results = (
            self.calculate_distance_scores(
                route_results
            )
        )


        route_results = (
            self.calculate_duration_scores(
                route_results
            )
        )


        # ----------------------------------------------------
        # Static batch scores
        # ----------------------------------------------------

        shelf_life_score = (
            self.shelf_life_score(
                batch.shelf_life_prediction
            )
        )


        risk_score = (
            self.risk_score(
                batch.risk_level
            )
        )


        evaluated = []


        # ----------------------------------------------------
        # Score destinations
        # ----------------------------------------------------

        for route in route_results:

            destination = (
                eligible_destinations[
                    route["destination_index"]
                ]
            )


            capacity_score = (
                self.capacity_score(
                    destination
                    .available_capacity_kg
                )
            )


            suitability_score = 100.0


            # ------------------------------------------------
            # TOTAL SCORE
            #
            # Prototype weights:
            #
            # Distance       35%
            # Duration       30%
            # Shelf-life     20%
            # Capacity       10%
            # Suitability     5%
            # ------------------------------------------------

            total_score = (

                route["distance_score"]
                * 0.35

                +

                route["duration_score"]
                * 0.30

                +

                shelf_life_score
                * 0.20

                +

                capacity_score
                * 0.10

                +

                suitability_score
                * 0.05
            )


            evaluated.append({

                "destination":
                    destination,

                "route":
                    route,

                "shelf_life_score":
                    shelf_life_score,

                "risk_score":
                    risk_score,

                "capacity_score":
                    capacity_score,

                "suitability_score":
                    suitability_score,

                "total_score":
                    total_score
            })


        # ----------------------------------------------------
        # Best destination
        # ----------------------------------------------------

        evaluated.sort(

            key=lambda item:
                item["total_score"],

            reverse=True
        )


        selected = (
            evaluated[0]
        )


        # ----------------------------------------------------
        # Save all evaluations
        # ----------------------------------------------------

        saved_options = []


        for item in evaluated:

            destination = (
                item["destination"]
            )

            route = (
                item["route"]
            )

            is_selected = (
                destination.destination_id
                ==
                selected[
                    "destination"
                ].destination_id
            )


            if is_selected:

                status = (
                    "RECOMMENDED"
                )

                reason = (

                    "Selected based on the "
                    "highest routing score "
                    "after considering road "
                    "distance, travel duration, "
                    "shelf-life urgency, and "
                    "destination capacity."
                )

            else:

                status = (
                    "ALTERNATIVE"
                )

                reason = (
                    "Valid alternative destination "
                    "with a lower routing score."
                )


            recommendation = (
                RouteRecommendation(

                    batch_id=
                        batch.batch_id,

                    destination_id=
                        destination.destination_id,

                    destination_name=
                        destination.name,

                    destination_type=
                        destination.destination_type,

                    destination_address=
                        destination.address,

                    origin_address=
                        batch.current_address,

                    distance_km=
                        route["distance_km"],

                    duration_minutes=
                        route["duration_minutes"],

                    distance_score=
                        route["distance_score"],

                    duration_score=
                        route["duration_score"],

                    shelf_life_score=
                        item[
                            "shelf_life_score"
                        ],

                    capacity_score=
                        item[
                            "capacity_score"
                        ],

                    suitability_score=
                        item[
                            "suitability_score"
                        ],

                    total_score=
                        item["total_score"],

                    is_selected=
                        is_selected,

                    recommendation_status=
                        status,

                    recommendation_reason=
                        reason
                )
            )


            db.add(
                recommendation
            )


            saved_options.append({

                "destination_id":
                    destination.destination_id,

                "destination_name":
                    destination.name,

                "destination_type":
                    destination.destination_type,

                "destination_address":
                    destination.address,

                "distance_km":
                    route["distance_km"],

                "duration_minutes":
                    route["duration_minutes"],

                "total_score":
                    round(
                        item["total_score"],
                        2
                    ),

                "is_selected":
                    is_selected,

                "recommendation_status":
                    status
            })


        db.commit()


        # ----------------------------------------------------
        # Final result
        # ----------------------------------------------------

        selected_destination = (
            selected["destination"]
        )

        selected_route = (
            selected["route"]
        )


        return {

            "success": True,

            "batch_id":
                batch.batch_id,

            "origin_address":
                batch.current_address,

            "recommended_destination":
                selected_destination.name,

            "recommended_destination_id":
                selected_destination.destination_id,

            "distance_km":
                round(
                    selected_route[
                        "distance_km"
                    ],
                    2
                ),

            "duration_minutes":
                round(
                    selected_route[
                        "duration_minutes"
                    ],
                    2
                ),

            "reason": (
                "This destination has the "
                "highest routing score among "
                "the eligible destinations."
            ),

            "options":
                saved_options
        }