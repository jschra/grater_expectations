#!/bin/bash

# Set environment variables
DOCKER_IMAGE={{ cfg["docker_image_name"] }}
AZURE_CONTAINER_REGISTRY_NAME={{ cfg["container_registry_name"] }}
AZURE_CLIENT_ID={{ cnx["AZURE_CLIENT_ID"] }}
AZURE_CLIENT_SECRET={{ cnx["AZURE_CLIENT_SECRET"] }}
AZURE_TENANT_ID={{ cnx["AZURE_CLIENT_SECRET"] }}

# Login to Azure
az login --service-principal -u $AZURE_CLIENT_ID -p $AZURE_CLIENT_SECRET --tenant $AZURE_TENANT_ID

# Login to Azure Container Registry
az acr login --name $AZURE_CONTAINER_REGISTRY_NAME

# Build Docker image
docker build -t $DOCKER_IMAGE .

# Tag Docker image to create alias
docker tag $DOCKER_IMAGE:latest $AZURE_CONTAINER_REGISTRY_NAME.azurecr.io/$AZURE_CONTAINER_REGISTRY_NAME:latest

# Push Docker image to Azure registry
docker push $AZURE_CONTAINER_REGISTRY_NAME.azurecr.io/$AZURE_CONTAINER_REGISTRY_NAME:latest