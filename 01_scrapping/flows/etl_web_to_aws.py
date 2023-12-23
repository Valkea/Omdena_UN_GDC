#! /usr/bin/env python3

import re
import os
import pathlib
import requests
import hashlib
import time

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


def generate_hash(contents):

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
def write_local(base_url: str, file_name: str, local_dir: pathlib.Path) -> pathlib.Path:
    """Download the provided remote file locally"""

    try:
        file_path = f"{base_url}{file_name}"
        print("Download from source:", file_name, file_path)

        r = requests.get(file_path, allow_redirects=True, headers=headers)
        file_hash = generate_hash(r.content)

        local_path = pathlib.Path(local_dir, file_name)
        tmp_path = pathlib.Path(local_dir, f"{file_name}.tmp")

        open(tmp_path, "wb").write(r.content)

        return local_path, tmp_path, file_hash

    except Exception as e:
        print(e, file_name)



def get_info(path):

    with open(path, 'rb') as f:
        pdf = PdfReader(f)
        info = pdf.metadata

    # number_of_pages = len(pdf.pages)
    # print(info)
    # author = info.author
    # creator = info.creator
    # producer = info.producer
    # subject = info.subject
    # title = info.title

    return info.creation_date


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

    files_tracker_path = pathlib.Path('data', 'files_tracker.csv')
    read_AWS(files_tracker_path, files_tracker_path, bucket_block)

    if os.path.exists(files_tracker_path):
        files_tracker = pd.read_csv(files_tracker_path)
        files_tracker['present_in_last_update'] = False
    else:
        columns = ['file_hash','file_name','file_creation_time','present_in_last_update', 'parsed', 'embedded', 'indexed']
        files_tracker = pd.DataFrame(columns=columns)

    for i, file_name in enumerate(files):

        print("================>", i, file_name)

        local_path, tmp_path, file_hash = write_local(base_files, file_name, local_dir)

        if file_hash in files_tracker['file_hash'].values:
            print(i, "La ligne existe")

            file_index = files_tracker.index[files_tracker['file_hash']==file_hash][0]
            files_tracker.at[file_index, 'present_in_last_update'] = True

            if os.path.exists(local_path):
                os.remove(tmp_path)
            else:
                os.rename(tmp_path, local_path)

        else:
            print(i, "La ligne n'existe PAS")

            os.rename(tmp_path, local_path)

            file_creation_time = get_info(local_path)
            new_row = {"file_hash":file_hash, "file_name":file_name, "file_creation_time":file_creation_time, "present_in_last_update":True, "parsed":False, "embedded":False, "indexed":False}

            files_tracker = pd.concat([files_tracker, pd.DataFrame([new_row])], ignore_index=True)
            write_AWS(local_path, local_path, bucket_block)

        files_tracker.to_csv(files_tracker_path, index=False)
        write_AWS(files_tracker_path, files_tracker_path, bucket_block)

        if i >= 1:
            break

if __name__ == "__main__":
    omdena_ungdc_etl_web_to_aws_parent()
