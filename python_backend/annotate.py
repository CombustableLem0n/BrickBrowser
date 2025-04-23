import os
import json
from PIL import Image

# Paths
# original_dataset = r"C:\Users\legol\OneDrive\Desktop\Parts by Color"
# train_dir = r"C:\Users\legol\OneDrive\Desktop\Part_Dataset\train"
# val_dir = r"C:\Users\legol\OneDrive\Desktop\Part_Dataset\validation"

dataset_dir = r"C:\Users\legol\OneDrive\Desktop\Smaller_Dataset"
output_json = r"C:\Users\legol\OneDrive\Desktop\Smaller_Dataset\annotation.json"
categories = []
annotations = []
images = []
category_dict = {}

image_id = 0
annotation_id = 0

# Loop through all color folders
for color in os.listdir(dataset_dir):
    color_path = os.path.join(dataset_dir, color)
    if not os.path.isdir(color_path):
        continue  # Skip non-folder items

    for filename in os.listdir(color_path):
        if filename.endswith(".png"):
            part_name = filename.split(".")[0]  # Get part ID
            img_path = os.path.join(color_path, filename)
            img = Image.open(img_path)
            width, height = img.size

            # Register part name + color as a class
            category_name = f"{part_name}_{color}"
            if category_name not in category_dict:
                category_dict[category_name] = len(category_dict) + 1
                categories.append({"id": category_dict[category_name], "name": category_name})

            # Register image
            images.append({"id": image_id, "file_name": img_path, "width": width, "height": height})

            # Auto-generate bounding box (assume full image)
            annotations.append({
                "id": annotation_id,
                "image_id": image_id,
                "category_id": category_dict[category_name],
                "bbox": [0, 0, width, height],  # Full image
                "area": width * height,
                "iscrowd": 0
            })

            print(f"Annotated {image_id}")
            image_id += 1
            annotation_id += 1

# Save to JSON file
with open(output_json, "w") as f:
    json.dump({"images": images, "annotations": annotations, "categories": categories}, f)

print(f"✅ Annotations saved to {output_json}")
