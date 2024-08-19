# import boto3

# def ensure_folder_exists(s3_client, bucket_name, folder_name):
#     folder_key = f"{folder_name}/"
#     s3_client.put_object(Bucket=bucket_name, Key=folder_key)
#     print(f"Folder '{folder_name}' created or already exists in bucket '{bucket_name}'")

# def upload_file_to_s3(file_path, bucket_name, folder_name):
#     s3_client = boto3.client('s3')
    
#     # Ensure the folder exists
#     ensure_folder_exists(s3_client, bucket_name, folder_name)
    
#     # Prepare the object name (key) for the file
#     file_name = file_path.split('/')[-1]  # Extract file name from path
#     object_name = f"{folder_name}/{file_name}"
    
#     try:
#         with open(file_path, 'rb') as file:
#             s3_client.upload_fileobj(file, bucket_name, object_name)
#         print(f"File uploaded successfully to {bucket_name}/{object_name}")
#     except Exception as e:
#         print(f"Error uploading file: {str(e)}")

# # Example usage
# bucket_name = 'your-bucket-name'
# folder_name = 'test'
# file_path = 'test.[y'

# upload_file_to_s3(file_path, bucket_name, folder_name)




import boto3
from botocore.exceptions import ClientError

def create_bucket_if_not_exists(s3_client, bucket_name, region='us-east-1'):
    try:
        s3_client.head_bucket(Bucket=bucket_name)
        print(f"Bucket '{bucket_name}' already exists.")
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == '404':
            try:
                if region == 'us-east-1':
                    s3_client.create_bucket(Bucket=bucket_name)
                else:
                    s3_client.create_bucket(
                        Bucket=bucket_name,
                        CreateBucketConfiguration={'LocationConstraint': region}
                    )
                print(f"Bucket '{bucket_name}' created successfully.")
            except ClientError as e:
                print(f"Error creating bucket: {e}")
                return False
        else:
            print(f"Error checking bucket: {e}")
            return False
    return True

def ensure_folder_exists(s3_client, bucket_name, folder_name):
    folder_key = f"{folder_name}/"
    s3_client.put_object(Bucket=bucket_name, Key=folder_key)
    print(f"Folder '{folder_name}' created or already exists in bucket '{bucket_name}'")

def upload_file_to_s3(file_path, bucket_name, folder_name, region='us-east-1'):
    s3_client = boto3.client('s3', region_name=region)
    
    # Create bucket if it doesn't exist
    if not create_bucket_if_not_exists(s3_client, bucket_name, region):
        return
    
    # Ensure the folder exists
    ensure_folder_exists(s3_client, bucket_name, folder_name)
    
    # Prepare the object name (key) for the file
    file_name = file_path.split('/')[-1]  # Extract file name from path
    object_name = f"{folder_name}/{file_name}"
    
    try:
        with open(file_path, 'rb') as file:
            s3_client.upload_fileobj(file, bucket_name, object_name)
        print(f"File uploaded successfully to {bucket_name}/{object_name}")
    except Exception as e:
        print(f"Error uploading file: {str(e)}")

# Example usage
bucket_name = 'your-unique-bucket-name'
folder_name = 'test'
file_path = 'test.[y'
region = 'us-east-1'  # Change this to your preferred region

upload_file_to_s3(file_path, bucket_name, folder_name, region)
