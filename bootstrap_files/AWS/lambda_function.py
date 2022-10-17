# Imports
import great_expectations as ge
from great_expectations.core.batch import RuntimeBatchRequest

from supporting_functions import (
    TestingConfiguration,
    evaluate_ge_results,
    setup_logging,
)
import boto3

# Logger
logger = setup_logging()


def lambda_handler(event, context):
    """Lambda function for using Grater Expectations. This function runs through
    the following steps:

    0. Load project parameters for the tutorial from project_config.yml and parse the
       event passed at runtime
    1. Initialize S3 client object, S3 bucket object and GE DataContext object
    2. Load data (LOGIC TO BE WRITTEN BY DEVELOPER)
    3. Generate a RuntimeBatchRequest to run against the checkpoint generated in
       expectation_suite.ipynb
    4. Run expectations against current batch of data by calling the checkpoint with
       the RuntimeBatchRequest from step 3
    5. Evaluate expectation results and return status code 200 if successfull

    Parameters
    ----------
    event : dict
        Event passed to the Lambda at runtime
    context
        An object with methods and properties that provide information about the 
        invocation, function and execution environment. Does not need to be passed
        upon invocation
    """
    # -- 0. Load parameters from configuration file and event
    test_config = TestingConfiguration("project_config.yml")
    test_config.load_config()
    params = event

    # -- 1. Initialize GE and S3 objects
    s3_client = boto3.client("s3")
    bucket = boto3.resource("s3").Bucket(test_config.data_bucket)
    context = ge.data_context.DataContext()

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
    success = evaluate_ge_results(results)

    if success:
        return {"statuscode": 200}
