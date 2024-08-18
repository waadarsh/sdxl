# Complete Updated Guide: LoRA Fine-tuning on Amazon SageMaker with Python 3.10

This comprehensive guide will walk you through setting up and running a LoRA (Low-Rank Adaptation) fine-tuning job for Stable Diffusion XL on Amazon SageMaker using Python 3.10.

## Prerequisites

1. An AWS account with access to SageMaker, ECR, and S3
2. AWS CLI installed and configured
3. Docker installed on your local machine
4. Python 3.10 installed locally (for development and testing)

## Step 1: Prepare Your Local Environment

1. Create a new directory for your project:
   ```bash
   mkdir sdxl-lora-sagemaker && cd sdxl-lora-sagemaker
   ```

2. Create a virtual environment with Python 3.10 and activate it:
   ```bash
   python3.10 -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install required Python packages:
   ```bash
   pip install boto3 sagemaker
   ```

## Step 2: Prepare Your Training Scripts

1. Create `train_lora.sh`:
   ```bash
   #!/bin/bash

   # SageMaker passes hyperparameters as environment variables
   INSTANCE_DATA_DIR=${SM_CHANNEL_TRAINING}
   OUTPUT_DIR=${SM_MODEL_DIR}
   INSTANCE_PROMPT=${SM_HP_INSTANCE_PROMPT}

   # Print Python version for debugging
   python --version

   accelerate launch --config_file /opt/ml/code/accelerate_config.yaml /opt/ml/code/train_dreambooth_lora_sdxl.py \
     --pretrained_model_name_or_path='stabilityai/stable-diffusion-xl-base-1.0' \
     --instance_data_dir="${INSTANCE_DATA_DIR}" \
     --pretrained_vae_model_name_or_path="madebyollin/sdxl-vae-fp16-fix" \
     --output_dir="${OUTPUT_DIR}" \
     --mixed_precision="fp16" \
     --instance_prompt="${INSTANCE_PROMPT}" \
     --resolution=1024 \
     --train_batch_size=2 \
     --gradient_accumulation_steps=2 \
     --gradient_checkpointing \
     --learning_rate=1e-4 \
     --lr_scheduler="constant" \
     --lr_warmup_steps=0 \
     --max_train_steps=500 \
     --seed="0"
   ```

2. Create `accelerate_config.yaml`:
   ```yaml
   compute_environment: LOCAL_MACHINE
   distributed_type: 'NO'
   downcast_bf16: 'no'
   machine_rank: 0
   main_training_function: main
   mixed_precision: fp16
   num_machines: 1
   num_processes: 1
   use_cpu: false
   ```

3. Create `train_dreambooth_lora_sdxl.py` with your LoRA fine-tuning logic. Here's a basic structure:
   ```python
   import argparse
   from diffusers import StableDiffusionXLPipeline, DPMSolverMultistepScheduler
   
   def parse_args():
       parser = argparse.ArgumentParser()
       parser.add_argument("--pretrained_model_name_or_path", type=str, required=True)
       # Add other arguments as needed
       return parser.parse_args()

   def main():
       args = parse_args()
       # Your LoRA fine-tuning logic here
       # Use args to access command-line parameters

   if __name__ == "__main__":
       main()
   ```

## Step 3: Create and Push the Docker Image

1. Create a `Dockerfile`:
   ```dockerfile
   FROM pytorch/pytorch:2.0.1-cuda11.7-cudnn8-runtime

   # Install Python 3.10
   RUN apt-get update && apt-get install -y \
       python3.10 \
       python3.10-distutils \
       python3.10-dev \
       python3-pip \
       git \
       wget \
       && rm -rf /var/lib/apt/lists/*

   # Set Python 3.10 as the default python version
   RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.10 1
   RUN update-alternatives --set python /usr/bin/python3.10

   # Upgrade pip
   RUN python -m pip install --upgrade pip

   # Install Python packages
   RUN pip install --no-cache-dir \
       accelerate \
       transformers \
       diffusers \
       peft \
       bitsandbytes \
       xformers \
       scipy \
       safetensors \
       boto3 \
       sagemaker \
       huggingface \
       sagemaker-huggingface-inference-toolkit \
       huggingface-hub \
       sagemaker-training

   # Set up code directory
   WORKDIR /opt/ml/code

   # Copy your training script and accelerate config
   COPY train_dreambooth_lora_sdxl.py .
   COPY accelerate_config.yaml .
   COPY train_lora.sh .

   # Make sure the shell script is executable
   RUN chmod +x train_lora.sh

   # Set the entrypoint
   ENTRYPOINT ["train_lora.sh"]
   ```

2. Build and push the Docker image:
   ```bash
   # Build the Docker image
   docker build -t sdxl-lora-sagemaker-py310 .

   # Log in to Amazon ECR
   aws ecr get-login-password --region your-region | docker login --username AWS --password-stdin your-account-id.dkr.ecr.your-region.amazonaws.com

   # Create a repository in ECR (if not already created)
   aws ecr create-repository --repository-name sdxl-lora-sagemaker-py310 --region your-region

   # Tag your Docker image
   docker tag sdxl-lora-sagemaker-py310:latest your-account-id.dkr.ecr.your-region.amazonaws.com/sdxl-lora-sagemaker-py310:latest

   # Push the image to ECR
   docker push your-account-id.dkr.ecr.your-region.amazonaws.com/sdxl-lora-sagemaker-py310:latest
   ```

## Step 4: Prepare Your Training Data

1. Organize your training images in a local directory.

2. Upload your training images to an S3 bucket:
   ```bash
   aws s3 cp --recursive ./your-local-image-directory s3://your-training-data-bucket/your-collection-path
   ```

## Step 5: Set Up the SageMaker Training Job

Create `launch_sagemaker_job.py`:

```python
import boto3
import sagemaker
from sagemaker.estimator import Estimator
from sagemaker.inputs import TrainingInput

# Set up AWS clients
sagemaker_client = boto3.client('sagemaker')
s3_client = boto3.client('s3')

# Set up a SageMaker session
sagemaker_session = sagemaker.Session(
    boto_session=boto3.Session(region_name='your-region'),
    sagemaker_client=sagemaker_client,
    s3_client=s3_client
)

# Define the Estimator
estimator = Estimator(
    image_uri='your-account-id.dkr.ecr.your-region.amazonaws.com/sdxl-lora-sagemaker-py310:latest',
    role='arn:aws:iam::your-account-id:role/SageMakerRole',
    instance_count=1,
    instance_type='ml.g4dn.xlarge',
    output_path='s3://your-output-bucket/output',
    sagemaker_session=sagemaker_session,
    entry_point='train_lora.sh',
    source_dir='.',
    hyperparameters={
        'instance_prompt': 'your keyword here'
    }
)

# Set up the data input
training_input = TrainingInput(
    s3_data='s3://your-training-data-bucket/your-collection-path',
    content_type='application/x-image'
)

# Start the training job
estimator.fit({'training': training_input})
```

## Step 6: Run the SageMaker Training Job

1. Run the Python script to start the SageMaker training job:
   ```bash
   python launch_sagemaker_job.py
   ```

2. Monitor the job progress in the AWS SageMaker console or using the AWS CLI:
   ```bash
   aws sagemaker describe-training-job --training-job-name your-job-name
   ```

## Step 7: Retrieve and Use Your Fine-tuned Model

1. Once the job is complete, find your model artifacts in the S3 output location you specified.

2. Download the model artifacts:
   ```bash
   aws s3 cp --recursive s3://your-output-bucket/output/your-job-name/output /path/to/local/model
   ```

3. You can now use this fine-tuned model for inference or further training.

## Important Notes

1. Replace all placeholder values (like 'your-region', 'your-account-id', etc.) with your actual AWS account details and desired configurations.

2. Ensure your IAM role has the necessary permissions:
   - AmazonSageMakerFullAccess
   - AmazonS3FullAccess
   - AmazonEC2ContainerRegistryFullAccess

3. The Docker image build process might take some time, especially if you're running it for the first time, as it needs to download all the dependencies.

4. Make sure your `train_dreambooth_lora_sdxl.py` script is compatible with Python 3.10. You may need to update some syntax or library usage if you're using features that have changed between Python versions.

5. The SageMaker training job duration will depend on the size of your dataset and the number of training steps. Monitor the job in the SageMaker console to track its progress.

6. Always be mindful of the costs associated with running GPU instances on SageMaker. Make sure to stop or terminate resources when they're not in use.

## Troubleshooting

- If you encounter permission issues, double-check your IAM role permissions.
- For Docker-related issues, ensure your Docker daemon is running and you have sufficient permissions.
- If the training job fails, check the CloudWatch logs for detailed error messages.
- If you encounter Python version-related issues, check the CloudWatch logs for the output of `python --version` at the start of the training script.
- If certain libraries are incompatible with Python 3.10, you may need to downgrade them or find alternative libraries. Always check the compatibility of your dependencies.

Remember to clean up your resources (EC2 instances, S3 buckets, ECR repositories) when you're done to avoid unnecessary charges.
