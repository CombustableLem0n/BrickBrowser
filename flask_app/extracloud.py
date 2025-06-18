from flask import Flask, request, jsonify
from PIL import Image, ImageDraw
import io
import os
import json
from werkzeug.utils import secure_filename
from flask_cors import CORS
import torch
import torchvision
from torchvision.models.detection.faster_rcnn import FastRCNNPredictor
from torchvision.transforms import functional as F
import imghdr
import base64

from flask_cors import CORS
from requests_oauthlib import OAuth1Session
import traceback
from dotenv import load_dotenv

from google.cloud import storage

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

        def load_custom_model():
                from google.cloud import storage

                bucket_name = os.getenv('GCS_BUCKET_NAME')
                model_filename = os.getenv('MODEL_FILENAME', 'lego_detector.pth')
                local_model_path = f"/tmp/{model_filename}"

                # Download model from GCS if not already downloaded
                if not os.path.exists(local_model_path):
                    print(f"☁️ Downloading model {model_filename} from GCS bucket {bucket_name}...")
                    try:
                        client = storage.Client()
                        bucket = client.bucket(bucket_name)
                        blob = bucket.blob(model_filename)
                        blob.download_to_filename(local_model_path)
                        print("✅ Model downloaded to", local_model_path)
                    except Exception as e:
                        print("❌ Failed to download model:", e)
                        raise e

                # Load the model
                num_classes = 3
                model = torchvision.models.detection.fasterrcnn_resnet50_fpn(pretrained=False)
                in_features = model.roi_heads.box_predictor.cls_score.in_features
                model.roi_heads.box_predictor = FastRCNNPredictor(in_features, num_classes)
                model.load_state_dict(torch.load(local_model_path, map_location=torch.device('cpu')))
                model.eval()
                print("✅ Custom model loaded and ready")
                return model


        model = load_custom_model()

        image_tensor = F.to_tensor(image)
        print("🔁 Converting image to tensor...")

        with torch.no_grad():
            predictions = model([image_tensor])

        boxes = predictions[0]["boxes"]
        labels = predictions[0]["labels"]
        scores = predictions[0]["scores"]

        print("📊 All Predictions:")
        for i, (box, label, score) in enumerate(zip(boxes, labels, scores)):
            print(f" → Object {i}: Label={label.item()}, Score={score.item():.4f}, Box={box.tolist()}")

        confidence_threshold = 0.5
        print(f"⚙️ Filtering objects with confidence > {confidence_threshold}")
        filtered_boxes = [
            (box, label, score)
            for box, label, score in zip(boxes, labels, scores)
            if score > confidence_threshold
        ]
        print(f"✅ Found {len(filtered_boxes)} objects above threshold")

        highlighted_images_base64 = []

        for i, (box, label, score) in enumerate(filtered_boxes):
            img_copy = image.copy()
            draw = ImageDraw.Draw(img_copy)
            box = box.tolist()
            draw.rectangle(box, outline="red", width=5)
            draw.text((box[0], box[1] - 10), f"{score:.2f}", fill="red")

            img_byte_arr = io.BytesIO()
            img_format = file_extension.upper() if file_extension.upper() in ["JPEG", "PNG"] else "PNG"
            img_copy.save(img_byte_arr, format=img_format)
            img_byte_arr.seek(0)
            base64_img = base64.b64encode(img_byte_arr.read()).decode('utf-8')

            highlighted_images_base64.append({
                "label": int(label),
                "score": float(score),
                "image_base64": base64_img
            })

        if not highlighted_images_base64:
            print("❌ No objects detected above threshold.")
            return jsonify({"error": "No objects detected above the threshold"}), 404

        print("📤 Sending back JSON with all highlighted images (base64)")
        return jsonify({
            "results": highlighted_images_base64,
            "format": img_format.lower()
        })

    except Exception as e:
        print(f"❌ Error processing image: {e}")
        return jsonify({"error": f"Error processing image: {str(e)}"}), 500
    

load_dotenv()  # Load variables from .env into environment

consumer_key = os.getenv('CONSUMER_KEY')
consumer_secret = os.getenv('CONSUMER_SECRET')
token = os.getenv('TOKEN')
token_secret = os.getenv('TOKEN_SECRET')

@app.route('/ping', methods=['GET'])
def ping():
    return jsonify({"message": "pong"}), 200

@app.route('/check-gcs-access', methods=['GET'])
def check_gcs_access():
    try:
        bucket_name = os.getenv('GCS_BUCKET_NAME')
        test_filename = os.getenv('GCS_TEST_FILENAME', 'test-image.png')  # You can add this to .env

        print(f"🔍 Checking access to GCS file: {test_filename} in bucket: {bucket_name}")

        client = storage.Client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(test_filename)

        if blob.exists():
            print("✅ File found and accessible")
            return jsonify({"message": f"Access to {test_filename} confirmed"}), 200
        else:
            print("❌ File not found in bucket")
            return jsonify({"error": f"File {test_filename} not found in bucket {bucket_name}"}), 404

    except Exception as e:
        print(f"❌ Error checking GCS access: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/part-images', methods=['POST'])
def part_images():
    data = request.json
    part_numbers = data.get('part_numbers')

    if not part_numbers or not isinstance(part_numbers, list):
        return jsonify({'error': 'Missing or invalid part_numbers'}), 400

    oauth = OAuth1Session(
        client_key=consumer_key,
        client_secret=consumer_secret,
        resource_owner_key=token,
        resource_owner_secret=token_secret,
    )

    results = []

    try:
        for part_number in part_numbers:
            print(f"Looking up image for part {part_number}")
            image_url = None
            color_used = None

            # Step 1: Get known colors for the part
            colors_url = f'https://api.bricklink.com/api/store/v1/items/PART/{part_number}/colors'
            colors_resp = oauth.get(colors_url)

            if colors_resp.status_code == 200:
                colors_data = colors_resp.json().get('data', [])
                if colors_data:
                    # Pick the first known color's ID
                    color_used = colors_data[0].get('color_id') or colors_data[0].get('id')
                    print(f"Found known color {color_used} for part {part_number}")

                    # Step 2: Get image for that part in the first known color
                    image_url_api = f'https://api.bricklink.com/api/store/v1/items/PART/{part_number}/images/{color_used}'
                    image_resp = oauth.get(image_url_api)

                    if image_resp.status_code == 200:
                        image_data = image_resp.json().get('data', {})
                        image_url = image_data.get('thumbnail_url')
                        print(f"Found image for part {part_number} in color {color_used}")
                    else:
                        print(f"Image not found for part {part_number} in color {color_used}")
                else:
                    print(f"No known colors found for part {part_number}")
            else:
                print(f"Failed to get colors for part {part_number}, status: {colors_resp.status_code}")

            results.append({
                'part_number': part_number,
                'image_url': image_url,
                'color_id': color_used,
                'external_url': f'https://www.bricklink.com/v2/catalog/catalogitem.page?P={part_number}' + (f'&C={color_used}' if color_used else '')
            })

        return jsonify({'images': results})

    except Exception as e:
        print("Exception in /part-images:", traceback.format_exc())
        return jsonify({'error': str(e)}), 500
        

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))  # Use the Cloud Run provided port
    app.run(host="0.0.0.0", port=port, debug=False)

#  Run in terminal: python -m flask --app extra run
#  Must be ran while python_backend is in filepath
#  Example path: C:\Users\Developer\Project\python_backend)