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
    """Lambda function for the Grater Expectations tutorial. This function runs through
    the following steps:

    0. Load project parameters for the tutorial from project_config.yml and parse the
       event passed at runtime for object_prefix
    1. Initialize S3 bucket object and GE DataContext object
    2. Load data from S3 using the object_prefix passed in the event, parse the prefix
       for an asset name (name of the dataset) and batch_identifier (date of the
       dataset, retrieved from the file name)
    3. Generate a RuntimeBatchRequest to run against the checkpoint generated in
       expectation_suite.ipynb
    4. Set values for dynamic evaluation parameters and store in dictionary
    5. Run expectations against current batch of data by calling the checkpoint with
       the RuntimeBatchRequest from step 3 and dynamic evaluation parameters from step 4
    6. Evaluate expectation results and return status code 200 if successfull

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
    prefix = event["object_prefix"]

    # -- 1. Initialize AWS and GE objects
    bucket = boto3.resource("s3").Bucket(test_config.data_bucket)
    context = ge.data_context.DataContext()

    # -- 2. Load data using load_csv_from_s3 and parse the data prefix into an asset
    #       name and a batch identifier that can be used in the RuntimeBatchRequest
    #       to identify the current batch being run
    df_batch = load_data(bucket, prefix)
    # Extract asset name by getting file name of data (end of prefix)
    asset_name = prefix.split("/")[-1]
    # Extract batch_identifier by pulling date from filename (year_month)
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

    # -- 5. Run validations
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

    # -- 6. Evaluate results from running the expectations on the current batch of data,
    #       return statuscode 200 if successfull
    success = evaluate_ge_results(results)

    if success:
        return {"statuscode": 200}
