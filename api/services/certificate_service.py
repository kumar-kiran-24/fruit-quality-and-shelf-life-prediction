from datetime import datetime
import uuid

from api.schemas.certificate import (
    CertificateAssessment
)

from api.services.llm_service import (
    LLMService
)


class CertificateService:

    def __init__(
        self,
        llm_service: LLMService
    ):

        self.llm_service = (
            llm_service
        )


    # CREATE CERTIFICATE

    def create_certificate(
        self,
        prediction: dict,
        batch_id: str,
        origin: str
    ):

        freshness = (
            prediction[
                "freshness"
            ]
        )

        shelf_life = (
            prediction[
                "shelf_life"
            ]
        )


        # VERIFIED MODEL OUTPUT

        freshness_prediction = (
            freshness[
                "prediction"
            ]
        )

        freshness_confidence = (
            freshness[
                "confidence"
            ]
        )


        shelf_life_prediction = (
            shelf_life[
                "prediction"
            ]
        )

        shelf_life_confidence = (
            shelf_life[
                "confidence"
            ]
        )



        system_prompt = """

You are an agricultural supply-chain
quality assessment assistant.

Your task is to create an assessment
for an Apple Digital Birth Certificate.

IMPORTANT RULES:

1. The AI model predictions are verified facts.

2. NEVER change the freshness prediction.

3. NEVER change the shelf-life prediction.

4. NEVER convert a shelf-life range into
   an exact number of days.

5. NEVER invent laboratory measurements.

6. NEVER invent storage conditions.

7. Use only the information provided.

8. You may explain the implications of
   the provided predictions.

9. Provide practical logistics recommendations.

10. Return only the requested structured fields.

"""

        user_prompt = f"""

Create a quality assessment for this
Apple batch.

Verified AI information:

Fruit:
Apple

Freshness prediction:
{freshness_prediction}

Freshness confidence:
{freshness_confidence:.4f}

Shelf-life prediction:
{shelf_life_prediction}

Shelf-life confidence:
{shelf_life_confidence:.4f}

Batch ID:
{batch_id}

Origin:
{origin}

Inspection date:
{datetime.now().isoformat()}

Determine:

- quality_status
- risk_level
- summary
- recommended_action

Do not change the model predictions.

"""


        # ====================================================
        # STRUCTURED LLM
        # ====================================================

        structured_llm = (
            self.llm_service.llm
            .with_structured_output(
                CertificateAssessment,
                method="json_schema",
                strict=True
            )
        )


        assessment = structured_llm.invoke(

            [
                (
                    "system",
                    system_prompt
                ),

                (
                    "human",
                    user_prompt
                )
            ]
        )


        

        certificate_id = (
            "DBC-APL-"
            + datetime.now().strftime(
                "%Y%m%d"
            )
            + "-"
            + uuid.uuid4().hex[:8].upper()
        )


       

        certificate = {

            "certificate_id":
                certificate_id,

            "batch_id":
                batch_id,

            "fruit":
                "apple",

            "origin":
                origin,

            "inspection_date":
                datetime.now().isoformat(),

      

            "freshness_prediction":
                freshness_prediction,

            "freshness_confidence":
                freshness_confidence,

            "shelf_life_prediction":
                shelf_life_prediction,

            "shelf_life_confidence":
                shelf_life_confidence,

            "quality_status":
                assessment.quality_status,

            "risk_level":
                assessment.risk_level,

            "summary":
                assessment.summary,

            "recommended_action":
                assessment.recommended_action,

         

            "freshness_model":
                "EfficientNet-B0",

            "shelf_life_model":
                "EfficientNet-B0"
        }


        return certificate