# -- Imports
from locale import D_FMT
import boto3
import pandas as pd
import ruamel.yaml as yaml
import logging
import great_expectations as ge
import sys
from IPython.display import display, HTML
import os

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


# S3 data handling functions
def get_file_keys_from_s3(
    s3_client: boto3.client, bucket: str, prefix: str = ""
) -> list:
    """Function that queries a bucket and a given prefix for underlying keys

    Parameters
    ----------
    s3_client : boto3.client
        Instantiated s3 client using boto3
    bucket : str
        Name of bucket to query
    prefix : str, optional
        Prefix to query

    Returns
    -------
    list
        List of keys
    """
    logger.info(f"Extracting file keys from {bucket} at {prefix}")
    client_response = s3_client.list_objects(Bucket=bucket, Prefix=prefix)
    file_keys = [elem["Key"] for elem in client_response["Contents"]]

    return file_keys


def load_csv_from_s3(
    s3_bucket_client: boto3.resource("s3").Bucket, prefix: str
) -> pd.DataFrame:
    """Function to loads a csv from S3 into a pandas DataFrame

    Parameters
    ----------
    s3_bucket_client : boto3.resource
        Instantiated s3 bucket client using boto3. Note that it should already
        be pointing to the bucket from which you want to load objects
    prefix : str
        Prefix to csv object on S3

    Returns
    -------
    pd.DataFrame
        The loaded csv object as pandas DataFrame
    """
    s3_object = s3_bucket_client.Object(prefix).get()
    df = pd.read_csv(s3_object["Body"])

    return df


def get_common_prefixes(
    s3: boto3.client, bucket_name: str, prefix: str = "", delimiter: str = "/"
) -> list:
    """Function to retrieve common prefixes (which function alike directories
    on S3) from an S3 bucket

    Parameters
    ----------
    s3 : boto3.client
        A boto3 S3 client
    bucket_name : str
        Name of the bucket to list common prefixes for
    prefix : str, optional
        Prefix ('directory') for which common prefixes should be listed,
        by default "", in other words the root
    delimiter : str, optional
        Delimiter by which prefixes in the bucket are seperated, by default "/"

    Returns
    -------
    list
        A list with common prefixes
    """
    results = []

    # Create a paginator to handle multiple pages from list_objects_v2
    paginator = s3.get_paginator("list_objects_v2")

    # Get each page from a call to list_objects_v2
    logger.info(f"Extracting common prefixes from {bucket_name} at {prefix}")
    for page in paginator.paginate(
        Bucket=bucket_name, Prefix=prefix, Delimiter=delimiter
    ):
        # Inside of each page, return the common prefixes (folders)
        for common_prefix in page.get("CommonPrefixes", []):
            results.append(common_prefix["Prefix"])

    logger.info("Common prefixes extracted")
    return results


# Function to invoke AWS Lambda function
def invoke_lambda_function(
    lambda_client: boto3.client, payload: bytes, lambda_function: str
) -> list:
    """Function to invoke a Lambda function from Python

    Parameters
    ----------
    lambda_client : boto3.client
        A boto3 client for lambda. It is expected initialised outside of this function.
    payload : bytes
        Payload to send to Lambda function in request, expected to contain a json 
        encoded as bytes
    lambda_function : str
        Name of the lambda function

    Returns
    -------
    list
        A list of responses from the lambdas
    """
    # -- Invoke lambda
    logger.info(
        f"Invoking AWS Lambda {lambda_function} with payload: {payload.decode('utf-8')}"
    )
    response = lambda_client.invoke(
        FunctionName=lambda_function, InvocationType="RequestResponse", Payload=payload,
    )

    if response["ResponseMetadata"]["HTTPStatusCode"] != 200:
        raise RuntimeError(
            "The lambda function has not run properly. Please check " " what went wrong"
        )

    return response


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
    url = build_data_docs_output[list(build_data_docs_output.keys())[0]]
    url_os_adjusted = url.replace(os.sep, "/")
    url_components = url_os_adjusted.split("/")
    url_start = "http://" + url_components[3]
    site_name_parts = url_components[2].split("-")
    site_name = "-".join([site_name_parts[0], "website", "-".join(site_name_parts[1:])])
    s3_url = ".".join([url_start, site_name]) + "/"
    return s3_url


def print_ge_site_link(build_data_docs_output: dict):
    """Helper function to output link to GE site in Jupyter notebook"""
    url = generate_ge_site_link(build_data_docs_output)
    return generate_link_in_notebook(url)
