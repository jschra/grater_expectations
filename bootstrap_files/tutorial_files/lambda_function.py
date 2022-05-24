# Imports
import great_expectations as ge
from great_expectations.core.batch import RuntimeBatchRequest

from supporting_functions import (
    TestingConfiguration,
    evaluate_ge_results,
    setup_logging,
)
from supporting_functions import load_csv_from_s3 as load_data
import boto3
import re

# Logger
logger = setup_logging()


def lambda_handler(event, context):
    # -- 0. Load parameters from configuration file and event
    test_config = TestingConfiguration("project_config.yml")
    test_config.load_config()
    prefix = event["object_prefix"]

    # -- 1. Initialize AWS and GE objects
    bucket = boto3.resource("s3").Bucket(test_config.data_bucket)
    context = ge.data_context.DataContext()

    # -- 2. Load data and extract tile information
    ### PUT YOUR DATA LOADING LOGIC HERE
    # To validate a data batch, data must be loaded to subsequently validate
    # Accordingly, in the lines below custom logic is required to load
    # a dataset as a pandas DataFrame in the df_batch argument
    # To make the RuntimeBatchRequest complete, which is used by GE for the
    # validations a tile, asset_name and batch_identifier are required
    # NOTE: in order for this to properly run, an expectation suite must have been
    # previously generated!
    df_batch = load_data(bucket, prefix)
    asset_name = prefix.split("/")[-1]
    batch_identifier = re.search(r"\d{4}\-\d{2}", asset_name)[0]

    # -- 3. Generate batch request to run validations using a checkpoint
    batch_request = RuntimeBatchRequest(
        datasource_name="runtime_data",
        data_connector_name="runtime_data_connector",
        data_asset_name=asset_name,
        runtime_parameters={"batch_data": df_batch},
        batch_identifiers={"batch_identifier": batch_identifier},
    )

    # -- 4. Set dynamic evaluation parameters
    MIN_MAX_PASSENGER_COUNT = 5
    MAX_MAX_PASSENGER_COUNT = 8
    dict_evaluation_parameters = {
        "min_max_passenger_count": MIN_MAX_PASSENGER_COUNT,
        "max_max_passenger_count": MAX_MAX_PASSENGER_COUNT,
    }

    # -- 5. Run validations
    results = context.run_checkpoint(
        checkpoint_name=f"{test_config.checkpoint_name}",
        validations=[{"batch_request": batch_request}],
        evaluation_parameters=dict_evaluation_parameters,
    )

    # -- 5. Evaluate results, return statuscode 200 if successfull
    success = evaluate_ge_results(results)

    if success:
        return {"statuscode": 200}
