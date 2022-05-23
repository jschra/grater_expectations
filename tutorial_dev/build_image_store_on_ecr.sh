#!/bin/bash
    
# Ensure region is (temporarily) set to prevent errors
export AWS_DEFAULT_REGION="eu-west-1"

# Change permissions of files. Otherwise upstream lambda will give permission error
chmod 644 $(find . -type f)
chmod 755 $(find . -type d)

# Temporarily copy requirements.txt for usage w/ Dockerfile
cp ../requirements.txt ./requirements.txt

# Build image
docker build -t tutorial_image .

# Remove requirements.txt
rm -rf requirements.txt

# Log into AWS and ECR
aws ecr get-login-password --region eu-west-1 | docker login --username AWS --password-stdin 541219063706.dkr.ecr.eu-west-1.amazonaws.com

# Create test repo, gives warning but continues of it already exists
aws ecr create-repository --repository-name tutorial_image --image-scanning-configuration scanOnPush=true --image-tag-mutability MUTABLE || true

# Tag image and push to ECR
docker tag tutorial_image:latest 541219063706.dkr.ecr.eu-west-1.amazonaws.com/tutorial_image:latest
docker push 541219063706.dkr.ecr.eu-west-1.amazonaws.com/tutorial_image:latest