# ============================================================
# APPLE AI INFERENCE ENGINE
#
# Model 1:
#   Apple Freshness
#   Fresh / Rotten
#
# Model 2:
#   Apple Shelf Life
#   1-5 / 5-10 / 10-14 days
# ============================================================

from pathlib import Path

import torch
import torch.nn as nn

from PIL import Image

from torchvision import transforms
from torchvision import models


# ============================================================
# DEVICE
# ============================================================

DEVICE = torch.device(
    "cuda"
    if torch.cuda.is_available()
    else "cpu"
)


# ============================================================
# PROJECT PATHS
# ============================================================

# Current file:
#
# model/src/apple_predictor.py
#
# parents[0] = model/src
# parents[1] = model

PROJECT_MODEL_DIR = (
    Path(__file__)
    .resolve()
    .parents[1]
)


MODEL_DIR = (
    PROJECT_MODEL_DIR /
    "models"
)


# ============================================================
# MODEL PATHS
# ============================================================

FRESHNESS_MODEL_PATH = (
    MODEL_DIR /
    "apple_efficientnet_b0_best.pth"
)


SHELF_LIFE_MODEL_PATH = (
    MODEL_DIR /
    "apple_shelf_life_efficientnet_b0_best.pth"
)


# ============================================================
# IMAGE TRANSFORM
# ============================================================

IMAGE_SIZE = 224


IMAGE_TRANSFORM = transforms.Compose([

    transforms.Resize(
        (IMAGE_SIZE, IMAGE_SIZE)
    ),

    transforms.ToTensor(),

    transforms.Normalize(

        mean=[
            0.485,
            0.456,
            0.406
        ],

        std=[
            0.229,
            0.224,
            0.225
        ]
    )
])


# ============================================================
# MODEL BUILDER
# ============================================================

def create_efficientnet(
    num_classes: int
):

    """
    Create the same EfficientNet-B0 architecture
    used during training.
    """

    model = models.efficientnet_b0(
        weights=None
    )


    num_features = (
        model.classifier[1].in_features
    )


    model.classifier[1] = nn.Linear(
        num_features,
        num_classes
    )


    return model


# ============================================================
# LOAD CHECKPOINT
# ============================================================

def load_model(
    model_path: Path,
    num_classes: int
):

    """
    Load a trained EfficientNet model.
    """

    if not model_path.exists():

        raise FileNotFoundError(
            f"Model not found: {model_path}"
        )


    checkpoint = torch.load(
        model_path,
        map_location=DEVICE
    )


    model = create_efficientnet(
        num_classes=num_classes
    )


    model.load_state_dict(
        checkpoint[
            "model_state_dict"
        ]
    )


    model = model.to(
        DEVICE
    )


    model.eval()


    # Read class names stored during training
    class_names = checkpoint.get(
        "class_names"
    )


    if class_names is None:

        raise ValueError(
            f"class_names not found in "
            f"{model_path}"
        )


    return model, class_names


# ============================================================
# APPLE AI PREDICTOR
# ============================================================

class ApplePredictor:

    def __init__(self):

        print(
            "Initializing Apple AI..."
        )


        print(
            "Device:",
            DEVICE
        )


        # ----------------------------------------------------
        # LOAD MODEL 1
        # ----------------------------------------------------

        print(
            "Loading Model 1..."
        )


        self.freshness_model, self.freshness_classes = (
            load_model(

                FRESHNESS_MODEL_PATH,

                num_classes=2
            )
        )


        # ----------------------------------------------------
        # LOAD MODEL 2
        # ----------------------------------------------------

        print(
            "Loading Model 2..."
        )


        self.shelf_life_model, self.shelf_life_classes = (
            load_model(

                SHELF_LIFE_MODEL_PATH,

                num_classes=3
            )
        )


        print(
            "Both models loaded successfully."
        )


        print(
            "Freshness classes:",
            self.freshness_classes
        )


        print(
            "Shelf-life classes:",
            self.shelf_life_classes
        )


    # ========================================================
    # LOAD IMAGE
    # ========================================================

    def _load_image(
        self,
        image_path
    ):

        image_path = Path(
            image_path
        )


        if not image_path.exists():

            raise FileNotFoundError(
                f"Image not found: "
                f"{image_path}"
            )


        image = Image.open(
            image_path
        ).convert("RGB")


        image_tensor = IMAGE_TRANSFORM(
            image
        )


        image_tensor = (
            image_tensor
            .unsqueeze(0)
            .to(DEVICE)
        )


        return image_tensor


    # ========================================================
    # MODEL 1 - FRESHNESS
    # ========================================================

    def predict_freshness(
        self,
        image_tensor
    ):

        with torch.no_grad():

            outputs = (
                self.freshness_model(
                    image_tensor
                )
            )


            probabilities = torch.softmax(
                outputs,
                dim=1
            )


            confidence, prediction = (
                torch.max(
                    probabilities,
                    dim=1
                )
            )


        predicted_index = (
            prediction.item()
        )


        predicted_class = (
            self.freshness_classes[
                predicted_index
            ]
        )


        confidence_value = (
            confidence.item()
        )


        probability_values = (
            probabilities[0]
            .cpu()
            .numpy()
            .tolist()
        )


        return {

            "prediction":
                predicted_class,

            "confidence":
                confidence_value,

            "probabilities":
                probability_values
        }


    # ========================================================
    # MODEL 2 - SHELF LIFE
    # ========================================================

    def predict_shelf_life(
        self,
        image_tensor
    ):

        with torch.no_grad():

            outputs = (
                self.shelf_life_model(
                    image_tensor
                )
            )


            probabilities = torch.softmax(
                outputs,
                dim=1
            )


            confidence, prediction = (
                torch.max(
                    probabilities,
                    dim=1
                )
            )


        predicted_index = (
            prediction.item()
        )


        predicted_class = (
            self.shelf_life_classes[
                predicted_index
            ]
        )


        confidence_value = (
            confidence.item()
        )


        probability_values = (
            probabilities[0]
            .cpu()
            .numpy()
            .tolist()
        )


        return {

            "prediction":
                predicted_class,

            "confidence":
                confidence_value,

            "probabilities":
                probability_values
        }


    # ========================================================
    # COMPLETE APPLE PREDICTION
    # ========================================================

    def predict(
        self,
        image_path
    ):

        """
        Run both Apple models on one image.
        """

        # ----------------------------------------------------
        # Load image
        # ----------------------------------------------------

        image_tensor = (
            self._load_image(
                image_path
            )
        )


        # ----------------------------------------------------
        # Model 1
        # ----------------------------------------------------

        freshness_result = (
            self.predict_freshness(
                image_tensor
            )
        )


        # ----------------------------------------------------
        # Model 2
        # ----------------------------------------------------

        shelf_life_result = (
            self.predict_shelf_life(
                image_tensor
            )
        )


        # ----------------------------------------------------
        # Combined result
        # ----------------------------------------------------

        result = {

            "fruit":
                "apple",

            "freshness": {

                "prediction":
                    freshness_result[
                        "prediction"
                    ],

                "confidence":
                    freshness_result[
                        "confidence"
                    ],

                "probabilities":
                    freshness_result[
                        "probabilities"
                    ]
            },


            "shelf_life": {

                "prediction":
                    shelf_life_result[
                        "prediction"
                    ],

                "confidence":
                    shelf_life_result[
                        "confidence"
                    ],

                "probabilities":
                    shelf_life_result[
                        "probabilities"
                    ]
            }

        }


        return result


# ============================================================
# TEST DIRECTLY FROM TERMINAL
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 60)
    print("APPLE AI INFERENCE ENGINE")
    print("=" * 60)


    # --------------------------------------------------------
    # CHANGE THIS TO YOUR TEST IMAGE
    # --------------------------------------------------------

    TEST_IMAGE = (
        r"C:\major-project\model\extenal-test-data\images.jpg"
    )


    # --------------------------------------------------------
    # Initialize predictor
    # 

    predictor = ApplePredictor()


    # 
    # Predict

    result = predictor.predict(
        TEST_IMAGE
    )


    # Display result

    print()
    print("=" * 60)
    print("FINAL APPLE PREDICTION")
    print("=" * 60)


    print(
        "Fruit:",
        result["fruit"]
    )


    print(
        "Freshness:",
        result["freshness"]["prediction"]
    )


    print(
        "Freshness Confidence:",
        f"{result['freshness']['confidence'] * 100:.2f}%"
    )


    print(
        "Shelf Life:",
        result["shelf_life"]["prediction"]
    )


    print(
        "Shelf Life Confidence:",
        f"{result['shelf_life']['confidence'] * 100:.2f}%"
    )


    print("=" * 60)