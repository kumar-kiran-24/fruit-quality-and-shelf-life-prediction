# from datetime import datetime

# from pydantic import BaseModel, ConfigDict


# class DispatchResponse(BaseModel):

#     batch_id: str
#     batch_status: str
#     message: str

#     updated_at: datetime

#     model_config = ConfigDict(
#         from_attributes=True
#     )
    

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field




class DispatchCreate(BaseModel):

    batch_id: str = Field(
        ...,
        description="Batch ID to dispatch"
    )

    destination_id: str = Field(
        ...,
        description="Destination ID"
    )




class DispatchStatusUpdate(BaseModel):

    status: str = Field(
        ...,
        description="New dispatch status"
    )


class DispatchResponse(BaseModel):

    id: int

    dispatch_id: str

    batch_id: str

    origin_address: str

    destination_id: str

    destination_name: str

    destination_address: str

    distance_km: float

    duration_minutes: float

    dispatch_status: str

    dispatched_at: Optional[datetime] = None

    estimated_delivery_at: Optional[datetime] = None

    delivered_at: Optional[datetime] = None

    created_at: datetime

    updated_at: datetime

    class Config:
        from_attributes = True