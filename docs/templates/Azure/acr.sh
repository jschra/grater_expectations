#!/bin/bash

# Set environment variables
DOCKER_IMAGE_NAME={{ cfg["docker_image_name"] }}
AZURE_CONTAINER_REGISTRY_NAME={{ cfg["container_registry_name"] }}
AZURE_CLIENT_ID={{ cnx["AZURE_CLIENT_ID"] }}
AZURE_CLIENT_SECRET={{ cnx["AZURE_CLIENT_SECRET"] }}
AZURE_TENANT_ID={{ cnx["AZURE_TENANT_ID"] }}
AZURE_RESOURCE_GROUP_NAME={{ cfg["resource_group_name"] }}

# Login to Azure
az login --service-principal -u $AZURE_CLIENT_ID -p $AZURE_CLIENT_SECRET --tenant $AZURE_TENANT_ID

# Login to Azure Container Registry
az acr login --name $AZURE_CONTAINER_REGISTRY_NAME

# Build Docker image locally
docker build -t $DOCKER_IMAGE_NAME .

# Tag Docker image and create alias
docker tag $DOCKER_IMAGE_NAME:latest $AZURE_CONTAINER_REGISTRY_NAME.azurecr.io/$DOCKER_IMAGE_NAME:latest

# Push Docker image to Azure Container Registry
docker push $AZURE_CONTAINER_REGISTRY_NAME.azurecr.io/$DOCKER_IMAGE_NAME:latest

# TODO: Authenticate
# Create Docker container on Azure
az container create --resource-group $AZURE_RESOURCE_GROUP_NAME --name $DOCKER_CONTAINER_NAME --image $AZURE_CONTAINER_REGISTRY_NAME.azurecr.io/$DOCKER_IMAGE_NAME

# Start Docker container on Azure
az container start --resource-group $AZURE_RESOURCE_GROUP_NAME --name $DOCKER_CONTAINER_NAME --no-wait