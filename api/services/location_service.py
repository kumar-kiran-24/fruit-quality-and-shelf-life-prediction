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

        Supports:
          - pincode only
          - address + pincode
          - address only (when pincode is None/empty)

        Returns city, state, country, latitude, longitude
        """

        # Build search queries based on what we have
        queries = []

        has_pincode = pincode and pincode.strip()
        has_address = address and address.strip()

        if has_pincode and has_address:
            # Best accuracy: try pincode alone first, then address+pincode
            queries.append(pincode.strip())
            queries.append(f"{address.strip()}, {pincode.strip()}")
        elif has_pincode:
            # Pincode only
            queries.append(pincode.strip())
        elif has_address:
            # Address only (e.g. "Raichur, Karnataka")
            queries.append(address.strip())
        else:
            # Nothing to search with
            return None, None, None, None, None

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
        search_desc = pincode if has_pincode else address
        raise ValueError(f"Unable to resolve location for: {search_desc}")
