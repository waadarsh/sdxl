
# Custom Docker Setup for AWS SageMaker with diffusers, transformers, and Additional Libraries

This guide walks through creating a custom Docker environment on AWS SageMaker that includes `diffusers >= 0.30.0`, `transformers >= 4.44.0`, `peft`, `torch`, `huggingface_hub`, and `sagemaker`, along with additional libraries like `accelerate`, `bitsandbytes`, and `deepspeed` for optimized training.

## 1. Dockerfile Setup

Below is the Dockerfile that installs the required dependencies:

```Dockerfile
# Use an official Nvidia CUDA image with PyTorch as the base
FROM nvidia/cuda:11.7.1-cudnn8-devel-ubuntu20.04

# Install essential dependencies and Python 3.8
RUN apt-get update && apt-get install -y \
    python3-pip \
    git \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Set Python 3 as the default version
RUN ln -sf /usr/bin/python3 /usr/bin/python

# Upgrade pip to the latest version
RUN pip install --upgrade pip

# Install PyTorch, transformers, diffusers, and required libraries
RUN pip install torch torchvision transformers>=4.44.0 diffusers>=0.30.0 \
    peft huggingface_hub sagemaker

# Install additional libraries: accelerate and bitsandbytes for efficient training
RUN pip install accelerate bitsandbytes

# (Optional) Install deepspeed for more efficient large model training
RUN pip install deepspeed

# (Optional) Install xformers for memory-efficient attention in transformers
RUN pip install xformers

# Set the working directory
WORKDIR /opt/ml/code

# Copy the training script to the container (train_dreambooth_lora_sdxl.py in this case)
COPY train_dreambooth_lora_sdxl.py /opt/ml/code/train_dreambooth_lora_sdxl.py

# Define the entry point for the training script
ENTRYPOINT ["python", "/opt/ml/code/train_dreambooth_lora_sdxl.py"]
```

## 2. Build and Push the Docker Image to Amazon ECR

Once the Dockerfile is ready, follow these steps to build and push the image to **Amazon ECR**:

### Step 1: Authenticate Docker with AWS ECR

```bash
aws ecr get-login-password --region <region> | docker login --username AWS --password-stdin <aws_account_id>.dkr.ecr.<region>.amazonaws.com
```

### Step 2: Create an ECR Repository

```bash
aws ecr create-repository --repository-name custom-sagemaker-diffusion
```

### Step 3: Build the Docker Image

```bash
docker build -t custom-sagemaker-diffusion .
```

### Step 4: Tag the Docker Image

```bash
docker tag custom-sagemaker-diffusion:latest <aws_account_id>.dkr.ecr.<region>.amazonaws.com/custom-sagemaker-diffusion:latest
```

### Step 5: Push the Docker Image to ECR

```bash
docker push <aws_account_id>.dkr.ecr.<region>.amazonaws.com/custom-sagemaker-diffusion:latest
```

## 3. Configure the SageMaker Training Job

Once the Docker image is pushed to ECR, configure the **SageMaker estimator** in your Python script:

```python
import sagemaker
from sagemaker.pytorch import PyTorch

# Define SageMaker role and instance details
role = 'your-sagemaker-role'
image_uri = '<aws_account_id>.dkr.ecr.<region>.amazonaws.com/custom-sagemaker-diffusion:latest'

# Define the hyperparameters for the training job
hyperparameters = {
    'pretrained_model_name_or_path': 'stabilityai/stable-diffusion-xl-base-1.0',
    'instance_data_dir': 's3://your-s3-bucket/your-dataset-dir',
    'pretrained_vae_model_name_or_path': 'madebyollin/sdxl-vae-fp16-fix',
    'output_dir': 's3://your-s3-bucket/your-output-dir',
    'mixed_precision': 'fp16',
    'instance_prompt': 'your-prompt',
    'resolution': 1024,
    'train_batch_size': 2,
    'gradient_accumulation_steps': 2,
    'gradient_checkpointing': True,
    'learning_rate': 1e-4,
    'lr_scheduler': 'constant',
    'lr_warmup_steps': 0,
    'max_train_steps': 500,
    'seed': 0
}

# Create a SageMaker PyTorch estimator
estimator = PyTorch(
    entry_point='train_dreambooth_lora_sdxl.py',
    role=role,
    image_uri=image_uri,
    instance_count=1,
    instance_type='ml.p3.2xlarge',
    hyperparameters=hyperparameters,
    volume_size=100,  # Disk space for the instance in GB
    output_path='s3://your-s3-bucket/output'
)

# Launch the training job
estimator.fit({'train': 's3://your-s3-bucket/your-dataset-dir'})
```

## 4. Monitor the Training Job

Use the **SageMaker Console** to monitor the job and check **CloudWatch** for logs and status updates.

## 5. Key Considerations

- **Instance Types**: Use powerful GPU instances like `ml.p3.2xlarge` or `ml.p4d.24xlarge` depending on the complexity of the model.
- **S3 Paths**: Ensure all data paths (datasets, output) are correctly set up in your S3 bucket.
- **Libraries**: `accelerate` and `bitsandbytes` are essential for efficient distributed training and memory management.

---

By following this guide, you will set up a powerful custom Docker environment that allows you to train or fine-tune models like Stable Diffusion XL using DreamBooth or LoRA efficiently on AWS SageMaker.
