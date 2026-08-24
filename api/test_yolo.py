from api.services.yolo_service import YOLOService


IMAGE_PATH = r"C:\major-project\images.jpg"


def main():

    yolo = YOLOService()

    detection = yolo.get_best_apple(
        image_path=IMAGE_PATH
    )

    print()
    print("=" * 60)
    print("YOLOv11 APPLE DETECTION")
    print("=" * 60)

    if detection is None:

        print("No apple detected.")

        return

    print(
        f"Class: {detection['class_name']}"
    )

    print(
        f"Confidence: "
        f"{detection['confidence'] * 100:.2f}%"
    )

    print(
        f"Bounding Box: "
        f"{detection['bbox']}"
    )

    print("=" * 60)


if __name__ == "__main__":
    main()