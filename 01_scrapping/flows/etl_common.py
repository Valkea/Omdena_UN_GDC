"""
Common Utility Functions

This module defines various common utility functions for the ETL pipeline.

Functions:
- read_AWS: Downloads a remote file from AWS-S3 to a local folder.
- write_AWS: Uploads a local file to AWS-S3.
- get_arguments: Initialize the argparse module and return the expected arguments
  ...

Note: Ensure that the 'prefect' and 'prefect_aws' packages are installed for proper execution.
"""
import os
import argparse
from datetime import timedelta

import pandas as pd

from prefect import flow, task
from prefect_aws import S3Bucket

# from prefect.tasks import task_input_hash


@task(
    name="Read Data from AWS-S3",
    log_prints=True,
    # cache_key_fn=task_input_hash,
    # cache_expiration=timedelta(days=1),
)
def read_AWS(remote_path: str, local_path: str, bucket_block: S3Bucket) -> None:
    """
    Task to download a remote AWS-S3 file or folder to a local folder.

    Parameters:
    - remote_path (str): The path to the remote file or folder on AWS-S3.
    - local_path (str): The path to the local folder where the file will be downloaded.
    - bucket_block (S3Bucket): The Prefect S3Bucket object representing the AWS-S3 bucket.

    Returns:
    None
    """
    try:
        print("Download from S3:", remote_path, ">", local_path)
        if os.path.isfile(remote_path):
            bucket_block.download_object_to_path(
                from_path=str(remote_path), to_path=str(local_path)
            )
        elif os.path.isdir(remote_path):
            bucket_block.download_folder_to_path(
                from_folder=str(remote_path), to_folder=str(local_path)
            )

    except Exception as e:
        print(e, remote_path)


@task(
    name="Write Data on AWS-S3",
    log_prints=True,
    # cache_key_fn=task_input_hash,
    # cache_expiration=timedelta(days=1),
)
def write_AWS(local_path: str, remote_path: str, bucket_block: S3Bucket) -> None:
    """
    Task to upload a local file or folder to AWS-S3.

    Parameters:
    - local_path (str): The path to the local file or folder to be uploaded.
    - remote_path (str): The path to the remote location on AWS-S3.
    - bucket_block (S3Bucket): The Prefect S3Bucket object representing the AWS-S3 bucket.

    Returns:
    None
    """
    try:
        print("Upload to S3:", local_path, ">", remote_path)
        if os.path.isfile(local_path):
            bucket_block.upload_from_path(
                from_path=str(local_path), to_path=str(remote_path)
            )
        elif os.path.isdir(local_path):
            bucket_block.upload_from_folder(
                from_folder=str(local_path), to_folder=str(remote_path)
            )

    except Exception as e:
        print(e, local_path)


def get_arguments() -> str:
    """
    Initialize the argparse module and return the expected arguments.

    Returns:
    str: The value of the 'max_doc' argument if provided, otherwise None.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--max_doc', help="The max number of documents to process (for testing purpose)")
    args = parser.parse_args()

    max_doc = None
    if args.max_doc:
        max_doc = args.max_doc
        print(f"Max document to process: {max_doc}")

    return max_doc

