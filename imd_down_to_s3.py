import os
import requests
import boto3
import sagemaker
from sagemaker.s3 import S3Uploader

def download_image(url, local_filename):
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192): 
                f.write(chunk)
    return local_filename

def upload_to_s3(local_file, s3_uri):
    try:
        S3Uploader.upload(local_file, s3_uri)
        print(f"Upload Successful: {s3_uri}")
        return True
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return False

def main():
    # Set up SageMaker session
    boto_session = boto3.setup_default_session()
    sess = sagemaker.Session(boto_session=boto_session)
    desired_s3_uri = f"s3://{sess.default_bucket()}/collection"

    # Replace with your GitHub repository details
    github_repo = "marshmellow77/dreambooth-sm"
    branch = "main"
    image_folder = "training-images"

    # Get list of images from GitHub
    api_url = f"https://api.github.com/repos/{github_repo}/contents/{image_folder}?ref={branch}"
    response = requests.get(api_url)
    files = response.json()

    for file in files:
        if file['type'] == 'file':
            file_name = file['name']
            download_url = file['download_url']
            
            # Download the image
            local_file = download_image(download_url, file_name)
            
            # Upload to S3
            s3_uri = os.path.join(desired_s3_uri, file_name)
            upload_to_s3(local_file, s3_uri)
            
            # Clean up local file
            os.remove(local_file)

if __name__ == "__main__":
    main()
