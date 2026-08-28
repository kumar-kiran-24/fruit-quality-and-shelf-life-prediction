import sys
sys.path.append('C:/major-project')
from pathlib import Path
from api.services.yolo_services import YOLOService

image_path = "C:/major-project/model/apple_yolo_dataset/images/test/00016.jpg"
service = YOLOService()
print(f"Service model path: {service.model_path}")
print(f"Classes: {service.class_names}")

for conf in [0.25, 0.20, 0.15]:
    apples = service.detect_apples(image_path=image_path, confidence_threshold=conf)
    print(f"\nService threshold {conf}: {len(apples)} apples")
    for i, a in enumerate(apples,1):
        print(f"  {i}. conf={a['confidence']:.4f} bbox={a['bbox']}")
