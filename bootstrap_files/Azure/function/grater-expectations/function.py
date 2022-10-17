# -- Azure imports
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
from azure.mgmt.storage import StorageManagementClient
import azure.functions as func

# -- Great Expectations imports
import great_expectations as ge
from great_expectations.core.batch import RuntimeBatchRequest

# -- Grater expectations imports
from supporting_functions import (
    TestingConfiguration,
    evaluate_ge_results,
    setup_logging,
    get_connection_string,
)

# -- General imports
import logging
import json
import os
import re

# -- Set up logger
logger = setup_logging()

# -- Set constants so function properly works in Docker
PATH_PROJECT_ROOT = "/home/site/wwwroot/"
PATH_PROJECT_CONFIG = PATH_PROJECT_ROOT + "grater-expectations/project_config.yml"
PATH_GE_CONFIG = PATH_PROJECT_ROOT + "great_expectations"


# -- Main function
def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Python HTTP trigger function processed a request.")

    # -- 0. Load parameters from configuration file, initialize context
    test_config = TestingConfiguration(PATH_PROJECT_CONFIG)
    test_config.load_config()
    context = ge.data_context.DataContext(context_root_dir=PATH_GE_CONFIG)

    # -- 1. Parse request params
    request_params = dict(req.params)

    # -- 2. Load data
    ### PUT YOUR DATA LOADING LOGIC HERE
    # To validate a data batch, data must be loaded to subsequently validate
    # Accordingly, in the lines below custom logic is required to load
    # a dataset as a pandas DataFrame in the df_batch argument
    # To make the RuntimeBatchRequest complete, which is used by GE for running
    # validations, asset_name and batch_identifier are required
    # NOTE: in order for this to properly run, an expectation suite must have been
    # previously generated!
    df_batch = load_data()
    asset_name = "ASSET NAME OR LOGIC TO GENERATE IT GOES HERE"
    batch_identifier = "BATCH IDENTIFIER OR LOGIC TO GENERATE IT GOES HERE"

    # -- 3. Generate batch request to run validations using a checkpoint
    batch_request = RuntimeBatchRequest(
        datasource_name="runtime_data",
        data_connector_name="runtime_data_connector",
        data_asset_name=asset_name,
        runtime_parameters={"batch_data": df_batch},
        batch_identifiers={"batch_identifier": batch_identifier},
    )

    # -- 4. Run validations
    #       Below, the checkpoint generated in the expectation_suite.ipynb is being
    #       called, passing the currently loaded dataset as batch request to run the
    #       expectations against. To accomodate for the dynamic evaluation parameters,
    #       values for these are being passed in a dictionary
    #       (dict_evaluation_parameters) to the evaluation_parameters argument
    results = context.run_checkpoint(
        checkpoint_name=f"{test_config.checkpoint_name}",
        validations=[{"batch_request": batch_request}],
    )

    # -- 5. Evaluate results from running the expectations on the current batch of data,
    #       return statuscode 200 if successfull
    success = evaluate_ge_results(results)

    if success:
        return func.HttpResponse(json.dumps({"statuscode": 200}))
    else:
        return func.HttpResponse(
            json.dumps({"statuscode": 500, "message": "Something went wrong"})
        )

