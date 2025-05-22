import os
import random
import shutil

# Paths
train_folder = r"C:\Users\legol\OneDrive\Desktop\TwoMask_Dataset\renders"
val_folder = r"C:\Users\legol\OneDrive\Desktop\TwoMask_Dataset\validation"

# Create validation folder if not exists
os.makedirs(val_folder, exist_ok=True)

# Extensions to consider
valid_exts = ['.png', '.jpg', '.jpeg']

# Find all images recursively
image_paths = []
for root, _, files in os.walk(train_folder):
    for file in files:
        if any(file.lower().endswith(ext) for ext in valid_exts):
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, train_folder)
            image_paths.append((full_path, rel_path))

print(f"Found {len(image_paths)} images.")

# Pick 20% randomly
val_sample = random.sample(image_paths, int(len(image_paths) * 0.2))

# Copy to validation folder, preserving subfolders
for src_path, rel_path in val_sample:
    dest_path = os.path.join(val_folder, rel_path)
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    shutil.copy2(src_path, dest_path)

print(f"Copied {len(val_sample)} images to validation folder.")
