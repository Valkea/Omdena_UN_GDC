#! /usr/bin/env python3

import re
import os
import pathlib
import requests
from datetime import timedelta

from prefect import flow, task
from prefect_aws import S3Bucket
from prefect.tasks import task_input_hash

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
    """Connect to https://www.un.org/techenvoy/global-digital-compact/submissions and get HTML code"""

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.text
    else:
        raise Exception(f"Request failed with status code: {response.status_code}")


@task(name="Extract files urls from HTML", log_prints=True)
def get_files_uris(html_code: str, base_files: str) -> list:
    """Find file uris in the provided HTML code"""

    files = re.findall(rf"{base_files}([-_/A-Za-z0-9.]*.(pdf|doc))", html_code)

    return [f"{x[0]}" for x in files]


@task(
    name="Write Data Locally",
    log_prints=True,
    cache_key_fn=task_input_hash,
    cache_expiration=timedelta(days=1),
)
def write_local(base_url: str, file_name: str, local_dir: pathlib.Path) -> pathlib.Path:
    """Download the provided remote file locally"""

    try:
        file_path = f"{base_url}{file_name}"
        print("Download from source:", file_name, file_path)

        r = requests.get(file_path, allow_redirects=True, headers=headers)
        local_path = pathlib.Path(local_dir, file_name)
        open(local_path, "wb").write(r.content)

        return local_path

    except Exception as e:
        print(e, file_name)


@task(
    name="Write Data on AWS-S3",
    log_prints=True,
    cache_key_fn=task_input_hash,
    cache_expiration=timedelta(days=1),
)
def write_AWS(local_path: str, file_name: str, bucket_block: S3Bucket) -> None:
    """Upload a local file to AWS-S3"""

    try:
        print("Upload to S3:", local_path)
        bucket_block.upload_from_path(from_path=local_path, to_path=file_name)

    except Exception as e:
        print(e, file_name)


@flow(log_prints=True)
def omdena_ungdc_etl_web_to_aws_parent() -> None:
    """Collect files from source_url"""

    print("ETL | Web to AWS-S3")

    source_url = "https://www.un.org/techenvoy/global-digital-compact/submissions"
    base_files = "https://www.un.org/techenvoy/sites/www.un.org.techenvoy/files/"

    local_dir = "data"
    bucket_block = S3Bucket.load("omdena-un-gdc-bucket")

    if not os.path.exists(local_dir):
        os.makedirs(local_dir)

    html_code = get_html(source_url)
    files = get_files_uris(html_code, base_files)

    for file_name in files:
        local_path = write_local(base_files, file_name, local_dir)
        write_AWS(local_path, file_name, bucket_block)


if __name__ == "__main__":
    omdena_ungdc_etl_web_to_aws_parent()
