#!/bin/bash

# Login to Azure
# -- Note that environment variables containing service principal credentials are required
# -- to log in. Ensure these are set in the calling terminal before running this script
az login --service-principal -u $ARM_CLIENT_ID -p $ARM_CLIENT_SECRET --tenant $ARM_TENANT_ID

# Create a registry on ACR
az acr create --resource-group {{cfg["resource_group_name"]}} --name {{cfg["container_registry_name"]}} --sku Basic --admin-enabled true

# Login to Azure Container Registry
az acr login --name {{cfg["container_registry_name"]}}

# Build Docker image locally, pass Service Principal credentials
docker build -t {{cfg["docker_image_name"]}} \
--build-arg AZURE_CLIENT_SECRET=${ARM_CLIENT_SECRET} \
--build-arg AZURE_CLIENT_ID=${ARM_CLIENT_ID} \
--build-arg AZURE_SUBSCRIPTION_ID=${ARM_SUBSCRIPTION_ID} \
--build-arg AZURE_TENANT_ID=${ARM_TENANT_ID} \
.

# Tag Docker image and create alias
docker tag {{cfg["docker_image_name"]}}:latest {{cfg["container_registry_name"]}}.azurecr.io/{{cfg["docker_image_name"]}}:latest

# Push Docker image to Azure Container Registry
docker push {{cfg["container_registry_name"]}}.azurecr.io/{{cfg["docker_image_name"]}}:latest