# -- Base Python imports
import logging
import re

# -- 3rd party imports
import boto3
import botocore
import ipaddress


# -- Functions
def validate_s3_buckets(cfg: dict):
    """Function to validate the passed S3 bucket names in the config file for a project"

    Parameters
    ----------
    cfg : dict
        The passed config to be checked for buckets
    """
    logging.info("Validating bucket names provided in project config")

    # -- 1. Get bucket names
    BUCKETS = ["store_bucket", "site_bucket", "data_bucket"]
    list_buckets = [cfg[bucket] for bucket in BUCKETS if cfg[bucket] != ""]

    # -- 2. Validate
    for bucket_name in list_buckets:
        validate_bucket_name(bucket_name)


def validate_bucket_name(bucket_name: str):
    """This function validates a provided name for an S3 bucket, based on the rules
    outlined at 
    https://docs.aws.amazon.com/AmazonS3/latest/userguide/bucketnamingrules.html.

    Parameters
    ----------
    bucket_name : str
        Name to be used for an S3 bucket
    """
    logging.debug(f"Check validity of bucket name {bucket_name}")
    s3_resource = boto3.resource("s3")

    # -- 1. Bucket name too short
    assert len(bucket_name) >= 3, (
        f"Bucket name {bucket_name} is too short. Bucket names should be at least 3 "
        "characters"
    )

    # -- 2. Bucket name too long
    assert len(bucket_name) <= 64, (
        f"Bucket name {bucket_name} is too long. Bucket names should be at most 64 "
        "characters"
    )

    # -- 3. Name must consists of lowercase letters, numbers, dots or hyphens
    reg_pattern = r"[^a-z0-9\-\.]"
    list_not_allowed = []
    for character in bucket_name:
        if re.search(reg_pattern, character):
            list_not_allowed.append(character)

    assert not list_not_allowed, (
        f"Bucket name {bucket_name} contains unallowed characters: {list_not_allowed}. "
        "S3 bucket names should only consists of lowercase letters, numbers, dots or "
        "hyphens"
    )

    # -- 4. Begin and end character must be number or character
    reg_pattern = r"[a-z0-9]"
    first, last = bucket_name[0], bucket_name[-1]
    assert re.search(reg_pattern, first), (
        f"Unallowed first character found in bucket name {bucket_name}, {first}. "
        "First character must be a number or a lowercase letter"
    )
    assert re.search(reg_pattern, last), (
        f"Unallowed last character found in bucket name {bucket_name}, {last}. "
        "Last character must be a number or a lowercase letter"
    )

    # -- 5. No adjacent periods in bucket name
    reg_pattern = r"\.\."
    assert not re.search(
        reg_pattern, bucket_name
    ), f"Bucket name {bucket_name} contains adjacent periods, which is not allowed"

    # -- 6. Bucket name must not be formatted as an IP address
    error = None
    try:
        ipaddress.ip_address(bucket_name)
    except ValueError as e:
        error = e
        pass

    assert (
        error
    ), f"Bucket name {bucket_name} is formatted as an IP address, which is not allowed"

    # -- 7. Bucket name must not start with xn--
    assert not bucket_name.startswith(
        "xn--"
    ), f"Bucket name {bucket_name} starts with xn--, which is not allowed"

    # -- 8. Bucket name must not end with -s3alias
    assert not bucket_name.endswith(
        "-s3alias"
    ), f"Bucket name {bucket_name} ends with -s3alias, which is not allowed"

    # -- 9. Name must be globally unique
    status_code = None
    try:
        s3_resource.meta.client.head_bucket(Bucket=bucket_name)
    except botocore.exceptions.ClientError as e:
        status_code = int(e.response["Error"]["Code"])

    assert status_code == 404, (
        f"Bucket name {bucket_name} already exists. Please pick a different, globally "
        "unique name for this bucket"
    )


def validate_region(region_name: str):
    """Function to validate if the provided AWS region is a valid one

    Parameters
    ----------
    region_name : str
        Name of the AWS region
    """
    logging.info(f"Check validity of region name {region_name}")
    list_regions = [
        "af-south-1",
        "ap-east-1",
        "ap-northeast-1",
        "ap-northeast-2",
        "ap-northeast-3",
        "ap-south-1",
        "ap-southeast-1",
        "ap-southeast-2",
        "ca-central-1",
        "eu-central-1",
        "eu-north-1",
        "eu-south-1",
        "eu-west-1",
        "eu-west-2",
        "eu-west-3",
        "me-south-1",
        "sa-east-1",
        "us-east-1",
        "us-east-2",
        "us-west-1",
        "us-west-2",
    ]
    assert region_name in list_regions, (
        f"The provided region, {region_name}, is not valid. Please choose an existing "
        f"AWS region. Existing regions are: {list_regions}"
    )
