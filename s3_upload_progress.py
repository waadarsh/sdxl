from tqdm import tqdm
import os
from sagemaker.s3 import S3Uploader

class ProgressPercentage:
    def __init__(self, filename):
        self._filename = filename
        self._size = float(os.path.getsize(filename))
        self._seen_so_far = 0
        self._pbar = tqdm(total=self._size, unit='B', unit_scale=True, desc=f"Uploading {filename}")

    def __call__(self, bytes_amount):
        self._seen_so_far += bytes_amount
        self._pbar.update(bytes_amount)

    def __del__(self):
        self._pbar.close()

def upload_with_progress(local_path, desired_s3_uri):
    callback = ProgressPercentage(local_path)
    s3_model_uri = S3Uploader.upload(
        local_path=local_path,
        desired_s3_uri=desired_s3_uri,
        kms_key=None,
        sagemaker_session=None,
        transfer_config=None,
        callback=callback
    )
    return s3_model_uri

# Usage
local_path = "model.tar.gz"
desired_s3_uri = f"s3://{sess.default_bucket()}/sdxl-model"

s3_model_uri = upload_with_progress(local_path, desired_s3_uri)
print(f"Model uploaded to: {s3_model_uri}")
