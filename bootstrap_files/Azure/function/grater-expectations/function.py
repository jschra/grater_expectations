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
from supporting_functions import load_csv_from_container as load_data

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

    # -- 0. Load parameters from configuration file and event
    test_config = TestingConfiguration(PATH_PROJECT_CONFIG)
    test_config.load_config()

    # -- 1. Parse request params, derive asset_name from path_to_file
    request_params = dict(req.params)
    path_to_file = request_params["path_file"]
    asset_name = path_to_file.split("/")[-1]

    # -- 2. Authenticate on Azure and initilize blob service
    credentials = DefaultAzureCredential()
    storage_client = StorageManagementClient(
        credentials, os.environ.get("AZURE_SUBSCRIPTION_ID")
    )
    connection_string = get_connection_string(storage_client, test_config)

    blob_service_client = BlobServiceClient.from_connection_string(
        conn_str=connection_string
    )

    # -- 3. Initialize GE DataContext
    context = ge.data_context.DataContext(context_root_dir=PATH_GE_CONFIG)

    # -- 4. Load data using load_data and set a batch identifier that can be used in
    #       the RuntimeBatchRequest to identify the current batch being run
    df_batch = load_data(
        blob_service_client=blob_service_client,
        container_name=test_config.data_container_name,
        path_csv=path_to_file,
    )
    #       Extract batch_identifier by pulling date from filename (year_month)
    batch_identifier = re.search(r"\d{4}\-\d{2}", asset_name)[0]

    # -- 5. Generate batch request to run validations using a checkpoint
    batch_request = RuntimeBatchRequest(
        datasource_name="runtime_data",
        data_connector_name="runtime_data_connector",
        data_asset_name=asset_name,
        runtime_parameters={"batch_data": df_batch},
        batch_identifiers={"batch_identifier": batch_identifier},
    )

    # -- 6. Set dynamic evaluation parameters
    #       Here, evaluation parameters are provided at runtime. They are hard-coded
    #       for simplicity, but note that you could develop your own logic to for
    #       example derive testing values with data from last month to test the data
    #       of this month against. The code below just shows you how this can be done
    MIN_MAX_PASSENGER_COUNT = 5
    MAX_MAX_PASSENGER_COUNT = 8
    dict_evaluation_parameters = {
        "min_max_passenger_count": MIN_MAX_PASSENGER_COUNT,
        "max_max_passenger_count": MAX_MAX_PASSENGER_COUNT,
    }

    # -- 7. Run validations
    #       Below, the checkpoint generated in the expectation_suite.ipynb is being
    #       called, passing the currently loaded dataset as batch request to run the
    #       expectations against. To accomodate for the dynamic evaluation parameters,
    #       values for these are being passed in a dictionary
    #       (dict_evaluation_parameters) to the evaluation_parameters argument
    results = context.run_checkpoint(
        checkpoint_name=f"{test_config.checkpoint_name}",
        validations=[{"batch_request": batch_request}],
        evaluation_parameters=dict_evaluation_parameters,
    )

    # -- 8. Evaluate results from running the expectations on the current batch of data,
    #       return statuscode 200 if successfull
    success = evaluate_ge_results(results)

    if success:
        return func.HttpResponse(json.dumps({"statuscode": 200}))
    else:
        return func.HttpResponse(
            json.dumps({"statuscode": 500, "message": "Something went wrong"})
        )

