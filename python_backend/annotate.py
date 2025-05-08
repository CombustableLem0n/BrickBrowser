import os
import json
from PIL import Image

# Paths
train_dir = r"C:\Users\legol\OneDrive\Desktop\RenderProject\train_val_split\train"
output_json = r"C:\Users\legol\OneDrive\Desktop\RenderProject\train_val_split\annotation.json"

categories = []
annotations = []
images = []
category_dict = {}

image_id = 0
annotation_id = 0

# Loop through all part folders inside train/
for part_folder in os.listdir(train_dir):
    part_path = os.path.join(train_dir, part_folder)
    if not os.path.isdir(part_path):
        continue

    # Register part folder name as a category
    if part_folder not in category_dict:
        category_dict[part_folder] = len(category_dict) + 1
        categories.append({"id": category_dict[part_folder], "name": part_folder})

    for filename in os.listdir(part_path):
        if filename.lower().endswith(".png"):
            full_img_path = os.path.join(part_path, filename)
            relative_img_path = os.path.relpath(full_img_path, train_dir).replace("\\", "/")  # for COCO format

            try:
                with Image.open(full_img_path) as img:
                    width, height = img.size
            except Exception as e:
                print(f"❌ Could not open {full_img_path}: {e}")
                continue

            # Add image entry
            images.append({
                "id": image_id,
                "file_name": relative_img_path,
                "width": width,
                "height": height
            })

            # Add annotation (full image bounding box)
            annotations.append({
                "id": annotation_id,
                "image_id": image_id,
                "category_id": category_dict[part_folder],
                "bbox": [0, 0, width, height],
                "area": width * height,
                "iscrowd": 0
            })

            print(f"📝 Annotated image {image_id}: {relative_img_path}")
            image_id += 1
            annotation_id += 1

# Save COCO-format JSON
with open(output_json, "w") as f:
    json.dump({
        "images": images,
        "annotations": annotations,
        "categories": categories
    }, f, indent=2)

print(f"\n✅ COCO annotations saved to {output_json}")
