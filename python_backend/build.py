import os
import shutil
import random

# Paths
original_dataset = r"C:\Users\legol\OneDrive\Desktop\Parts by Color"
train_dir = r"C:\Users\legol\OneDrive\Desktop\Part_Dataset\train"
val_dir = r"C:\Users\legol\OneDrive\Desktop\Part_Dataset\validation"

# Create new dataset directories
os.makedirs(train_dir, exist_ok=True)
os.makedirs(val_dir, exist_ok=True)

print("✅ Dataset folders created.")

# Get all color folders
color_folders = os.listdir(original_dataset)
all_images = []

print(f"🔍 Found {len(color_folders)} color folders. Processing...")

# Loop through color folders
for color in color_folders:
    color_path = os.path.join(original_dataset, color)
    
    if not os.path.isdir(color_path):
        print(f"⚠️ Skipping {color} (not a folder).")
        continue  

    images = [img for img in os.listdir(color_path) if img.endswith(".png")]
    print(f"📂 Processing {color}: {len(images)} images found.")

    # Get all images inside the color folder
    for image_name in images:
        part = image_name.split(".")[0]  # Extract part ID
        new_name = f"{color}_{part}.png"  # Rename format
        all_images.append((os.path.join(color_path, image_name), new_name))

print(f"🔄 Shuffling {len(all_images)} images and splitting dataset...")

# Shuffle and split into train & validation (80/20 split)
random.shuffle(all_images)
split_idx = int(0.8 * len(all_images))
train_images, val_images = all_images[:split_idx], all_images[split_idx:]

print(f"📤 Moving {len(train_images)} images to training folder...")
for src_path, new_name in train_images:
    shutil.copy(src_path, os.path.join(train_dir, new_name))

print(f"📤 Moving {len(val_images)} images to validation folder...")
for src_path, new_name in val_images:
    shutil.copy(src_path, os.path.join(val_dir, new_name))

print("🎉 Dataset restructuring complete!")
print(f"📊 {len(train_images)} training images")
print(f"📊 {len(val_images)} validation images")
