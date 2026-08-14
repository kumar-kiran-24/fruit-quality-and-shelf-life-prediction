from sqlalchemy.orm import Session

from api.database.models import Batch


class FEFOService:

    # ========================================================
    # SHELF-LIFE PRIORITY
    # ========================================================

    @staticmethod
    def shelf_life_priority(
        shelf_life: str
    ) -> int:

        priority_map = {

            "1-5 days": 1,

            "5-10 days": 2,

            "10-14 days": 3
        }

        return priority_map.get(
            shelf_life,
            999
        )


    # ========================================================
    # RISK PRIORITY
    # ========================================================

    @staticmethod
    def risk_priority(
        risk_level: str
    ) -> int:

        priority_map = {

            "HIGH": 1,

            "MEDIUM": 2,

            "LOW": 3
        }

        return priority_map.get(
            risk_level.upper(),
            999
        )


    # ========================================================
    # QUALITY PRIORITY
    # ========================================================

    @staticmethod
    def quality_priority(
        quality_status: str
    ) -> int:

        priority_map = {

            "CRITICAL": 1,

            "WARNING": 2,

            "GOOD": 3
        }

        return priority_map.get(
            quality_status.upper(),
            999
        )


    # ========================================================
    # GET FEFO QUEUE
    # ========================================================

    def get_fefo_queue(
        self,
        db: Session
    ):

        # ----------------------------------------------------
        # Get available batches
        # ----------------------------------------------------

        batches = (

            db.query(Batch)

            .filter(
                Batch.batch_status
                == "AVAILABLE"
            )

            .all()
        )


        # ----------------------------------------------------
        # Sort according to FEFO
        # ----------------------------------------------------

        batches.sort(

            key=lambda batch: (

                self.shelf_life_priority(
                    batch.shelf_life_prediction
                ),

                self.risk_priority(
                    batch.risk_level
                ),

                self.quality_priority(
                    batch.quality_status
                ),

                batch.inspection_date
            )
        )


        # ----------------------------------------------------
        # Build FEFO queue
        # ----------------------------------------------------

        queue = []


        for index, batch in enumerate(
            batches,
            start=1
        ):

            shelf_priority = (
                self.shelf_life_priority(
                    batch.shelf_life_prediction
                )
            )

            risk_priority = (
                self.risk_priority(
                    batch.risk_level
                )
            )

            quality_priority = (
                self.quality_priority(
                    batch.quality_status
                )
            )


            # ------------------------------------------------
            # Determine dispatch action
            # ------------------------------------------------

            if (

                shelf_priority == 1

                or risk_priority == 1

                or quality_priority == 1

            ):

                action = "DISPATCH_NOW"


            elif shelf_priority == 2:

                action = "DISPATCH_NEXT"


            else:

                action = "NORMAL"


            # ------------------------------------------------
            # Calculate priority score
            # ------------------------------------------------

            priority_score = (
                (
                    shelf_priority * 50
                )
                +
                (
                    risk_priority * 30
                )
                +
                (
                    quality_priority * 20
                )
            )


            queue.append({

                "priority": index,

                "batch_id":
                    batch.batch_id,

                "fruit":
                    batch.fruit,

                "origin":
                    batch.origin,

                "current_address":
                    batch.current_address,

                "freshness":
                    batch.freshness_prediction,

                "freshness_confidence":
                    batch.freshness_confidence,

                "shelf_life":
                    batch.shelf_life_prediction,

                "shelf_life_confidence":
                    batch.shelf_life_confidence,

                "quality_status":
                    batch.quality_status,

                "risk_level":
                    batch.risk_level,

                "priority_score":
                    priority_score,

                "recommended_action":
                    action,

                "certificate_id":
                    batch.certificate_id
            })


        return queue