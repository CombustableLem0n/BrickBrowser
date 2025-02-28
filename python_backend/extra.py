from flask import Flask, request, jsonify, send_file
from PIL import Image, ImageDraw
import io
import os
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

# Set the folder for image uploads
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

# Check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/image', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        print("Error: No file part in the request")
        return jsonify({"error": "No file part"}), 400

    file = request.files['image']
    
    if not allowed_file(file.filename):
        print(f"Error: Invalid file type for {file.filename}")
        return jsonify({"error": "Invalid file type"}), 400
    
    print(f"Received file: {file.filename}")
    
    try:
        # Manually detect file type using imghdr (this is more reliable)
        file_extension = imghdr.what(file)  # Get the file type based on header
        if not file_extension:
            print(f"Error: Could not determine file format for {file.filename}")
            return jsonify({"error": "Unable to detect file format"}), 400

        print(f"Detected file format: {file_extension}")

        # Reset file pointer and open the image using PIL
        # file.seek(0)
        image = Image.open(file).convert("RGB")
        print(f"Image loaded successfully, format: {image.format}")

        # Load the pre-trained SSD model
        print("Loading pre-trained SSD model...")
        # model = torchvision.models.detection.ssd300_vgg16(weights=SSD300_VGG16_Weights.DEFAULT)
        model = torchvision.models.detection.fasterrcnn_resnet50_fpn(pretrained=True)
        model.eval()  # Set model to evaluation mode
        print("Model loaded and set to evaluation mode.")

        # Convert image to tensor for model
        print("Converting image to tensor...")
        image_tensor = F.to_tensor(image)

        # Perform inference
        print("Performing inference...")
        with torch.no_grad():
            predictions = model([image_tensor])

        # Get the predictions
        boxes = predictions[0]["boxes"]
        labels = predictions[0]["labels"]
        scores = predictions[0]["scores"]

        # Filter objects by confidence score
        confidence_threshold = 0.5  # Adjust this as needed
        print(f"Filtering objects with confidence above {confidence_threshold}...")
        filtered_boxes = [
            (box, label, score)
            for box, label, score in zip(boxes, labels, scores)
            if score > confidence_threshold
        ]

        print(f"Found {len(filtered_boxes)} objects above the confidence threshold.")

        # List to store images with single objects highlighted
        highlighted_images = []

        # Create separate images for each detected object
        print("Creating highlighted images...")
        for i, (box, label, score) in enumerate(filtered_boxes):
            img_copy = image.copy()
            draw = ImageDraw.Draw(img_copy)
            
            # Draw bounding box for this object only
            box = box.tolist()  # Convert tensor to list
            draw.rectangle(box, outline="red", width=5)
            
            # Store the image in an array
            highlighted_images.append(img_copy)

        # Check if any images were created
        if not highlighted_images:
            print("No highlighted images created.")
            return jsonify({"error": "No objects detected above the threshold"}), 404

        # Use imghdr detected file extension for saving the image
        image_format = file_extension.upper() if file_extension.upper() in ["JPEG", "PNG"] else "PNG"
        print(f"Saving the altered image in {image_format} format...")

        # Save the altered image to a BytesIO object
        img_byte_arr = io.BytesIO()
        highlighted_images[0].save(img_byte_arr, format=image_format)  # Keep original format
        img_byte_arr.seek(0)

        # Send back the altered image in the correct format
        print("Sending back the altered image...")
        return send_file(img_byte_arr, mimetype=f'image/{image_format.lower()}')
    
    except Exception as e:
        print(f"Error processing image: {e}")
        return jsonify({"error": f"Error processing image: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)

#  Run in terminal: python -m flask --app extra run
#  Must be ran while python_backend is in filepath
#  Example path: C:\Users\Developer\Project\python_backend
