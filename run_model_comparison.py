import os
from pathlib import Path
from ultralytics import YOLO

# Configuration
image_path = Path("C:/major-project/model/apple_yolo_dataset/images/test/00016.jpg")
output_dir = Path("C:/major-project/model_comparison_results")
output_dir.mkdir(parents=True, exist_ok=True)

models = [
    "C:/major-project/model/apple_models/apple_detection_100epochs/weights/best.pt",
    "C:/major-project/model/yolo11/runs/apple_detection_gpu/weights/best.pt",
    "C:/major-project/model/yolo11/runs/apple_detection_final_v2/weights/best.pt",
]

thresholds = [0.25, 0.15, 0.10]

results_summary = []

for model_path in models:
    model_path = Path(model_path)
    # Create a safe short name for file naming
    safe_name = model_path.parent.parent.name + "_" + model_path.parent.name + "_" + model_path.stem
    model_name = model_path.parent.parent.name + "/" + model_path.parent.name
    print(f"\n=== Loading model: {model_path} ===")
    if not model_path.exists():
        print(f"Model not found: {model_path}")
        continue
    try:
        model = YOLO(str(model_path))
    except Exception as e:
        print(f"Failed to load model: {e}")
        continue

    print(f"Model names: {model.names}")

    for conf in thresholds:
        print(f"\n-- Threshold {conf} --")
        try:
            # Run prediction
            results = model.predict(
                source=str(image_path),
                conf=conf,
                imgsz=640,
                verbose=False
            )
            res = results[0]
            boxes = res.boxes
            detections = []
            if boxes is not None and len(boxes) > 0:
                for box in boxes:
                    cls_id = int(box.cls[0].cpu().item())
                    conf_score = float(box.conf[0].cpu().item())
                    class_name = model.names.get(cls_id, str(cls_id))
                    # Only keep apple
                    if str(class_name).lower().strip() == "apple":
                        detections.append({
                            "class_id": cls_id,
                            "class_name": class_name,
                            "confidence": conf_score,
                            "bbox": box.xyxy[0].cpu().numpy().tolist()
                        })
            apple_count = len(detections)
            confidences = [d["confidence"] for d in detections]
            print(f"Apples detected: {apple_count}")
            print(f"Confidences: {[round(c,4) for c in confidences]}")

            # Save annotated image
            save_name = f"{safe_name}_conf{conf:.2f}.jpg"
            save_path = output_dir / save_name
            # Ultralytics can save with results[0].save()
            res.save(filename=str(save_path))
            print(f"Annotated image saved to {save_path}")

            results_summary.append({
                "model_path": str(model_path),
                "model_name": model_name,
                "threshold": conf,
                "apple_count": apple_count,
                "confidences": confidences,
                "annotated_path": str(save_path),
                "visual_notes": ""
            })
        except Exception as e:
            print(f"Error during inference: {e}")

# Write summary table
summary_path = output_dir / "comparison_summary.txt"
with open(summary_path, "w", encoding="utf-8") as f:
    f.write("Model Path | Confidence Threshold | Apples Detected | Confidences | Annotated Image\n")
    f.write("-" * 120 + "\n")
    for r in results_summary:
        confs = ", ".join([f"{c:.3f}" for c in r["confidences"]])
        f.write(f"{r['model_path']} | {r['threshold']:.2f} | {r['apple_count']} | {confs} | {r['annotated_path']}\n")

print(f"\nSummary written to {summary_path}")
