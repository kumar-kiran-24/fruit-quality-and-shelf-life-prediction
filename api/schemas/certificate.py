from pydantic import BaseModel, Field


class CertificateAssessment(BaseModel):

    quality_status: str = Field(
        description=(
            "Overall batch quality status: "
            "GOOD, WARNING, or CRITICAL."
        )
    )

    risk_level: str = Field(
        description=(
            "Risk level: LOW, MEDIUM, or HIGH."
        )
    )

    summary: str = Field(
        description=(
            "Short explanation of the AI "
            "assessment."
        )
    )

    recommended_action: str = Field(
        description=(
            "Recommended action for handling "
            "or logistics."
        )
    )


class DigitalBirthCertificate(BaseModel):

    certificate_id: str

    batch_id: str

    fruit: str

    origin: str

    inspection_date: str

    freshness_prediction: str

    freshness_confidence: float

    shelf_life_prediction: str

    shelf_life_confidence: float

    quality_status: str

    risk_level: str

    summary: str

    recommended_action: str

    freshness_model: str

    shelf_life_model: str