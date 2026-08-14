from pathlib import Path

import torch
import torch.nn as nn

from PIL import Image

from torchvision import models, transforms


class PredictionService:
    """
    Service responsible for loading the trained Apple models
    and performing inference.

    Runtime model dependency:
        model/models/*.pth

    No Python file from the model/ directory is imported.
    """

    def __init__(self):

        # DEVICE

        self.device = torch.device(
            "cuda"
            if torch.cuda.is_available()
            else "cpu"
        )

        # MODEL PATHS


        project_root = (
            Path(__file__)
            .resolve()
            .parents[2]
        )

        model_directory = (
            project_root /
            "model" /
            "models"
        )

        self.freshness_model_path = (
            model_directory /
            "apple_efficientnet_b0_best.pth"
        )

        self.shelf_life_model_path = (
            model_directory /
            "apple_shelf_life_efficientnet_b0_best.pth"
        )

        # CLASS NAMES

        self.freshness_classes = [
            "fresh",
            "rotten"
        ]

        self.shelf_life_classes = [
            "1-5 days",
            "5-10 days",
            "10-14 days"
        ]

        # IMAGE PREPROCESSING

        self.transform = transforms.Compose([

            transforms.Resize(
                (224, 224)
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

        # LOAD MODELS

        print(
            "Initializing Prediction Service..."
        )

        print(
            f"Device: {self.device}"
        )

        self.freshness_model = (
            self._load_model(
                model_path=self.freshness_model_path,
                num_classes=2
            )
        )

        print(
            "Freshness model loaded."
        )

        self.shelf_life_model = (
            self._load_model(
                model_path=self.shelf_life_model_path,
                num_classes=3
            )
        )

        print(
            "Shelf-life model loaded."
        )

        print(
            "Prediction Service initialized successfully."
        )

    # CREATE EFFICIENTNET-B0

    def _create_efficientnet(
        self,
        num_classes: int
    ):

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

    # LOAD TRAINED MODEL

    def _load_model(
        self,
        model_path: Path,
        num_classes: int
    ):

        if not model_path.exists():

            raise FileNotFoundError(
                f"Model file not found: "
                f"{model_path}"
            )

        checkpoint = torch.load(
            model_path,
            map_location=self.device
        )

        model = self._create_efficientnet(
            num_classes=num_classes
        )

        # LOAD STATE DICT

        if isinstance(
            checkpoint,
            dict
        ) and "model_state_dict" in checkpoint:

            state_dict = (
                checkpoint[
                    "model_state_dict"
                ]
            )

        else:

            # Supports a plain state_dict too
            state_dict = checkpoint

        model.load_state_dict(
            state_dict
        )

        model.to(
            self.device
        )

        model.eval()

        return model

    # IMAGE PREPROCESSING

    def _prepare_image(
        self,
        image_path: str
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

        image_tensor = self.transform(
            image
        )

        image_tensor = (
            image_tensor
            .unsqueeze(0)
            .to(self.device)
        )

        return image_tensor

    # FRESHNESS PREDICTION

    def _predict_freshness(
        self,
        image_tensor
    ):

        with torch.no_grad():

            output = (
                self.freshness_model(
                    image_tensor
                )
            )

            probabilities = torch.softmax(
                output,
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

        confidence_value = (
            confidence.item()
        )

        probability_values = (
            probabilities[0]
            .cpu()
            .tolist()
        )

        return {

            "prediction":
                self.freshness_classes[
                    predicted_index
                ],

            "confidence":
                confidence_value,

            "probabilities":
                probability_values
        }

    # SHELF-LIFE PREDICTION

    def _predict_shelf_life(
        self,
        image_tensor
    ):

        with torch.no_grad():

            output = (
                self.shelf_life_model(
                    image_tensor
                )
            )

            probabilities = torch.softmax(
                output,
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

        confidence_value = (
            confidence.item()
        )

        probability_values = (
            probabilities[0]
            .cpu()
            .tolist()
        )

        return {

            "prediction":
                self.shelf_life_classes[
                    predicted_index
                ],

            "confidence":
                confidence_value,

            "probabilities":
                probability_values
        }

    def predict_apple(
        self,
        image_path: str
    ):

        image_tensor = (
            self._prepare_image(
                image_path
            )
        )

        freshness = (
            self._predict_freshness(
                image_tensor
            )
        )

        shelf_life = (
            self._predict_shelf_life(
                image_tensor
            )
        )

        return {

            "fruit": "apple",

            "freshness":
                freshness,

            "shelf_life":
                shelf_life
        }