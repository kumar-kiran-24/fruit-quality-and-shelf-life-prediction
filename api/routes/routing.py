from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)

from sqlalchemy.orm import Session

from api.database.database import (
    get_db
)

from api.schemas.routing import (
    RoutingRequest,
    RoutingResponse
)

from api.services.routing_service import (
    RoutingService
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(

    prefix="/routing",

    tags=["Route Optimization"]
)


# ============================================================
# SERVICE
# ============================================================

routing_service = (
    RoutingService()
)


# ============================================================
# ROUTE RECOMMENDATION
# ============================================================

@router.post(
    "/recommend",
    response_model=RoutingResponse
)
def recommend_route(

    request: RoutingRequest,

    db: Session = Depends(
        get_db
    )

):

    try:

        return (
            routing_service.recommend(

                db,

                request.batch_id
            )
        )

    except ValueError as exc:

        raise HTTPException(

            status_code=400,

            detail=str(exc)
        )

    except Exception as exc:

        db.rollback()

        raise HTTPException(

            status_code=500,

            detail=(
                "Route recommendation failed: "
                f"{str(exc)}"
            )
        )