import os
from typing import Any
from pathlib import Path

import requests
from dotenv import load_dotenv


# ============================================================
# ENVIRONMENT
# ============================================================

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[2]
)

load_dotenv(PROJECT_ROOT / ".env")


# ============================================================
# CONFIGURATION
# ============================================================

ROUTING_PROVIDER = os.getenv(
    "ROUTING_PROVIDER",
    "openrouteservice"
).lower()

OPENROUTESERVICE_API_KEY = os.getenv(
    "OPENROUTESERVICE_API_KEY"
)

ORS_BASE_URL = (
    "https://api.heigit.org/openrouteservice"
)

ORS_MATRIX_URL = (
    f"{ORS_BASE_URL}/v2/matrix/driving-car"
)

ORS_GEOCODE_URL = (
    "https://api.heigit.org/pelias/v1/search"
)


class MapsService:

    def __init__(self):

        if ROUTING_PROVIDER != "openrouteservice":

            raise RuntimeError(
                f"Unsupported routing provider: "
                f"{ROUTING_PROVIDER}"
            )

        self.api_key = (
            OPENROUTESERVICE_API_KEY
        )

        self.has_api_key = bool(
            OPENROUTESERVICE_API_KEY
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

        # --------------------------------------------
        # If no API key, signal to caller that
        # a fallback should be used
        # --------------------------------------------

        if not self.has_api_key:

            raise RuntimeError(
                "OPENROUTESERVICE_API_KEY is not "
                "configured. Using haversine "
                "fallback."
            )


        # ----------------------------------------------------
        # Resolve origin address → coordinates
        # ----------------------------------------------------

        origin_coordinates = (
            self._resolve_origin(
                origin_address
            )
        )


        # ----------------------------------------------------
        # Build coordinates
        #
        # ORS expects:
        # [longitude, latitude]
        #
        # First coordinate = origin
        # Remaining coordinates = destinations
        # ----------------------------------------------------

        locations = [
            origin_coordinates
        ]

        for destination in destinations:

            if (
                destination.latitude is None
                or destination.longitude is None
            ):

                continue

            locations.append([
                float(destination.longitude),
                float(destination.latitude)
            ])


        if len(locations) <= 1:

            raise RuntimeError(
                "No destination coordinates are available "
                "for routing."
            )


        # ----------------------------------------------------
        # Destination index mapping
        # ----------------------------------------------------

        destination_mapping = []

        for index, destination in enumerate(
            destinations
        ):

            if (
                destination.latitude is None
                or destination.longitude is None
            ):
                continue

            # ORS matrix index:
            #
            # 0 = origin
            # 1 = first destination
            # 2 = second destination
            # ...

            destination_mapping.append(
                (
                    index,
                    len(destination_mapping) + 1
                )
            )


        # ----------------------------------------------------
        # OpenRouteService Matrix request
        # ----------------------------------------------------

        payload = {

            "locations": locations,

            "sources": [
                0
            ],

            "destinations": [
                matrix_index
                for _, matrix_index
                in destination_mapping
            ],

            "metrics": [
                "distance",
                "duration"
            ]
        }


        headers = {

            "Content-Type":
                "application/json",

            "Accept":
                "application/json",

            "Authorization":
                self.api_key
        }


        try:

            response = requests.post(

                ORS_MATRIX_URL,

                json=payload,

                headers=headers,

                timeout=30
            )

        except requests.RequestException as exc:

            raise RuntimeError(
                "OpenRouteService network error: "
                f"{str(exc)}"
            ) from exc


        # ----------------------------------------------------
        # Error handling
        # ----------------------------------------------------

        if response.status_code >= 400:

            raise RuntimeError(
                "OpenRouteService API error: "
                f"{response.status_code} "
                f"{response.text}"
            )


        try:

            result = response.json()

        except ValueError as exc:

            raise RuntimeError(
                "OpenRouteService returned "
                "an invalid JSON response."
            ) from exc


        # ----------------------------------------------------
        # Extract matrix values
        # ----------------------------------------------------

        distances = (
            result.get("distances")
        )

        durations = (
            result.get("durations")
        )


        if distances is None:

            raise RuntimeError(
                "OpenRouteService response does not "
                "contain distance data."
            )


        if durations is None:

            raise RuntimeError(
                "OpenRouteService response does not "
                "contain duration data."
            )


        if not distances:

            return []


        distance_row = distances[0]
        duration_row = durations[0]


        # ----------------------------------------------------
        # Normalize response
        #
        # Keep the same response structure that the
        # existing routing service expects.
        # ----------------------------------------------------

        normalized = []


        for position, (
            destination_index,
            matrix_index
        ) in enumerate(
            destination_mapping
        ):

            if position >= len(
                distance_row
            ):
                continue


            distance_meters = (
                distance_row[position]
            )


            duration_seconds = (
                duration_row[position]
                if position < len(duration_row)
                else None
            )


            # ORS can return null when a route
            # cannot be calculated.
            if distance_meters is None:

                continue


            if duration_seconds is None:

                continue


            normalized.append({

                "destination_index":
                    destination_index,

                "distance_km":
                    float(distance_meters)
                    / 1000.0,

                "duration_minutes":
                    float(duration_seconds)
                    / 60.0,

                "status":
                    "OK",

                "condition":
                    "ROUTE_FOUND"
            })


        return normalized


    # ========================================================
    # RESOLVE ORIGIN
    # ========================================================

    def _resolve_origin(
        self,
        origin_address: str
    ) -> list[float]:

        if not origin_address:
            raise ValueError(
                "Origin address is required for route calculation."
            )

        origin_address = origin_address.strip()

        # ----------------------------------------------------
        # Support "latitude,longitude"
        # Example:
        # 14.4673,75.9149
        # ----------------------------------------------------

        parts = origin_address.split(",")

        if len(parts) == 2:

            try:
                latitude = float(parts[0].strip())
                longitude = float(parts[1].strip())

                if (
                    -90 <= latitude <= 90
                    and
                    -180 <= longitude <= 180
                ):
                    return [
                        longitude,
                        latitude
                    ]

            except ValueError:
                pass

        # ----------------------------------------------------
        # Normalize known city name
        # ----------------------------------------------------

        normalized_address = origin_address.lower()

        if normalized_address in {
            "shivamoga",
            "shivamogga",
            "shimoga"
        }:
            origin_address = (
                "Shivamogga, Karnataka, India"
            )

        # ----------------------------------------------------
        # Nominatim geocoding
        # ----------------------------------------------------

        url = (
            "https://nominatim.openstreetmap.org/search"
        )

        params = {
            "q": origin_address,
            "format": "jsonv2",
            "limit": 1,
            "countrycodes": "in"
        }

        headers = {
            "User-Agent":
                "FruitSupplyChainPrototype/1.0"
        }

        try:

            response = requests.get(
                url,
                params=params,
                headers=headers,
                timeout=30
            )

        except requests.RequestException as exc:

            raise RuntimeError(
                "Nominatim geocoding network error: "
                f"{str(exc)}"
            ) from exc

        if response.status_code >= 400:

            raise RuntimeError(
                "Nominatim geocoding error: "
                f"{response.status_code} "
                f"{response.text}"
            )

        try:

            results = response.json()

        except ValueError as exc:

            raise RuntimeError(
                "Nominatim returned invalid JSON."
            ) from exc

        if not results:

            raise ValueError(
                "Could not geocode origin address: "
                f"{origin_address}"
            )

        latitude = float(
            results[0]["lat"]
        )

        longitude = float(
            results[0]["lon"]
        )

        # ORS requires:
        # [longitude, latitude]

        return [
            longitude,
            latitude
        ]