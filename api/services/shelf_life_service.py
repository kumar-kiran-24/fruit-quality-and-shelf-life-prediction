from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from api.database.models import Batch


# ============================================================
# SHELF-LIFE PREDICTION SERVICE
#
# Modular service that predicts remaining shelf life
# for apple batches.
#
# This implementation uses a rule-based approach
# derived from the existing model predictions.
#
# A future ML model can replace the
# _predict_with_ml method without changing
# the overall architecture.
# ============================================================


class ShelfLifeService:

    # ========================================================
    # SHELF-LIFE MAPPING
    #
    # Maps the existing shelf_life_prediction labels
    # to estimated days remaining.
    # ========================================================

    SHELF_LIFE_DAYS_MAP = {

        "1-5 days": {
            "min_days": 1,
            "max_days": 5,
            "estimated_days": 3,
            "urgency": "CRITICAL"
        },

        "5-10 days": {
            "min_days": 5,
            "max_days": 10,
            "estimated_days": 7,
            "urgency": "MODERATE"
        },

        "10-14 days": {
            "min_days": 10,
            "max_days": 14,
            "estimated_days": 12,
            "urgency": "LOW"
        }
    }

    # ========================================================
    # FRESHNESS IMPACT
    #
    # Adjust shelf-life based on freshness prediction.
    # ========================================================

    FRESHNESS_IMPACT = {

        "fresh": 1.0,
        "rotten": 0.2
    }

    # ========================================================
    # PREDICT SHELF LIFE
    # ========================================================

    def predict_shelf_life(
        self,
        db: Session,
        batch_id: str
    ):

        batch = (
            db.query(Batch)
            .filter(
                Batch.batch_id == batch_id
            )
            .first()
        )

        if not batch:

            raise ValueError(
                f"Batch not found: {batch_id}"
            )

        # ----------------------------------------------------
        # Get base shelf-life data
        # ----------------------------------------------------

        shelf_life_label = (
            batch.shelf_life_prediction
        )

        shelf_life_data = (
            self.SHELF_LIFE_DAYS_MAP.get(
                shelf_life_label,
                {
                    "min_days": 5,
                    "max_days": 10,
                    "estimated_days": 7,
                    "urgency": "MODERATE"
                }
            )
        )

        # ----------------------------------------------------
        # Get freshness adjustment
        # ----------------------------------------------------

        freshness_label = (
            batch.freshness_prediction
            .lower()
        )

        freshness_factor = (
            self.FRESHNESS_IMPACT.get(
                freshness_label,
                0.8
            )
        )

        # ----------------------------------------------------
        # Confidence factor
        # ----------------------------------------------------

        confidence = (
            batch.shelf_life_confidence
        )

        # ----------------------------------------------------
        # Try ML prediction first (placeholder)
        # ----------------------------------------------------

        ml_result = (
            self._predict_with_ml(
                batch
            )
        )

        if ml_result is not None:

            return ml_result

        # ----------------------------------------------------
        # Rule-based prediction
        # ----------------------------------------------------

        estimated_days = (
            shelf_life_data["estimated_days"]
        )

        min_days = (
            shelf_life_data["min_days"]
        )

        max_days = (
            shelf_life_data["max_days"]
        )

        # Adjust by freshness
        adjusted_days = (
            estimated_days
            * freshness_factor
        )

        # Adjust by confidence
        adjusted_min = (
            min_days * confidence
        )

        adjusted_max = (
            max_days * confidence
        )

        # Round to integers
        adjusted_days = max(
            1,
            round(adjusted_days)
        )

        adjusted_min = max(
            1,
            round(adjusted_min)
        )

        adjusted_max = max(
            adjusted_min + 1,
            round(adjusted_max)
        )

        # ----------------------------------------------------
        # Calculate expiry date
        # ----------------------------------------------------

        now = datetime.utcnow()

        predicted_expiry = (
            now
            + timedelta(days=adjusted_days)
        )

        recommended_sale_deadline = (
            now
            + timedelta(
                days=adjusted_min
            )
        )

        # ----------------------------------------------------
        # Confidence score
        # ----------------------------------------------------

        prediction_confidence = (
            confidence
            * freshness_factor
        )

        # ----------------------------------------------------
        # Build result
        # ----------------------------------------------------

        result = {

            "batch_id":
                batch.batch_id,

            "estimated_shelf_life_days":
                adjusted_days,

            "min_shelf_life_days":
                adjusted_min,

            "max_shelf_life_days":
                adjusted_max,

            "predicted_expiry_date":
                predicted_expiry
                .isoformat(),

            "recommended_sale_deadline":
                recommended_sale_deadline
                .isoformat(),

            "confidence":
                round(
                    prediction_confidence,
                    4
                ),

            "urgency":
                shelf_life_data["urgency"],

            "shelf_life_label":
                shelf_life_label,

            "freshness_label":
                batch.freshness_prediction,

            "freshness_factor_applied":
                freshness_factor,

            "prediction_method":
                "RULE_BASED",

            "predicted_at":
                now.isoformat()
        }

        return result

    # ========================================================
    # ML PREDICTION PLACEHOLDER
    #
    # Replace this method with a trained ML model
    # for production use.
    #
    # Return None to fall back to rule-based prediction.
    # ========================================================

    def _predict_with_ml(
        self,
        batch
    ) -> dict | None:

        # ----------------------------------------------------
        # TODO: Integrate trained ML model here.
        #
        # Example:
        #
        #   model = load_shelf_life_model()
        #   features = extract_features(batch)
        #   prediction = model.predict(features)
        #   return format_prediction(prediction)
        #
        # For now, return None to use
        # rule-based prediction.
        # ----------------------------------------------------

        return None
