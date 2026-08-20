from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DestinationCreate(BaseModel):

    destination_id: str
    name: str
    destination_type: str
    address: str
    latitude: float
    longitude: float
    capacity_kg: float
    available_capacity_kg: float
    accepted_fruit: str = "apple"


class DestinationResponse(BaseModel):

    id: int
    destination_id: str
    name: str
    destination_type: str
    address: str
    latitude: float
    longitude: float
    capacity_kg: float
    available_capacity_kg: float
    accepted_fruit: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )