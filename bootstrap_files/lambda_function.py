# Imports
import great_expectations as ge
from great_expectations.core.batch import RuntimeBatchRequest

from supporting_functions import (
    TestingConfiguration,
    AwsPreprocessFunction,
    evaluate_ge_results,
    setup_logging,
)
import boto3

# Logger
logger = setup_logging()


def lambda_handler(event, context):
    # -- 0. Load parameters from configuration file and event
    test_config = TestingConfiguration("project_config.yml")
    test_config.load_config()
    params = event["initialParameters"]

    # -- 1. Initialize GE and S3 objects
    s3_client = boto3.client("s3")
    bucket = boto3.resource("s3").Bucket(test_config.data_bucket)
    context = ge.data_context.DataContext()
    preprocessor = AwsPreprocessFunction(params)

    # -- 2. Load data
    ### PUT YOUR DATA LOADING LOGIC HERE
    # To validate a data batch, data must be loaded to subsequently validate
    # Accordingly, in the lines below custom logic is required to load
    # a dataset as a pandas DataFrame in the df_batch argument
    # To make the RuntimeBatchRequest complete, which is used by GE for running
    # validations, asset_name and batch_identifier are required
    # NOTE: in order for this to properly run, an expectation suite must have been
    # previously generated!
    df_batch = load_data()  # Needs to be defined!
    asset_name = "ASSET NAME OR LOGIC TO GENERATE IT GOES HERE"
    batch_identifier = "BATCH IDENTIFIER OR LOGIC TO GENERATE IT GOES HERE"

    # -- 3. Generate batch request to run validations using a checkpoint
    batch_request = RuntimeBatchRequest(
        datasource_name="runtime_data",
        data_connector_name="runtime_data_connector",
        data_asset_name=asset_name,
        runtime_parameters={"batch_data": df_batch},
        batch_identifiers={"batch_identifier": batch_identifier,},
    )

    # -- 4. Run validations
    results = context.run_checkpoint(
        checkpoint_name=f"{test_config.checkpoint_name}",
        validations=[{"batch_request": batch_request}],
    )

    # -- 5. Evaluate results, return input if successfull
    evaluate_ge_results(results)
    output = preprocessor.get_response(params["s3_key"], df_batch.shape)
    return output
