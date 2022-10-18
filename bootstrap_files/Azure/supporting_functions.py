# Imports
import logging
from ruamel import yaml
import os
import sys
import great_expectations as ge
from IPython.display import display, HTML
from ruamel.yaml import YAML
from azure.mgmt.storage import StorageManagementClient
from azure.storage.blob import BlobServiceClient
from io import StringIO
import pandas as pd


# Logger initialization and function for lambda
logger = logging.getLogger(__name__)


def setup_logging():
    logger = logging.getLogger()
    for default_handler in logger.handlers:
        logger.removeHandler(default_handler)

    handler = logging.StreamHandler(sys.stdout)

    DATEFMT = "%Y-%m-%d %H:%M:%S"
    FORMAT = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    handler.setFormatter(logging.Formatter(FORMAT, DATEFMT))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    return logger


# Classes
class TestingConfiguration:
    def __init__(self, path_config: str):
        logger.info("Initializing testing config")
        self.path_config = path_config

    def load_config(self):
        logger.info(f"Loading testing config from {self.path_config}")
        with open(self.path_config, "r") as f:
            cfg = yaml.safe_load(f)

        self.config = cfg
        for key, value in cfg.items():
            setattr(self, key, value)


# Azure credentials helper
def copy_tf_env_vars_for_az():
    """Helper function that takes environment variables for a service principal as
    needed by Terraform and sets their equivalents for the Azure CLI and Python SDK. For
    example, it takes the value set for ARM_CLIENT_ID (needed by Terraform) and sets a
    copy of it as AZURE_CLIENT_ID (needed by Azure CLI and SDK)
    """
    # -- 1. Set env var mapping dict
    DICT_TF_VAR_MAPPING = {
        "ARM_CLIENT_ID": "AZURE_CLIENT_ID",
        "ARM_CLIENT_SECRET": "AZURE_CLIENT_SECRET",
        "ARM_SUBSCRIPTION_ID": "AZURE_SUBSCRIPTION_ID",
        "ARM_TENANT_ID": "AZURE_TENANT_ID",
    }

    # -- 2. Copy environment variables
    for arm_var, azure_var in DICT_TF_VAR_MAPPING.items():
        try:
            os.environ[azure_var] = os.environ.get(arm_var)
        except Exception as error:
            message = (
                f"Something went wrong while trying to retrieve {arm_var} from the "
                "environment variables in your current terminal session. Please ensure "
                f"these are set before calling this program. Error output: {error}"
            )
            logging.error(message)
            raise error


# Functions for interacting with containers and blobs
def get_file_keys_from_container(
    blob_service_client: BlobServiceClient, container_name: str
) -> list:
    """Function to get a list of all blobs in a container, given an instantiated
    BlobServiceClient for the storage account to target and a name of a container
    within it

    Parameters
    ----------
    blob_service_client : BlobServiceClient
        BlobServiceClient for the storage account to target. Must be authenticated and
        allowed to access and interact with containers
    container_name : str
        Name of the container to get a list of blobs from

    Returns
    -------
    list
        List of blobs residing in the container provided at runtime
    """
    # -- Initiate client, pull blobs and return blob paths
    container_client = blob_service_client.get_container_client(container_name)
    list_blobs = [blob.name for blob in container_client.list_blobs()]

    return list_blobs


def load_csv_from_container(
    blob_service_client: BlobServiceClient, container_name: str, path_csv: str
) -> pd.DataFrame:
    """Function that downloads a CSV from a container in an Azure storage account and
    returns it as a pandas DataFrame

    Parameters
    ----------
    blob_service_client : BlobServiceClient
        BlobServiceClient for the storage account to target. Must be authenticated and
        allowed to access and interact with containers
    container_name : str
        Name of the container to get a list of blobs from
    path_csv : str
        Path to the CSV file in the container (can be obtained by calling 
        get_file_keys_from_container)

    Returns
    -------
    pd.DataFrame
        The downloaded CSV file as a pandas DataFrame in memory
    """

    # -- 1. Initiate blob client and download blob
    blob_client = blob_service_client.get_blob_client(
        container=container_name, blob=path_csv
    )
    downloaded_blob = blob_client.download_blob()

    # -- 2. Read incoming stream as pandas DataFrame
    df = pd.read_csv(StringIO(downloaded_blob.content_as_text()))

    return df


# Helper functions for Great Expectations config for Azure
def get_connection_string(
    storage_client: StorageManagementClient, test_config: TestingConfiguration
) -> str:
    """Helper function to generate a connection string for a storage account

    Parameters
    ----------
    storage_client : StorageManagementClient
        An initialized storage account client for the current Azure account
    test_config : TestingConfiguration
        The testing configurations for the current Grater Expectations config, generally
        retrieved by initiating TestingConfiguration with project_config.yml

    Returns
    -------
    str
        A connection string for the storage account that is being targeted
    """
    # -- 1. Get keys for storage account
    response = storage_client.storage_accounts.list_keys(
        test_config.resource_group_name, test_config.storage_account
    )

    storage_keys = {key.key_name: key.value for key in response.keys}

    # -- 2. Pull first key and generate connection string
    storage_key = storage_keys["key1"]
    connection_string = (
        f"DefaultEndpointsProtocol=https;"
        f"EndpointSuffix=core.windows.net;"
        f"AccountName={test_config.storage_account};"
        f"AccountKey={storage_key}"
    )

    return connection_string


def add_connection_string_to_config(
    connection_string: str,
    test_config: TestingConfiguration,
    path_config: str = "./great_expectations/great_expectations.yml",
):
    """Helper function to add a storage account connection string to the storage account
    configurations in the Great Expectations configuration file

    Parameters
    ----------
    connection_string : str
        A connection string for the storage account being targeted. Can be generated by
        running get_connection_string
    test_config : TestingConfiguration
        The testing configurations for the current Grater Expectations config, generally
        retrieved by initiating TestingConfiguration with project_config.yml
    path_config : str, optional
        Path to configuration file of Great Expectations, by default 
        "./great_expectations/great_expectations.yml"
    """

    STORES_TO_ADJUST = [
        "expectations_store",
        "validations_store",
        "checkpoint_store",
        "profiler_store",
        "evaluation_parameter_store",
    ]

    # -- 1. Initialize yaml and open file
    local_yaml = YAML()
    with open(path_config, "r") as file_in:
        data = local_yaml.load(file_in)

    # -- 2. Add connection strings to stores
    for store in STORES_TO_ADJUST:
        data["stores"][store]["store_backend"]["connection_string"] = connection_string

    # -- 3. Add connection string to Data Docs
    data["data_docs_sites"][test_config.site_name]["store_backend"][
        "connection_string"
    ] = connection_string

    # -- 4. Write back to config
    with open(path_config, "w") as file_out:
        local_yaml.dump(data, file_out)


# Additional functions for Great Expectations
def evaluate_ge_results(
    ge_results: ge.checkpoint.types.checkpoint_result.CheckpointResult,
):
    # Pull information from GE results
    logger.info("Evaluating expectation results from Great Expectations")
    success_statistics = ge_results.get_statistics()
    failed_validations = success_statistics["unsuccessful_validation_count"]

    if failed_validations > 0:
        logger.warning("WARNING: not all expectations were passed at validation time")
        batch_definition = ge_results.list_validation_results()[0]["meta"][
            "active_batch_definition"
        ]
        batch = batch_definition["batch_identifiers"].values()
        raise ge.exceptions.GreatExpectationsError(
            f"The expectations run on the batch of data for {batch} failed, "
            "because not all expectations were successfully passed. Please review the "
            "results by generating the GE Data Docs and inspecting the failed run."
        )
    else:
        logger.info("All expectations were successfully passed")
        return True


def checkpoint_without_datadocs_update(test_config: TestingConfiguration) -> str:
    """Function that generate a checkpoint for data testing based on the
    SimpleCheckpoint template, but without the automatic action to update the Data
    Docs website.

    This can be helpful when you run many validations against a checkpoint (1000+),
    which severly slows down the rendering of the Data Docs website. Instead, you can
    use this checkpoint to run and store just the validations, to generate the Data
    Docs website at a later stage.

    Parameters
    ----------
    test_config : TestingConfiguration
        Initialized testing configuration which contains the following attributes:
        -   checkpoint_name
        -   run_name_template
        -   expectation_suite_name

    Returns
    -------
    str
        A string containing the YAML configuration for a checkpoint
    """
    checkpoint_yml = f"""
name: {test_config.checkpoint_name}
config_version: 1.0
template_name:
module_name: great_expectations.checkpoint
class_name: Checkpoint
run_name_template: {test_config.run_name_template}
expectation_suite_name: {test_config.expectations_suite_name}
batch_request: {{}}
action_list:
  - name: store_validation_result
    action:
      class_name: StoreValidationResultAction
  - name: store_evaluation_params
    action:
      class_name: StoreEvaluationParametersAction
evaluation_parameters: {{}}
runtime_configuration: {{}}
ge_cloud_id:
expectation_suite_ge_cloud_id:"""
    return yaml.load(checkpoint_yml)


# Helper functions for Jupyter
def make_clickable(url):
    """Helper function to make HTML tags around a url"""
    return f'<a href="{url}">{url}</a>'


def generate_link_in_notebook(url: str):
    """Helper function to make a URL clickable in a Jupyter notebook"""
    return display(HTML(make_clickable(url)))


def generate_ge_site_link(build_data_docs_output: dict) -> str:
    """Helper function to create URL to GE Data Docs website using
    context.build_data_docs() output"""
    url_raw = build_data_docs_output[list(build_data_docs_output.keys())[0]]
    url_os_adjusted = url_raw.replace(os.sep, "/")
    url_output = url_os_adjusted.replace(".blob.", ".z6.web.").replace(
        "/$web/index.html", ""
    )

    return url_output


def print_ge_site_link(build_data_docs_output: dict):
    """Helper function to output link to GE site in Jupyter notebook"""
    url = generate_ge_site_link(build_data_docs_output)
    return generate_link_in_notebook(url)
