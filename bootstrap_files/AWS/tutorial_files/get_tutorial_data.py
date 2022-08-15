# -- Imports
import boto3
import pandas as pd
import shutil
import os

# -- Constants
PREFIX_DATA = "trip data/"
S3_BUCKET = "nyc-tlc"
LOCAL_DATA_DIR = "tutorial_data/"

# -- Initialize objects
s3 = boto3.client("s3")


def main():
    # -- 1. Get pages, extract objects, filter for parquet
    pages = get_object_pages_at_prefix(s3, S3_BUCKET, PREFIX_DATA)
    objects = extract_prefixes_from_pages(pages)
    objects = [obj for obj in objects if ".parquet" in obj]

    # -- 2. Load last parquet files as pandas DataFrame
    files_to_load = objects[-5:]

    list_df = []
    for prefix in files_to_load:
        prefix = "s3://" + prefix
        list_df.append(pd.read_parquet(prefix))

    # -- 3. Create directory, create tutorial csv's
    create_new_directory_at_root(LOCAL_DATA_DIR, overwrite=True)
    create_tutorial_data(list_df, files_to_load, LOCAL_DATA_DIR)


def get_object_pages_at_prefix(
    s3_client: boto3.client("s3"), bucket_name: str, prefix: str, delimiter: str = "/"
) -> list:
    """Helper function to get list of objects within an S3 bucket at a specific prefix.
    Returns a list of results from running the paginator, as the API can only return
    1,000 keys per iteration. Hence if more than 1,000 objects exist under a specific
    prefix, multiple pages of results are returned by this function.  

    Parameters
    ----------
    s3_client : boto3.client
        Instantiated s3 client using boto3
    bucket_name : str
        Name of bucket to query
    prefix : str
        Prefix to query
    delimiter : str, optional
        Delimiter used in prefixes, by default "/"

    Returns
    -------
    list
        List of page results from running the paginator
    """
    # Create a paginator to handle multiple pages from list_objects_v2
    paginator = s3_client.get_paginator("list_objects_v2")

    # Get each page from a call to list_objects_v2
    pages = []
    for page in paginator.paginate(
        Bucket=bucket_name, Prefix=prefix, Delimiter=delimiter
    ):
        pages.append(page)

    return pages


def extract_prefixes_from_pages(list_pages) -> list:
    """Helper function to extract list of objects from the results of 
    get_object_pages_at_prefix"""
    object_prefixes = []
    for page in list_pages:
        for object in page["Contents"]:
            object_prefixes.append(S3_BUCKET + "/" + object["Key"])

    return object_prefixes


def create_new_directory_at_root(path: str, overwrite: bool = False):
    """Helper function to create a new directory at the current root of the kernel
    (current working directory)"""
    if not overwrite:
        os.mkdir(path)
    else:
        shutil.rmtree(path)
        os.mkdir(path)


def create_tutorial_data(list_data: list, list_prefixes: list, directory: str):
    """Helper function that creates the tutorial datasets

    Parameters
    ----------
    list_data : list
        List of DataFrames previously loaded from public AWS data
    list_prefixes : list
        List of prefixes of the datasets that were loaded
    directory : str
        Local directory wherein the tutorial datasets should be stored
    """
    for df, prefix in zip(list_data, list_prefixes):
        df_output = df.loc[0:9999]
        file_name = prefix.split("/")[-1].replace(".parquet", "") + ".csv"
        path = "./" + directory + file_name
        df_output.to_csv(path, sep=",", header=True, index=False)


if __name__ == "__main__":
    main()
