from pathlib import Path
from ultralytics import YOLO

image_path = Path("C:/major-project/model/apple_yolo_dataset/images/test/00016.jpg")
model_path = Path("C:/major-project/model/yolo11/runs/apple_detection_gpu/weights/best.pt")
output_dir = Path("C:/major-project/model_comparison_results/failing_image_test")
output_dir.mkdir(parents=True, exist_ok=True)

model = YOLO(str(model_path))
print(f"Model loaded: {model_path}")
print(f"Classes: {model.names}")

thresholds = [0.25, 0.20, 0.15]

for conf in thresholds:
    results = model.predict(source=str(image_path), conf=conf, imgsz=640, verbose=False)
    res = results[0]
    boxes = res.boxes
    detections = []
    if boxes is not None:
        for box in boxes:
            cls_id = int(box.cls[0].cpu().item())
            conf_score = float(box.conf[0].cpu().item())
            class_name = model.names.get(cls_id, str(cls_id))
            if str(class_name).lower().strip() == "apple":
                detections.append({
                    "confidence": conf_score,
                    "bbox": box.xyxy[0].cpu().numpy().tolist()
                })
    print(f"\nThreshold {conf}: {len(detections)} detections")
    for i, d in enumerate(detections,1):
        print(f"  {i}. conf={d['confidence']:.4f} bbox={d['bbox']}")
    save_path = output_dir / f"direct_conf{conf:.2f}.jpg"
    res.save(filename=str(save_path))
    print(f"Saved annotated image to {save_path}")
