import boto3
import pandas as pd
import shutil
import os

PREFIX_DATA = "trip data/"
S3_BUCKET = "nyc-tlc"
LOCAL_DATA_DIR = "tutorial_data/"
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
    _ = create_new_directory_at_root(LOCAL_DATA_DIR, overwrite=True)
    _ = create_tutorial_data(list_df, files_to_load, LOCAL_DATA_DIR)


def get_object_pages_at_prefix(
    s3_client, bucket_name: str, prefix: str, delimiter: str = "/"
) -> list:
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
    object_prefixes = []
    for page in list_pages:
        for object in page["Contents"]:
            object_prefixes.append(S3_BUCKET + "/" + object["Key"])

    return object_prefixes


def create_new_directory_at_root(path: str, overwrite: bool = False):
    if not overwrite:
        os.mkdir(path)
    else:
        shutil.rmtree(path)
        os.mkdir(path)


def create_tutorial_data(list_data, list_prefixes, directory):
    for df, prefix in zip(list_data, list_prefixes):
        df_output = df.loc[0:9999]
        file_name = prefix.split("/")[-1].replace(".parquet", "") + ".csv"
        path = "./" + directory + file_name
        df_output.to_csv(path, sep=",", header=True, index=False)


if __name__ == "__main__":
    main()
