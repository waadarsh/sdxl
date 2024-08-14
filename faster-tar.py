import os
import subprocess
from tqdm.notebook import tqdm

def fast_compress_pigz(tar_dir=None, output_file="model.tar.gz", num_processes=None):
    if num_processes is None:
        num_processes = os.cpu_count()  # Use all available CPU cores
    
    parent_dir = os.getcwd()
    os.chdir(tar_dir)
    
    # Get total size for progress bar
    total_size = sum(os.path.getsize(f) for f in os.listdir('.') if os.path.isfile(f))
    
    # Prepare the pigz command
    pigz_cmd = f"tar cf - . | pigz -p {num_processes} > {os.path.join(parent_dir, output_file)}"
    
    # Create a process for the pigz command
    process = subprocess.Popen(pigz_cmd, shell=True, stderr=subprocess.PIPE)
    
    # Initialize progress bar
    pbar = tqdm(total=total_size, unit='B', unit_scale=True, desc="Compressing")
    
    # Update progress bar
    while True:
        output = process.stderr.readline()
        if process.poll() is not None:
            break
        if output:
            # pigz outputs progress to stderr, parse it to update the progress bar
            try:
                progress = int(output.decode().split()[1])
                pbar.n = progress
                pbar.refresh()
            except (ValueError, IndexError):
                pass
    
    pbar.close()
    os.chdir(parent_dir)
    
    if process.returncode != 0:
        raise subprocess.CalledProcessError(process.returncode, pigz_cmd)
