import torch
import torchvision.transforms as transforms
from PIL import Image
from flask import Flask, request, jsonify

app = Flask(__name__)

# Load trained model
model = torchvision.models.detection.fasterrcnn_resnet50_fpn(pretrained=False)
num_classes = 193  # Adjust based on dataset
in_features = model.roi_heads.box_predictor.cls_score.in_features
model.roi_heads.box_predictor = torch.nn.Linear(in_features, num_classes)
model.load_state_dict(torch.load("lego_frcnn.pth"))
model.eval()

@app.route("/detect", methods=["POST"])
def detect():
    if "image" not in request.files:
        return jsonify({"error": "No image provided"}), 400

    image = Image.open(request.files["image"]).convert("RGB")
    transform = transforms.Compose([transforms.Resize((300, 300)), transforms.ToTensor()])
    image_tensor = transform(image).unsqueeze(0)

    with torch.no_grad():
        predictions = model(image_tensor)

    detected_objects = []
    for box, label, score in zip(predictions[0]["boxes"], predictions[0]["labels"], predictions[0]["scores"]):
        if score > 0.5:
            detected_objects.append({"part": label.item(), "confidence": score.item()})

    return jsonify(detected_objects)

if __name__ == "__main__":
    app.run(debug=True)
