import requests
from typing import Tuple, Optional


class LocationService:
    USER_AGENT = "FruitSupplyChainPrototype/1.0"
    NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

    @staticmethod
    def resolve_from_postal_code(
        address: Optional[str],
        pincode: Optional[str]
    ) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[float], Optional[float]]:
        """
        Resolve city, state, country and coordinates from address + postal code
        using Nominatim.

        Returns city, state, country, latitude, longitude
        """
        if not pincode:
            return None, None, None, None, None

        # Try pincode alone first, then with address for better accuracy
        queries = [pincode.strip()]
        if address and address.strip():
            queries.append(f"{address.strip()}, {pincode.strip()}")

        headers = {"User-Agent": LocationService.USER_AGENT}
        last_error = None

        for query in queries:
            params = {
                "q": query,
                "format": "jsonv2",
                "limit": 1,
                "addressdetails": 1,
            }
            try:
                resp = requests.get(
                    LocationService.NOMINATIM_URL,
                    params=params,
                    headers=headers,
                    timeout=10
                )
            except requests.RequestException as exc:
                last_error = exc
                continue

            if resp.status_code >= 400:
                last_error = ValueError(f"Location lookup failed with status {resp.status_code}")
                continue

            try:
                results = resp.json()
            except ValueError:
                last_error = ValueError("Invalid response from location service")
                continue

            if results:
                result = results[0]
                address_details = result.get("address", {}) or {}

                city = (
                    address_details.get("city")
                    or address_details.get("town")
                    or address_details.get("village")
                    or address_details.get("hamlet")
                )
                state = address_details.get("state")
                country = address_details.get("country")

                try:
                    latitude = float(result.get("lat")) if result.get("lat") else None
                    longitude = float(result.get("lon")) if result.get("lon") else None
                except (TypeError, ValueError):
                    latitude = None
                    longitude = None

                return city, state, country, latitude, longitude

        # If we reach here, all queries failed
        if last_error:
            raise last_error
        raise ValueError(f"Unable to resolve location for PIN code {pincode}")

        result = results[0]
        address_details = result.get("address", {}) or {}

        city = (
            address_details.get("city")
            or address_details.get("town")
            or address_details.get("village")
            or address_details.get("hamlet")
        )
        state = address_details.get("state")
        country = address_details.get("country")

        try:
            latitude = float(result.get("lat")) if result.get("lat") else None
            longitude = float(result.get("lon")) if result.get("lon") else None
        except (TypeError, ValueError):
            latitude = None
            longitude = None

        return city, state, country, latitude, longitude
