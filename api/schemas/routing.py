from pydantic import BaseModel


class RoutingRequest(BaseModel):

    batch_id: str


class RouteOption(BaseModel):

    destination_id: str

    destination_name: str

    destination_type: str

    destination_address: str

    distance_km: float

    duration_minutes: float

    total_score: float

    is_selected: bool

    recommendation_status: str


class RoutingResponse(BaseModel):

    success: bool

    batch_id: str

    origin_address: str

    recommended_destination: str | None

    recommended_destination_id: str | None

    distance_km: float | None

    duration_minutes: float | None

    reason: str | None

    options: list[RouteOption]