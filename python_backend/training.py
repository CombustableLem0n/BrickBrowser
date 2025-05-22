import os
import torch
import torchvision
import torchvision.transforms as T
from torchvision.models.detection.faster_rcnn import FastRCNNPredictor
from torch.utils.data import DataLoader
from torchvision.datasets import CocoDetection
import numpy as np
import matplotlib.pyplot as plt

# Paths
root_dir = r"C:\Users\legol\OneDrive\Desktop\TwoMask_Dataset\train_val_split"
train_dir = os.path.join(root_dir, "train")
val_dir = os.path.join(root_dir, "val")
ann_file = os.path.join(root_dir, "annotation.json")  # Must cover both train and val images or split

# Transforms
def get_transform():
    return T.Compose([
        T.ToTensor(),  # Converts PIL to Tensor and scales to [0, 1]
    ])

# Load dataset
train_coco = CocoDetection(root=train_dir, annFile=ann_file, transform=get_transform())
val_coco = CocoDetection(root=val_dir, annFile=ann_file, transform=get_transform())

# Helper: Convert COCO annotations to model-compatible target
def coco_to_target(annotations):
    boxes = []
    labels = []
    for ann in annotations:
        if "bbox" not in ann or "category_id" not in ann:
            continue
        x, y, w, h = ann["bbox"]
        boxes.append([x, y, x + w, y + h])
        labels.append(ann["category_id"])

    if len(boxes) == 0:
        boxes = torch.zeros((0, 4), dtype=torch.float32)
        labels = torch.zeros((0,), dtype=torch.int64)
    else:
        boxes = torch.tensor(boxes, dtype=torch.float32)
        labels = torch.tensor(labels, dtype=torch.int64)

    return {
        "boxes": boxes,
        "labels": labels
    }

# Custom dataset wrapper
class LegoDataset(torch.utils.data.Dataset):
    def __init__(self, coco_dataset):
        self.coco_dataset = coco_dataset

    def __getitem__(self, idx):
        img, anns = self.coco_dataset[idx]
        if not anns or len(anns) == 0:
            return self.__getitem__((idx + 1) % len(self))  # Skip images with no annotations

        target = coco_to_target(anns)
        target["image_id"] = torch.tensor([idx])
        return img, target

    def __len__(self):
        return len(self.coco_dataset)

# Wrap datasets
train_dataset = LegoDataset(train_coco)
val_dataset = LegoDataset(val_coco)

# Dataloaders
train_loader = DataLoader(train_dataset, batch_size=2, shuffle=True, collate_fn=lambda x: tuple(zip(*x)))
val_loader = DataLoader(val_dataset, batch_size=2, shuffle=False, collate_fn=lambda x: tuple(zip(*x)))

# Debug sample output
print("✅ Sample target from dataset:", train_dataset[0][1])

# Load model
def get_model(num_classes):
    model = torchvision.models.detection.fasterrcnn_resnet50_fpn(pretrained=True)
    in_features = model.roi_heads.box_predictor.cls_score.in_features
    model.roi_heads.box_predictor = FastRCNNPredictor(in_features, num_classes)
    return model

# Number of classes (+1 for background)
num_classes = len(train_dataset.coco_dataset.coco.cats) + 1
model = get_model(num_classes)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)

# Optimizer & LR scheduler
params = [p for p in model.parameters() if p.requires_grad]
optimizer = torch.optim.SGD(params, lr=0.005, momentum=0.9, weight_decay=0.0005)
lr_scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=3, gamma=0.1)

# Training loop
num_epochs = 3
for epoch in range(num_epochs):
    print(f"\n🔁 Starting Epoch {epoch + 1}/{num_epochs}")
    model.train()
    total_loss = 0

    for batch_idx, (images, targets) in enumerate(train_loader):
        print(f"📦 Processing batch {batch_idx + 1}/{len(train_loader)}")

        images = list(img.to(device) for img in images)
        targets = [{k: v.to(device) for k, v in t.items()} for t in targets]

        # First batch debug loss print
        if epoch == 0 and batch_idx == 0:
            with torch.no_grad():
                loss_dict = model(images, targets)
                print("🧪 First batch loss dict (no backward):", loss_dict)

        loss_dict = model(images, targets)
        losses = sum(loss for loss in loss_dict.values())

        optimizer.zero_grad()
        losses.backward()
        optimizer.step()

        total_loss += losses.item()

    lr_scheduler.step()
    print(f"✅ Epoch [{epoch + 1}/{num_epochs}] complete. Loss: {total_loss:.4f}")

# Save model
os.makedirs("trained_model", exist_ok=True)
torch.save(model.state_dict(), "trained_model/lego_detector.pth")
print("🎉 Model saved as trained_model/lego_detector.pth")
