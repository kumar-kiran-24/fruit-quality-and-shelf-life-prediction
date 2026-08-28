from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)

from sqlalchemy.orm import Session

from api.database.database import get_db

from api.database.models import BatchImage, Batch, User

from api.schemas.batch import (
    BatchResponse,
    BatchDetailsResponse
)

from api.services.batch_service import (
    BatchService
)

from api.services.fefo_service import (
    FEFOService
)

from api.auth.dependencies import get_current_user

from api.services.llm_service import LLMService

from api.schemas.certificate import CertificateAssessment

from datetime import datetime


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(

    prefix="/batches",

    tags=["Batch Management"]
)


# ============================================================
# SERVICES
# ============================================================

batch_service = BatchService()

fefo_service = FEFOService()

llm_service = LLMService()


# ============================================================
# GET ALL BATCHES
# ============================================================

@router.get(
    "",
    response_model=list[BatchResponse]
)
def get_all_batches(

    db: Session = Depends(
        get_db
    )

):

    return batch_service.get_all_batches(
        db
    )


# ============================================================
# GET SINGLE BATCH
# ============================================================

@router.get(
    "/{batch_id}",
    response_model=BatchDetailsResponse
)
def get_batch(

    batch_id: str,

    db: Session = Depends(
        get_db
    )

):

    batch = batch_service.get_batch(
        db,
        batch_id
    )

    if not batch:

        raise HTTPException(

            status_code=404,

            detail=(
                f"Batch not found: "
                f"{batch_id}"
            )
        )

    # Fetch associated images
    images = db.query(BatchImage).filter(BatchImage.batch_id == batch_id).all()
    image_responses = []
    for img in images:
        # URL path is relative to FastAPI static mount
        url = f"/uploads/batches/{batch_id}/original/{img.filename}"
        image_responses.append({
            "id": img.id,
            "filename": img.filename,
            "url": url
        })

    # Return batch with images attached
    return {
        **batch.__dict__,
        "images": image_responses
    }


# ============================================================
# GENERATE AI QUALITY REPORT
# ============================================================

@router.post(
    "/{batch_id}/ai-report",
    summary="Generate AI Quality Report for a batch"
)
def generate_ai_report(
    batch_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # ----------------------------------------------------
    # Retrieve batch with ownership verification
    # ----------------------------------------------------

    batch = (
        db.query(Batch)
        .filter(
            Batch.batch_id == batch_id,
            Batch.user_id == current_user.user_id
        )
        .first()
    )

    if not batch:

        existing = (
            db.query(Batch)
            .filter(Batch.batch_id == batch_id)
            .first()
        )

        if existing:

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. This batch belongs to another user."
            )

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch not found: {batch_id}"
        )

    # ----------------------------------------------------
    # Validate required prediction data exists
    # ----------------------------------------------------

    if (
        not batch.freshness_prediction
        or batch.freshness_prediction == "N/A"
        or not batch.shelf_life_prediction
        or batch.shelf_life_prediction == "N/A"
    ):

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Prediction data not available. "
                "Analysis must be completed first."
            )
        )

    # ----------------------------------------------------
    # Return existing report if already generated
    # ----------------------------------------------------

    if (
        batch.ai_summary
        and batch.recommended_action
        and batch.quality_status
        and batch.quality_status != "PENDING"
    ):

        return {
            "batch_id": batch.batch_id,
            "quality_status": batch.quality_status,
            "risk_level": batch.risk_level,
            "ai_summary": batch.ai_summary,
            "recommended_action": batch.recommended_action,
            "generated_at": (
                batch.updated_at.isoformat()
                if batch.updated_at
                else datetime.utcnow().isoformat()
            ),
            "already_generated": True
        }

    # ----------------------------------------------------
    # Prepare LLM prompts with verified data only
    # ----------------------------------------------------

    system_prompt = """

You are an agricultural supply-chain quality assessment assistant.

Your task is to create an assessment for an Apple batch.

IMPORTANT RULES:

1. The AI model predictions are verified facts.
2. NEVER change the freshness prediction.
3. NEVER change the shelf-life prediction.
4. NEVER convert a shelf-life range into an exact number of days.
5. NEVER invent laboratory measurements.
6. NEVER invent storage conditions.
7. Use only the information provided.
8. You may explain the implications of the provided predictions.
9. Provide practical logistics recommendations.
10. Return only the requested structured fields.

"""

    user_prompt = f"""

Create a quality assessment for this Apple batch.

Verified AI information:

Fruit:
apple

Batch ID:
{batch.batch_id}

Origin:
{batch.origin}

Number of images processed:
{batch.number_of_images or 0}

Total apples detected:
{batch.total_apples_detected or 0}

Freshness prediction:
{batch.freshness_prediction}

Freshness confidence:
{batch.freshness_confidence:.4f}

Shelf-life prediction:
{batch.shelf_life_prediction}

Shelf-life confidence:
{batch.shelf_life_confidence:.4f}

Inspection date:
{batch.inspection_date.isoformat() if batch.inspection_date else ''}

Determine:

- quality_status
- risk_level
- summary
- recommended_action

Do not change the model predictions.

"""

    # ----------------------------------------------------
    # Generate assessment with LLM
    # ----------------------------------------------------

    try:

        structured_llm = (
            llm_service.llm
            .with_structured_output(
                CertificateAssessment,
                method="json_schema",
                strict=True
            )
        )

        assessment = structured_llm.invoke(
            [
                ("system", system_prompt),
                ("human", user_prompt)
            ]
        )

    except Exception as exc:

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LLM generation failed: {str(exc)}"
        )

    # ----------------------------------------------------
    # Persist assessment to batch
    # ----------------------------------------------------

    batch.quality_status = assessment.quality_status
    batch.risk_level = assessment.risk_level
    batch.ai_summary = assessment.summary
    batch.recommended_action = assessment.recommended_action

    db.commit()
    db.refresh(batch)

    # ----------------------------------------------------
    # Return generated report
    # ----------------------------------------------------

    return {
        "batch_id": batch.batch_id,
        "quality_status": batch.quality_status,
        "risk_level": batch.risk_level,
        "ai_summary": batch.ai_summary,
        "recommended_action": batch.recommended_action,
        "generated_at": datetime.utcnow().isoformat()
    }


# ============================================================
# FEFO QUEUE
# ============================================================

@router.get(
    "/fefo/queue"
)
def get_fefo_queue(

    db: Session = Depends(
        get_db
    )

):

    queue = fefo_service.get_fefo_queue(
        db
    )

    return {

        "success": True,

        "queue": queue
    }


# ============================================================
# DELETE BATCH
# ============================================================

@router.delete(
    "/{batch_id}",
    summary="Delete a batch"
)
def delete_batch(

    batch_id: str,

    current_user: User = Depends(get_current_user),

    db: Session = Depends(get_db)

):

    # ----------------------------------------------------
    # Retrieve batch with ownership verification
    # ----------------------------------------------------

    batch = (
        db.query(Batch)
        .filter(
            Batch.batch_id == batch_id,
            Batch.user_id == current_user.user_id
        )
        .first()
    )

    if not batch:

        existing = (
            db.query(Batch)
            .filter(Batch.batch_id == batch_id)
            .first()
        )

        if existing:

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. This batch belongs to another user."
            )

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch not found: {batch_id}"
        )

    # ----------------------------------------------------
    # Prevent deletion of in-transit or delivered batches
    # ----------------------------------------------------

    blocked_statuses = {
        "DISPATCHED",
        "IN_TRANSIT",
        "DELIVERED",
        "COMPLETED",
        "TRANSFERRED"
    }

    if (
        batch.batch_status in blocked_statuses
    ):

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Cannot delete batch with status "
                f"'{batch.batch_status}'. "
                f"Only batches in early lifecycle "
                f"stages can be deleted."
            )
        )

    # ----------------------------------------------------
    # Delete associated records
    # ----------------------------------------------------

    from api.database.models import (
        BatchImage,
        BatchStatusHistory,
        BatchTransfer,
        RouteRecommendation,
        Dispatch
    )

    # Delete images
    (
        db.query(BatchImage)
        .filter(BatchImage.batch_id == batch_id)
        .delete()
    )

    # Delete status history
    (
        db.query(BatchStatusHistory)
        .filter(BatchStatusHistory.batch_id == batch_id)
        .delete()
    )

    # Delete transfers
    (
        db.query(BatchTransfer)
        .filter(BatchTransfer.batch_id == batch_id)
        .delete()
    )

    # Delete route recommendations
    (
        db.query(RouteRecommendation)
        .filter(RouteRecommendation.batch_id == batch_id)
        .delete()
    )

    # Delete dispatches
    (
        db.query(Dispatch)
        .filter(Dispatch.batch_id == batch_id)
        .delete()
    )

    # ----------------------------------------------------
    # Delete the batch itself
    # ----------------------------------------------------

    db.delete(batch)
    db.commit()

    return {
        "success": True,
        "message": f"Batch '{batch_id}' and all associated records have been deleted.",
        "batch_id": batch_id
    }