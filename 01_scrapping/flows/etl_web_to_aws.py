#! /usr/bin/env python3

import re
# import unidecode
import os
import pathlib
import requests
#import pandas as pd
# from datetime import timedelta

import urllib.request
from urllib.error import HTTPError

from prefect import flow, task
#from prefect_gcp.cloud_storage import GcsBucket
from prefect_aws import S3Bucket
from prefect.tasks import task_input_hash

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
}

@task(
    name="Get HTML code",
    log_prints=True,
    retries=3,
    # cache_key_fn=task_input_hash,
    # cache_expiration=timedelta(days=1),
)
def get_html(url:str) -> str:
    """Connect to https://www.un.org/techenvoy/global-digital-compact/submissions
       and get HTML code
    """

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.text
    else:
        raise Exception(f'Request failed with status code: {response.status_code}')


@task(name="Extract files urls from HTML", log_prints=True)
def get_files_uris(html_code:str, base_files:str) -> list:

    files = re.findall(fr"{base_files}([-_/A-Za-z0-9.]*.(pdf|doc))", html_code)

    return [f"{x[0]}" for x in files]


@task(name="Write Data Locally", log_prints=True)
def write_local(files:list, base_url:str, local_dir:pathlib.Path) -> list:
    """Write the DataFrame out locally as a Parquet file"""

    path_list = []

    if not os.path.exists(local_dir):
        os.makedirs(local_dir)

    for file_name in files:
        try:
            file_path = f"{base_url}{file_name}"
            print("Download:", file_name, file_path)

            r = requests.get(file_path, allow_redirects=True, headers=headers)
            local_path = pathlib.Path(local_dir, file_name)
            open(local_path, 'wb').write(r.content)
            path_list.append(local_path)

        except HTTPError as e:
            print(e, file_name)

    raise Exception("stop")

    return path_list

@task(name="Write Data on AWS-S3", log_prints=True)
def write_AWS(path_list:list) -> None:
    """Copy the files to AWS-S3"""

    bucket_block = S3Bucket.load("omdena-un-gdc-bucket")

    for p in path_list:
        print("Upload:", p)
        bucket_block.upload_from_path(from_path=p, to_path=p)


@flow(log_prints=True)
def omdena_ungdc_etl_web_to_aws_parent() -> None:

    print("ETL | Web to AWS-S3")

    source_url = 'https://www.un.org/techenvoy/global-digital-compact/submissions'
    base_files = "https://www.un.org/techenvoy/sites/www.un.org.techenvoy/files/"
    local_dir = 'dataXXX'

    html_code = get_html(source_url)
    files = get_files_uris(html_code, base_files)
    path_list = write_local(files, base_files, local_dir)
    write_AWS(path_list)

if __name__ == "__main__":
    omdena_ungdc_etl_web_to_aws_parent()
