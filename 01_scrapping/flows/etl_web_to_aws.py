#! /usr/bin/env python3

"""
ETL Pipeline for Web Data to AWS-S3

This script defines a Prefect flow for collecting files from a specified URL and uploading them to AWS S3.
The flow includes tasks for retrieving HTML code, extracting file URLs, downloading files locally, and uploading to AWS S3.

Tasks:
- Get HTML code: Connects to a specified URL and retrieves the HTML code.
- Extract files URLs from HTML: Finds file URLs in the provided HTML code.
- Write Data Locally: Downloads the provided remote file locally and returns local file paths.
- get_info: Extracts creation date information from a PDF file.

Prefect Flow:
- omdena_ungdc_etl_web_to_aws_parent: Orchestrates the process of collecting files from the source URL.
  - Initializes variables for the source URL, base file URL, local directory, and AWS S3 bucket.
  - Retrieves HTML code from the source URL.
  - Extracts file URLs from the HTML code.
  - Reads the existing file tracking CSV from AWS S3.
  - Iterates through each file, downloading and uploading it, and updating the file tracking CSV.

Note: Ensure that the 'requests', 'hashlib', 'pathlib', 'PyPDF2', 'pandas', 'prefect', and 'prefect_aws' packages are installed for proper execution.
"""

import re
import os
import requests
import hashlib
import time
from pathlib import Path
from typing import List, Tuple, Optional

# from datetime import timedelta

import pandas as pd

from PyPDF2 import PdfReader

from prefect import flow, task
from prefect_aws import S3Bucket

# from prefect.tasks import task_input_hash

from etl_common import read_AWS, write_AWS

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
}


@task(
    name="Get HTML code",
    log_prints=True,
    retries=3,
    # cache_key_fn=task_input_hash,
    # cache_expiration=timedelta(days=1),
)
def get_html(url: str) -> str:
    """
    Task to connect to the specified URL and retrieve the HTML code.

    Parameters:
    - url (str): The URL to connect to.

    Returns:
    str: The retrieved HTML code.
    """

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.text
    else:
        raise Exception(f"Request failed with status code: {response.status_code}")


@task(name="Extract files urls from HTML", log_prints=True)
def get_files_uris(html_code: str, base_files: str) -> List[str]:
    """
    Task to find file URLs in the provided HTML code.

    Parameters:
    - html_code (str): The HTML code to search for file URLs.
    - base_files (str): The base URL for the files.

    Returns:
    List[str]: List of file URLs.
    """

    files = re.findall(rf"{base_files}([-_/A-Za-z0-9.]*.(pdf|doc))", html_code)

    return [f"{x[0]}" for x in files]


def generate_hash(contents: bytes) -> str:
    """
    Generates the SHA-256 hash of the given contents.

    Parameters:
    - contents (bytes): The contents for which to generate the hash.

    Returns:
    str: The hexadecimal representation of the hash.
    """

    # Open the file in binary mode
    # with open(file_path, "rb") as f:

    # Read the contents of the file
    # contents = f.read()

    # Generate the SHA-256 hash of the contents
    hash_object = hashlib.sha256(contents)

    # Return the hexadecimal representation of the hash
    return hash_object.hexdigest()


@task(
    name="Write Data Locally",
    log_prints=True,
    # cache_key_fn=task_input_hash,
    # cache_expiration=timedelta(days=1),
)
def write_local(
    base_url: str, file_name: str, local_dir: Path
) -> Tuple[Path, Path, str]:
    """
    Task to download the provided remote file locally.

    Parameters:
    - base_url (str): The base URL for the files.
    - file_name (str): The name of the file to download.
    - local_dir (Path): The local directory to store the downloaded file.

    Returns:
    Tuple[Path, Path, str]: Tuple containing local file path, temporary file path, and file hash.
    """

    try:
        file_path = f"{base_url}{file_name}"
        print("Download from source:", file_path)

        r = requests.get(file_path, allow_redirects=True, headers=headers)
        file_hash = generate_hash(r.content)

        local_path = Path(local_dir, file_name)
        tmp_path = Path(local_dir, f"{file_name}.tmp")

        open(tmp_path, "wb").write(r.content)

        return local_path, tmp_path, file_hash

    except Exception as e:
        print(e, file_name)


def get_info(path: Path) -> Optional[str]:
    """
    Task to extract creation date information from a PDF file.

    Parameters:
    - path (Path): Path to the PDF file.

    Returns:
    Optional[str]: The creation date information.
    """

    with open(path, "rb") as f:
        pdf = PdfReader(f)
        info = pdf.metadata

    # number_of_pages = len(pdf.pages)
    # print(info)
    # author = info.author
    # creator = info.creator
    # producer = info.producer
    # subject = info.subject
    # title = info.title

    return info.creation_date


@flow(log_prints=True)
def omdena_ungdc_etl_web_to_aws_parent(max_doc:int = None) -> None:
    """
    Prefect flow for collecting files from a source URL and uploading them to AWS S3.

    Parameters:
    - max_doc (int): The maximum number of documents to process

    Returns:
    None
    """

    print("ETL | Web to AWS-S3")

    source_url = "https://www.un.org/techenvoy/global-digital-compact/submissions"
    base_files = "https://www.un.org/techenvoy/sites/www.un.org.techenvoy/files/"

    local_dir = "data"
    bucket_block = S3Bucket.load("omdena-un-gdc-bucket")

    if not os.path.exists(local_dir):
        os.makedirs(local_dir)

    html_code = get_html(source_url)
    files = get_files_uris(html_code, base_files)

    files_tracker_path = Path("data", "files_tracker.csv")
    read_AWS(files_tracker_path, files_tracker_path, bucket_block)

    if os.path.exists(files_tracker_path):
        files_tracker = pd.read_csv(files_tracker_path)
        files_tracker["present_in_last_update"] = False
    else:
        columns = [
            "file_hash",
            "file_name",
            "file_creation_time",
            "present_in_last_update",
            "parsed",
            "embedded",
            "indexed",
        ]
        files_tracker = pd.DataFrame(columns=columns)

    for i, file_name in enumerate(files):

        local_path, tmp_path, file_hash = write_local(base_files, file_name, local_dir)

        if file_hash in files_tracker["file_hash"].values:
            print(i, "This file_hash already exists in the files_tracker CSV")

            file_index = files_tracker.index[files_tracker["file_hash"] == file_hash][0]
            files_tracker.at[file_index, "present_in_last_update"] = True

            if os.path.exists(local_path):
                os.remove(tmp_path)
            else:
                os.rename(tmp_path, local_path)

        else:
            print(i, "This file_hash doesn't exists in the files_tracker CSV")

            os.rename(tmp_path, local_path)

            file_creation_time = get_info(local_path)
            new_row = {
                "file_hash": file_hash,
                "file_name": file_name,
                "file_creation_time": file_creation_time,
                "present_in_last_update": True,
                "parsed": False,
                "embedded": False,
                "indexed": False,
            }

            files_tracker = pd.concat(
                [files_tracker, pd.DataFrame([new_row])], ignore_index=True
            )
            write_AWS(local_path, local_path, bucket_block)

        if max_doc is not None and i+1 >= max_doc:
            break

    files_tracker.to_csv(files_tracker_path, index=False)
    write_AWS(files_tracker_path, files_tracker_path, bucket_block)


if __name__ == "__main__":
    omdena_ungdc_etl_web_to_aws_parent()
