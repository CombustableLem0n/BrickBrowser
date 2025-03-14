import torch
import torchvision
import torchvision.transforms as transforms
from torchvision.datasets import CocoDetection
from torch.utils.data import DataLoader

# Define transformations
transform = transforms.Compose([
    transforms.Resize((300, 300)),  # Resize images for training
    transforms.ToTensor()
])

# Load dataset
dataset = CocoDetection(root="Parts by Color", annFile="annotations.json", transform=transform)
data_loader = DataLoader(dataset, batch_size=4, shuffle=True, collate_fn=lambda x: tuple(zip(*x)))

print(f"✅ Loaded {len(dataset)} images for training")

# Load pre-trained Faster R-CNN
model = torchvision.models.detection.fasterrcnn_resnet50_fpn(pretrained=True)

# Modify classifier for LEGO parts
num_classes = len(dataset.coco.cats) + 1  # Add 1 for background
in_features = model.roi_heads.box_predictor.cls_score.in_features
model.roi_heads.box_predictor = torch.nn.Linear(in_features, num_classes)

# Move to GPU if available
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)

import torch.optim as optim

optimizer = optim.Adam(model.parameters(), lr=0.001)

num_epochs = 10  # Adjust based on accuracy

for epoch in range(num_epochs):
    model.train()
    running_loss = 0.0

    for images, targets in data_loader:
        images = [img.to(device) for img in images]
        targets = [{k: v.to(device) for k, v in t.items()} for t in targets]

        optimizer.zero_grad()
        loss_dict = model(images, targets)
        loss = sum(loss for loss in loss_dict.values())
        loss.backward()
        optimizer.step()

        running_loss += loss.item()

    print(f"📊 Epoch {epoch+1}: Loss={running_loss/len(data_loader):.4f}")

torch.save(model.state_dict(), "lego_frcnn.pth")
print("🎉 Model saved as 'lego_frcnn.pth'")
