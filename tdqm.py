import tarfile
import os
from tqdm import tqdm

def compress(tar_dir=None, output_file="model.tar.gz"):
    parent_dir = os.getcwd()
    os.chdir(tar_dir)
    
    # Get the total size of all files to be compressed
    total_size = sum(os.path.getsize(f) for f in os.listdir('.') if os.path.isfile(f))
    
    with tarfile.open(os.path.join(parent_dir, output_file), "w:gz") as tar:
        with tqdm(total=total_size, unit='B', unit_scale=True, desc="Compressing") as pbar:
            for item in os.listdir('.'):
                if os.path.isfile(item):
                    tar.add(item, arcname=item)
                    pbar.update(os.path.getsize(item))
                else:
                    tar.add(item, arcname=item)
    
    os.chdir(parent_dir)

compress(str(model_tar))
