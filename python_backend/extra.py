from flask import Flask, request, jsonify, send_file
from PIL import Image
import io
import os
from werkzeug.utils import secure_filename
from flask_cors import CORS

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
        print("Error: No file part")
        return jsonify({"error": "No file part"}), 400

    file = request.files['image']
    
    if not allowed_file(file.filename):
        print("Error: Invalid file type")
        return jsonify({"error": "Invalid file type"}), 400
    
    print(f"Received file: {file.filename}")
    
    try:
        # Read the image using PIL
        image = Image.open(file)
        
        # Alter the image (e.g., rotate it upside down)
        altered_image = image.rotate(180)  # Rotate the image by 180 degrees (upside down)

        # Save the altered image to a BytesIO object
        img_byte_arr = io.BytesIO()
        altered_image.save(img_byte_arr, format='JPEG')
        img_byte_arr.seek(0)

        # Send back the altered image in the response
        return send_file(img_byte_arr, mimetype='image/jpeg')
    
    except Exception as e:
        print(f"Error processing image: {e}")
        return jsonify({"error": "Error processing image"}), 500

if __name__ == '__main__':
    app.run(debug=True)

#  Run in terminal: python -m flask --app extra run
#  Must be ran while python_backend is in filepath
#  Example path: C:\Users\Developer\Project\python_backend