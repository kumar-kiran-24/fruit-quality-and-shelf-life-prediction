import os

from typing import Any

import requests

from dotenv import load_dotenv

from pathlib import Path


# ============================================================
# ENVIRONMENT
# ============================================================

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[2]
)

load_dotenv(
    PROJECT_ROOT / ".env"
)


# ============================================================
# CONFIGURATION
# ============================================================

GOOGLE_MAPS_API_KEY = os.getenv(
    "GOOGLE_MAPS_API_KEY"
)

ROUTE_MATRIX_URL = (
    "https://routes.googleapis.com/"
    "distanceMatrix/v2:computeRouteMatrix"
)


class MapsService:

    def __init__(self):

        if not GOOGLE_MAPS_API_KEY:

            raise RuntimeError(
                "GOOGLE_MAPS_API_KEY is not configured "
                "in the .env file."
            )

        self.api_key = (
            GOOGLE_MAPS_API_KEY
        )


    # ========================================================
    # COMPUTE ROUTE MATRIX
    # ========================================================

    def compute_routes(
        self,
        origin_address: str,
        destinations: list
    ) -> list[dict[str, Any]]:

        if not destinations:

            return []


        # ----------------------------------------------------
        # Origin
        # ----------------------------------------------------

        origins = [

            {
                "waypoint": {
                    "address": origin_address
                }
            }

        ]


        # ----------------------------------------------------
        # Destinations
        # ----------------------------------------------------

        destination_waypoints = []

        for destination in destinations:

            destination_waypoints.append({

                "waypoint": {

                    "location": {

                        "latLng": {

                            "latitude":
                                destination.latitude,

                            "longitude":
                                destination.longitude
                        }
                    }
                }
            })


        # ----------------------------------------------------
        # Request
        # ----------------------------------------------------

        payload = {

            "origins":
                origins,

            "destinations":
                destination_waypoints,

            "travelMode":
                "DRIVE",

            "routingPreference":
                "TRAFFIC_AWARE",

            "units":
                "METRIC"
        }


        headers = {

            "Content-Type":
                "application/json",

            "X-Goog-Api-Key":
                self.api_key,

            "X-Goog-FieldMask":
                (
                    "originIndex,"
                    "destinationIndex,"
                    "duration,"
                    "distanceMeters,"
                    "status,"
                    "condition"
                )
        }


        response = requests.post(

            ROUTE_MATRIX_URL,

            json=payload,

            headers=headers,

            timeout=30
        )


        # ----------------------------------------------------
        # Error handling
        # ----------------------------------------------------

        if response.status_code >= 400:

            raise RuntimeError(
                "Google Routes API error: "
                f"{response.status_code} "
                f"{response.text}"
            )


        result = response.json()


        # ----------------------------------------------------
        # Normalize response
        # ----------------------------------------------------

        normalized = []


        for item in result:

            destination_index = (
                item.get(
                    "destinationIndex"
                )
            )

            if destination_index is None:

                continue


            distance_meters = (
                item.get(
                    "distanceMeters"
                )
            )


            duration_value = (
                item.get(
                    "duration"
                )
            )


            duration_seconds = (
                self._parse_duration(
                    duration_value
                )
            )


            status = item.get(
                "status"
            )


            condition = item.get(
                "condition"
            )


            if distance_meters is None:

                continue


            normalized.append({

                "destination_index":
                    destination_index,

                "distance_km":
                    distance_meters / 1000.0,

                "duration_minutes":
                    duration_seconds / 60.0,

                "status":
                    status,

                "condition":
                    condition
            })


        return normalized


    # ========================================================
    # PARSE GOOGLE DURATION
    # ========================================================

    @staticmethod
    def _parse_duration(
        duration_value
    ) -> float:

        if not duration_value:

            return 0.0


        if isinstance(
            duration_value,
            str
        ):

            if duration_value.endswith(
                "s"
            ):

                return float(
                    duration_value[:-1]
                )


        return 0.0