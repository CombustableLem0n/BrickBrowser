import torch
import torchvision
import torchvision.transforms as transforms
from torch.utils.data import DataLoader
import torchvision.datasets as datasets
import matplotlib.pyplot as plt
import cv2
import numpy as np

# Check if GPU is available
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Load a pre-trained SSD model
model = torchvision.models.detection.ssd300_vgg16(pretrained=True)
model.to(device)
model.eval()  # Set the model to evaluation mode

# Define the dataset transformation
transform = transforms.Compose([
    transforms.Resize((300, 300)),  # Resize images to 300x300 for SSD
    transforms.ToTensor()
])

# Load your dataset (modify the path as needed)
dataset = datasets.VOCDetection(root="./data", year="2012", image_set="train", transform=transform, download=True)
dataloader = DataLoader(dataset, batch_size=8, shuffle=True)

# Function to run inference on an image
def predict_image(image_path, model, threshold=0.5):
    image = cv2.imread(image_path)
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    image_tensor = transform(image_rgb).unsqueeze(0).to(device)

    with torch.no_grad():
        predictions = model(image_tensor)[0]

    # Draw bounding boxes on the image
    for i, score in enumerate(predictions["scores"]):
        if score > threshold:
            box = predictions["boxes"][i].cpu().numpy().astype(int)
            label = predictions["labels"][i].cpu().item()
            cv2.rectangle(image, (box[0], box[1]), (box[2], box[3]), (0, 255, 0), 2)
            cv2.putText(image, f"Class {label} ({score:.2f})", (box[0], box[1] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    plt.axis("off")
    plt.show()

# Example usage
image_path = "test_image.jpg"  # Replace with your test image path
predict_image(image_path, model)
