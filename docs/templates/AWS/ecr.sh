#!/bin/bash
    
# Ensure region is (temporarily) set to prevent errors
export AWS_DEFAULT_REGION="eu-west-1"

# Change permissions of files. Otherwise upstream lambda will give permission error
chmod 644 $(find . -type f)
chmod 755 $(find . -type d)

# Build image
docker build -t {{ docker_image }} .

# Log into AWS and ECR
aws ecr get-login-password --region {{ region }} | docker login --username AWS --password-stdin {{ ECR_endpoint }}

# Create test repo, gives warning but continues of it already exists
aws ecr create-repository --repository-name {{ docker_image }} --image-scanning-configuration scanOnPush=true --image-tag-mutability MUTABLE || true

# Tag image and push to ECR
docker tag {{ docker_image }}:latest {{ ECR_endpoint }}/{{ docker_image }}:latest
docker push {{ ECR_endpoint }}/{{ docker_image }}:latest