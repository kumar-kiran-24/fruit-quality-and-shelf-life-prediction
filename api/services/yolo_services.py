from pathlib import Path
from typing import List, Dict, Any

from PIL import Image
from ultralytics import YOLO


# ============================================================
# YOLOv11 SERVICE
# ============================================================

class YOLOService:

    def __init__(self):

        print("Initializing YOLOv11...")

        # ----------------------------------------------------
        # Model path
        # ----------------------------------------------------

        # Project root is two levels up from api/services
        project_root = Path(__file__).resolve().parents[2]
        self.model_path = (
            project_root
            / "model"
            / "yolo11"
            / "runs"
            / "apple_detection_gpu"
            / "weights"
            / "best.pt"
        )

        print(f"YOLO model path resolved to: {self.model_path}")

        if not self.model_path.exists():

            raise FileNotFoundError(
                f"YOLOv11 model not found: "
                f"{self.model_path}"
            )

        # ----------------------------------------------------
        # Load model
        # ----------------------------------------------------

        self.model = YOLO(
            str(self.model_path)
        )

        print(
            f"YOLOv11 model loaded successfully: "
            f"{self.model_path}"
        )

        # ----------------------------------------------------
        # Class names
        # ----------------------------------------------------

        self.class_names = self.model.names

        print(
            f"YOLO classes: {self.class_names}"
        )

    # ========================================================
    # DETECT FRUITS
    # ========================================================

    def detect(
        self,
        image_path: str,
        confidence_threshold: float = 0.25
    ) -> List[Dict[str, Any]]:

        # ----------------------------------------------------
        # Run YOLO
        # ----------------------------------------------------

        results = self.model.predict(
            source=image_path,
            conf=confidence_threshold,
            verbose=False
        )

        detections = []

        # ----------------------------------------------------
        # Process results
        # ----------------------------------------------------

        for result in results:

            if result.boxes is None:
                continue

            for box in result.boxes:

                # --------------------------------------------
                # Bounding box
                # --------------------------------------------

                coordinates = (
                    box.xyxy[0]
                    .cpu()
                    .numpy()
                    .tolist()
                )

                x1, y1, x2, y2 = coordinates

                # --------------------------------------------
                # Confidence
                # --------------------------------------------

                confidence = float(
                    box.conf[0].cpu().item()
                )

                # --------------------------------------------
                # Class ID
                # --------------------------------------------

                class_id = int(
                    box.cls[0].cpu().item()
                )

                # --------------------------------------------
                # Class name
                # --------------------------------------------

                class_name = self.class_names[
                    class_id
                ]

                detections.append({

                    "class_id": class_id,

                    "class_name": class_name,

                    "confidence": confidence,

                    "bbox": {
                        "x1": float(x1),
                        "y1": float(y1),
                        "x2": float(x2),
                        "y2": float(y2)
                    }
                })

        return detections

    # ========================================================
    # DETECT APPLE
    # ========================================================

    def detect_apples(
        self,
        image_path: str,
        confidence_threshold: float = 0.25
    ):

        detections = self.detect(
            image_path=image_path,
            confidence_threshold=confidence_threshold
        )

        apples = []

        for detection in detections:

            class_name = (
                detection["class_name"]
                .lower()
                .strip()
            )

            if class_name == "apple":

                apples.append(
                    detection
                )

        return apples

    # ========================================================
    # GET BEST APPLE
    # ========================================================

    def get_best_apple(
        self,
        image_path: str,
        confidence_threshold: float = 0.25
    ):

        apples = self.detect_apples(
            image_path=image_path,
            confidence_threshold=confidence_threshold
        )

        if not apples:

            return None

        return max(
            apples,
            key=lambda x: x["confidence"]
        )

    # ========================================================
    # CROP DETECTED APPLE
    # ========================================================

    def crop_apple(
        self,
        image_path: str,
        detection: Dict[str, Any],
        output_path: str
    ):

        image = Image.open(
            image_path
        ).convert("RGB")

        width, height = image.size

        bbox = detection["bbox"]

        # ----------------------------------------------------
        # Clamp coordinates
        # ----------------------------------------------------

        x1 = max(
            0,
            int(bbox["x1"])
        )

        y1 = max(
            0,
            int(bbox["y1"])
        )

        x2 = min(
            width,
            int(bbox["x2"])
        )

        y2 = min(
            height,
            int(bbox["y2"])
        )

        # ----------------------------------------------------
        # Crop
        # ----------------------------------------------------

        cropped = image.crop(
            (x1, y1, x2, y2)
        )

        # ----------------------------------------------------
        # Save
        # ----------------------------------------------------

        cropped.save(
            output_path
        )

        return output_path