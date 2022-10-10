#!/bin/bash

# Set environment variables
#TODO: refactor --> take env vars out, implemennt proper templating and injection of values (except for az login creds)
DOCKER_IMAGE_NAME={{ cfg["docker_image_name"] }}
AZURE_CONTAINER_REGISTRY_NAME={{ cfg["container_registry_name"] }}
AZURE_RESOURCE_GROUP_NAME={{ cfg["resource_group_name"] }}

# Login to Azure
az login --service-principal -u $AZURE_CLIENT_ID -p $AZURE_CLIENT_SECRET --tenant $AZURE_TENANT_ID

# Create a registry on ACR
az acr create --resource-group $AZURE_RESOURCE_GROUP_NAME --name $AZURE_CONTAINER_REGISTRY_NAME --sku Basic --admin-enabled true

# Login to Azure Container Registry
az acr login --name $AZURE_CONTAINER_REGISTRY_NAME

# Build Docker image locally
docker build -t $DOCKER_IMAGE_NAME .

# Tag Docker image and create alias
docker tag $DOCKER_IMAGE_NAME:latest $AZURE_CONTAINER_REGISTRY_NAME.azurecr.io/$DOCKER_IMAGE_NAME:latest

# Push Docker image to Azure Container Registry
docker push $AZURE_CONTAINER_REGISTRY_NAME.azurecr.io/$DOCKER_IMAGE_NAME:latest