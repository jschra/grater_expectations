# -- Base image
FROM mcr.microsoft.com/azure-functions/python:4-python3.8

# -- Catch arguments passed at buildtime to pass through as environment variables
#    TODO:
#    This is a workaround to ensure the Docker container can authenticate against
#    Azure in the cloud. Should be replaced by an RBAC implementation
ARG AZURE_CLIENT_ID
ARG AZURE_CLIENT_SECRET
ARG AZURE_SUBSCRIPTION_ID
ARG AZURE_TENANT_ID

# -- Set environment varialbes
ENV AzureWebJobsScriptRoot=/home/site/wwwroot \
    AzureFunctionsJobHost__Logging__Console__IsEnabled=true
ENV AZURE_CLIENT_ID $AZURE_CLIENT_ID
ENV AZURE_CLIENT_SECRET $AZURE_CLIENT_SECRET
ENV AZURE_SUBSCRIPTION_ID $AZURE_SUBSCRIPTION_ID
ENV AZURE_TENANT_ID $AZURE_TENANT_ID

# -- Copy files
COPY requirements.txt /
COPY function /home/site/wwwroot
COPY supporting_functions.py /home/site/wwwroot/supporting_functions.py
COPY project_config.yml /home/site/wwwroot/grater-expectations/project_config.yml
COPY great_expectations /home/site/wwwroot/great_expectations

# -- Install requirements
RUN pip install -r /requirements.txt