from azure.identity import ClientSecretCredential  # pip install azure-identity for azure 5.0 sdk
from azure.mgmt.storage import StorageManagementClient  # pip install azure-mgmt-storage for azure 5.0 sdk
import os


def get_environment():
    try:
        AZURE_TENANT_ID = os.environ["AZURE_TENANT_ID"]
        AZURE_CLIENT_ID = os.environ["AZURE_CLIENT_ID"]
        AZURE_CLIENT_SECRET = os.environ["AZURE_CLIENT_SECRET"]
        AZURE_SUBSCRIPTION_ID = os.environ["AZURE_SUBSCRIPTION_ID"]
        AZURE_RESOURCE_GROUP_NAME = os.environ["AZURE_RESOURCE_GROUP_NAME"]
        AZURE_STORAGE_ACCOUNT_NAME = os.environ["AZURE_STORAGE_ACCOUNT_NAME"]
    except Exception as e:
        raise(e)
    else:
        return {
            "AZURE_TENANT_ID": AZURE_TENANT_ID,
            "AZURE_CLIENT_ID": AZURE_CLIENT_ID,
            "AZURE_CLIENT_SECRET": AZURE_CLIENT_SECRET,
            "AZURE_SUBSCRIPTION_ID": AZURE_SUBSCRIPTION_ID,
            "AZURE_RESOURCE_GROUP_NAME": AZURE_RESOURCE_GROUP_NAME,
            "AZURE_STORAGE_ACCOUNT_NAME": AZURE_STORAGE_ACCOUNT_NAME,
        }


def _get_storage_key(
        AZURE_TENANT_ID,
        AZURE_CLIENT_ID,
        AZURE_CLIENT_SECRET,
        AZURE_SUBSCRIPTION_ID,
        AZURE_RESOURCE_GROUP_NAME,
        AZURE_STORAGE_ACCOUNT_NAME,
):
    credentials = ClientSecretCredential(
        client_id=AZURE_CLIENT_ID,
        client_secret=AZURE_CLIENT_SECRET,
        tenant_id=AZURE_TENANT_ID,
    )
    storage_client = StorageManagementClient(
        credentials,
        AZURE_SUBSCRIPTION_ID,
    )
    storage_keys = storage_client.storage_accounts.list_keys(
        AZURE_RESOURCE_GROUP_NAME,
        AZURE_STORAGE_ACCOUNT_NAME,
    )
    storage_keys = {key.key_name: key.value for key in storage_keys.keys}
    return storage_keys['key1']


def get_connection_string():
    environment = get_environment()
    storage_key = _get_storage_key(**environment)
    azure_storage_account_name = environment["AZURE_STORAGE_ACCOUNT_NAME"]
    return (
        f'DefaultEndpointsProtocol=https;'
        f'EndpointSuffix=core.windows.net;'
        f'AccountName={azure_storage_account_name};'
        f'AccountKey={storage_key}'
    )
