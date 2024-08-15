import os
import shutil
from tqdm import tqdm

def count_files(directory):
    total = 0
    for root, dirs, files in os.walk(directory):
        total += len(files)
    return total

def copy_folder(src, dst):
    if not os.path.exists(src):
        print(f"Error: Source directory '{src}' does not exist.")
        return

    # Create 'base' folder inside 'model'
    dst_base = os.path.join(dst, os.path.basename(src))
    if not os.path.exists(dst_base):
        os.makedirs(dst_base)

    total_files = count_files(src)
    
    with tqdm(total=total_files, unit='file', desc="Copying") as pbar:
        for root, dirs, files in os.walk(src):
            for dir in dirs:
                src_dir = os.path.join(root, dir)
                rel_path = os.path.relpath(src_dir, src)
                dst_dir = os.path.join(dst_base, rel_path)
                os.makedirs(dst_dir, exist_ok=True)
            
            for file in files:
                src_file = os.path.join(root, file)
                rel_path = os.path.relpath(src_file, src)
                dst_file = os.path.join(dst_base, rel_path)
                shutil.copy2(src_file, dst_file)
                pbar.update(1)

# Define the source and destination paths
source_folder = 'base'
destination_folder = 'model'

# Call the function to copy the folder
copy_folder(source_folder, destination_folder)

print(f"'{source_folder}' folder has been copied into '{destination_folder}'.")
