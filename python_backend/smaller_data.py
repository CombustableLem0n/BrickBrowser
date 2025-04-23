import os
import shutil

# Configuration
source_folder = r"C:\Users\legol\OneDrive\Desktop\Part_Dataset\validation"       # Change this
destination_folder = r"C:\Users\legol\OneDrive\Desktop\Smaller_Dataset\validation"    # Change this
end_terms = {"3005", "3004", "3622","3010","3001","2357"}  # Set of endings to look for (before extension)

# Create destination folder if it doesn't exist
os.makedirs(destination_folder, exist_ok=True)

# Process images
for filename in os.listdir(source_folder):
    name, ext = os.path.splitext(filename)
    if ext.lower() in [".png", ".jpg", ".jpeg"]:
        for term in end_terms:
            if name.endswith(term):
                src_path = os.path.join(source_folder, filename)
                dst_path = os.path.join(destination_folder, filename)
                shutil.copy2(src_path, dst_path)  # Use shutil.move to move instead
                print(f"Copied: {filename}")
                break
