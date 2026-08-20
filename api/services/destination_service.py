from sqlalchemy.orm import Session

from api.database.models import Destination


class DestinationService:

    def create_destination(
        self,
        db: Session,
        data
    ):

        existing = (
            db.query(Destination)
            .filter(
                Destination.destination_id
                == data.destination_id
            )
            .first()
        )

        if existing:

            raise ValueError(
                "Destination already exists: "
                f"{data.destination_id}"
            )

        destination = Destination(

            destination_id=data.destination_id,

            name=data.name,

            destination_type=data.destination_type,

            address=data.address,

            latitude=data.latitude,

            longitude=data.longitude,

            capacity_kg=data.capacity_kg,

            available_capacity_kg=(
                data.available_capacity_kg
            ),

            accepted_fruit=data.accepted_fruit,

            status="ACTIVE"
        )

        db.add(destination)

        db.commit()

        db.refresh(destination)

        return destination


    def get_all_destinations(
        self,
        db: Session
    ):

        return (
            db.query(Destination)
            .filter(
                Destination.status == "ACTIVE"
            )
            .order_by(
                Destination.name
            )
            .all()
        )


    def get_destination(
        self,
        db: Session,
        destination_id: str
    ):

        return (
            db.query(Destination)
            .filter(
                Destination.destination_id
                == destination_id
            )
            .first()
        )