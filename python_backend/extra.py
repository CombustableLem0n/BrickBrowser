from flask import Flask, request, jsonify, send_file
from PIL import Image, ImageDraw
import io
import os
import json
from werkzeug.utils import secure_filename
from flask_cors import CORS
import torch
import torchvision
from torchvision.models.detection.ssd import SSD300_VGG16_Weights
from torchvision.transforms import functional as F
import imghdr  # To detect image format
import matplotlib.pyplot as plt
import cv2
import numpy as np

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/image', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        print("❌ Error: No file part in the request")
        return jsonify({"error": "No file part"}), 400

    file = request.files['image']
    
    if not allowed_file(file.filename):
        print(f"❌ Error: Invalid file type for {file.filename}")
        return jsonify({"error": "Invalid file type"}), 400

    print(f"📥 Received file: {file.filename}")

    try:
        file_extension = imghdr.what(file)
        if not file_extension:
            print(f"❌ Error: Could not determine file format for {file.filename}")
            return jsonify({"error": "Unable to detect file format"}), 400
        print(f"🧠 Detected file format: {file_extension}")

        image = Image.open(file).convert("RGB")
        print(f"🖼️ Image loaded successfully")

        from torchvision.models.detection import fasterrcnn_resnet50_fpn
        from torchvision.models.detection.faster_rcnn import FastRCNNPredictor

        def load_custom_model():
            num_classes = 3
            model = fasterrcnn_resnet50_fpn(pretrained=False)
            in_features = model.roi_heads.box_predictor.cls_score.in_features
            model.roi_heads.box_predictor = FastRCNNPredictor(in_features, num_classes)

            model_path = r"C:\Users\legol\OneDrive\Desktop\ClassProject\trained_model\lego_detector.pth"
            model.load_state_dict(torch.load(model_path, map_location=torch.device('cpu')))
            model.eval()
            print("✅ Custom model loaded from", model_path)
            return model

        model = load_custom_model()

        image_tensor = F.to_tensor(image)
        print("🔁 Converting image to tensor...")

        with torch.no_grad():
            predictions = model([image_tensor])

        boxes = predictions[0]["boxes"]
        labels = predictions[0]["labels"]
        scores = predictions[0]["scores"]

        # DEBUG: Log all predictions before filtering
        print("📊 All Predictions:")
        for i, (box, label, score) in enumerate(zip(boxes, labels, scores)):
            print(f" → Object {i}: Label={label.item()}, Score={score.item():.4f}, Box={box.tolist()}")

        # Save raw predictions to debug_output.json
        raw_output = [
            {"label": int(label), "score": float(score), "box": box.tolist()}
            for box, label, score in zip(boxes, labels, scores)
        ]
        with open("debug_output.json", "w") as f:
            json.dump(raw_output, f, indent=2)
        print("💾 Raw predictions saved to debug_output.json")

        # Optional: Draw ALL boxes (even low-confidence) for visual inspection
        debug_image = image.copy()
        draw_debug = ImageDraw.Draw(debug_image)
        for box in boxes:
            draw_debug.rectangle(box.tolist(), outline="blue", width=2)
        debug_image.save("debug_all_boxes.png")
        print("🖼️ Debug image with all boxes saved as debug_all_boxes.png")

        # Apply confidence filtering
        confidence_threshold = 0.1
        print(f"⚙️ Filtering objects with confidence > {confidence_threshold}")
        filtered_boxes = [
            (box, label, score)
            for box, label, score in zip(boxes, labels, scores)
            if score > confidence_threshold
        ]
        print(f"✅ Found {len(filtered_boxes)} objects above threshold")

        highlighted_images = []

        for i, (box, label, score) in enumerate(filtered_boxes):
            img_copy = image.copy()
            draw = ImageDraw.Draw(img_copy)
            box = box.tolist()
            draw.rectangle(box, outline="red", width=5)
            draw.text((box[0], box[1] - 10), f"{score:.2f}", fill="red")
            highlighted_images.append(img_copy)

        if not highlighted_images:
            print("❌ No highlighted images created.")
            return jsonify({"error": "No objects detected above the threshold"}), 404

        image_format = file_extension.upper() if file_extension.upper() in ["JPEG", "PNG"] else "PNG"
        img_byte_arr = io.BytesIO()
        highlighted_images[0].save(img_byte_arr, format=image_format)
        img_byte_arr.seek(0)

        print("📤 Sending back altered image...")
        return send_file(img_byte_arr, mimetype=f'image/{image_format.lower()}')
    
    except Exception as e:
        print(f"❌ Error processing image: {e}")
        return jsonify({"error": f"Error processing image: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)


#  Run in terminal: python -m flask --app extra run
#  Must be ran while python_backend is in filepath
#  Example path: C:\Users\Developer\Project\python_backend