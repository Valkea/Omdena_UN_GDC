#! /usr/bin/env python3

"""
ETL Pipeline for PDF Parsing with IBM DeepSearch

This script defines a Prefect flow for extracting information from PDF files using IBM DeepSearch.
The flow includes tasks for parsing PDF, extracting JSON from ZIP, and parsing JSON files.

Tasks:
- Parse PDF: Utilizes the IBM DeepSearch API to convert PDF documents and download them locally.
- Extract JSON from ZIP: Extracts JSON files from ZIP archives generated by the DeepSearch process.
- Parse JSON: Processes JSON files to extract relevant information.

Prefect Flow:
- omdena_ungdc_etl_pdf_parsing_parent: Orchestrates the PDF parsing process for multiple files.
  - Initializes the DeepSearch API.
  - Retrieves a list of files to process from an AWS S3 bucket.
  - Parses each PDF, extracts JSON, and processes the information.
  - Updates a file tracking CSV with parsing status.
  - Writes the updated CSV back to the AWS S3 bucket.

Note: Ensure that the 'deepsearch', 'prefect', and 'prefect_aws' packages are installed for proper execution.
"""

import os
import json
import zipfile
from pathlib import Path
from typing import Optional, Union, Any, List, Dict

import pandas as pd
import deepsearch as ds
from deepsearch.cps.client.api import CpsApi

from prefect import flow, task
from prefect_aws import S3Bucket

from etl_common import read_AWS, write_AWS


@task(name="Parse PDF", log_prints=True)
def parse_PDF(
    api: CpsApi,
    proj_key: str,
    local_dir: str,
    file_path: Path,
    file_infos: pd.DataFrame,
) -> None:
    """
    Task to parse PDF documents using IBM DeepSearch.

    Parameters:
    - api (CpsApi): IBM DeepSearch API object.
    - proj_key (str): Project key for DeepSearch.
    - local_dir (str): Local directory to store downloaded documents.
    - file_path (Path): Path to the PDF file to be parsed.
    - file_infos (pd.DataFrame): Information about the file being processed.

    Returns:
    None
    """

    print(f"ETL | PDF parsing | Task: DeepSearch with {file_path}")

    documents = ds.convert_documents(api=api, proj_key=proj_key, source_path=file_path)
    documents.download_all(result_dir=local_dir)


@task(name="Extract JSON from ZIP", log_prints=True)
def extract_json(result_dir: str) -> Path:
    """
    Task to extract JSON files from ZIP archives.

    Parameters:
    - result_dir (str): Directory containing ZIP archives.

    Returns:
    Path: Path to the extracted JSON file.
    """

    print("ETL | PDF parsing | Task: Extracting JSON from Zip")

    json_file_path = None
    print("Extract from", result_dir)
    for document in os.listdir(result_dir):
        if document.endswith(".zip"):
            print(document)

            zip_file_path = Path(result_dir, document)
            with zipfile.ZipFile(zip_file_path, "r") as z:
                for filename in z.namelist():
                    if filename.endswith(".json"):
                        print(filename)

                        with z.open(filename) as f:
                            data = json.loads(f.read().decode("utf-8"))

                            json_file_path = Path(result_dir, filename)
                            with open(json_file_path, "w") as f:
                                json.dump(data, f, indent=4)

            os.remove(zip_file_path)

    return json_file_path



@task(name="Parse JSON", log_prints=True)
def parse_JSON(file_path: Path, pd_chunks: pd.DataFrame, file_infos:pd.DataFrame) -> None:
    """
    Task to parse information from JSON files.

    Parameters:
    - file_path (Path): Path to the JSON file to be parsed.
    - pd_chunks (pd.DataFrame): The pandas dataframe to store the extracted infos.
    - file_infos (pd.DataFrame): The source file informations.

    Returns:
    pd.DataFrame: The modified pandas dataframe.
    """

    print(f"ETL | PDF parsing | Task: Extracting infos from JSON {file_path}")

    min_chunk_size = 5

    with open(file_path, 'r') as file:
        data = json.load(file)

    last_header = None
    bloc_text = ""
    bloc_indexes = []
    last_index = pd_chunks.shape[0]
    ext_text = ""

    for item in data.get('main-text', []):


        if item['name'] == 'subtitle-level-1' and item['type'] == 'subtitle-level-1':
            last_header = item['text']

            if bloc_text != "":
                pd_chunks.loc[bloc_indexes, 'bloc'] = bloc_text
                bloc_text = ""
                bloc_indexes = []


        elif item['name'] == 'list-item' and item['type'] == 'paragraph':
            ext_text += item['text']
            ext_type = "list-item"


        elif item['name'] == 'text' and item['type'] == 'paragraph':
            ext_text += item['text']
            ext_type = "text"

        if ext_text != "":

            if len(ext_text) <= min_chunk_size:
                continue

            bloc_text += "\n"+ext_text
            bloc_indexes.append(last_index)
            last_index += 1

            new_row = {
                "file_hash": file_infos.file_hash,
                "file_name": file_infos.file_name,
                "page": item['prov'][0]['page'],
                "type": ext_type,
                "header": last_header,
                "chunk": ext_text,
                "bloc": "X"
            }

            pd_chunks = pd.concat([pd_chunks, pd.DataFrame([new_row])], ignore_index=True)
            ext_text = ""

    pd_chunks.loc[bloc_indexes, 'bloc'] = bloc_text

    return pd_chunks



@flow(log_prints=True)
def omdena_ungdc_etl_pdf_parsing_parent(max_doc:int = None) -> None:
    """
    Prefect flow for orchestrating PDF parsing using IBM DeepSearch.

    Parameters:
    - max_doc (int): The maximum number of documents to process

    Returns:
    None
    """

    print("ETL | PDF parsing")

    # Define IBM DeepSearch access
    api = CpsApi.from_env()
    proj_key = api.projects.list()[0].key

    # Get the list of files to ingest
    bucket_block = S3Bucket.load("omdena-un-gdc-bucket")

    local_dir = "data"
    if not os.path.exists(local_dir):
        raise Exception("The source folder doesn't exist")

    files_tracker_path = Path(local_dir, "files_tracker.csv")
    read_AWS(files_tracker_path, files_tracker_path, bucket_block)
    files_tracker = pd.read_csv(files_tracker_path)

    columns = ['file_hash','file_name','page','type','header','chunk','bloc']
    pd_chunks = pd.DataFrame(columns=columns)
    pd_chunk_path = Path(local_dir, "extracted_chunks.csv")

    # Parse the collected files
    i = 0
    for file in files_tracker.itertuples():
        if file.present_in_last_update is True and file.parsed is False: # ⚠️ 
            file_path = Path(local_dir, file.file_name)

            # Parse PDF using IBM DeepSearch
            parse_PDF(api, proj_key, local_dir, file_path, file)

            # Extract the JSON file from the returned DeepSearch Zip
            json_file_path = extract_json(local_dir)

            # Extract interesting information from JSON file
            pd_chunks = parse_JSON(json_file_path, pd_chunks, file)

            # Update the files_tracker
            files_tracker.at[file.Index, "parsed"] = True

            i += 1
        else:
            print(f"The last version of {file.file_name} has already been parsed")

        if max_doc is not None and i >= max_doc:
            break

    pd_chunks.to_csv(pd_chunk_path, index=False)

    files_tracker.to_csv(files_tracker_path, index=False)
    write_AWS(files_tracker_path, files_tracker_path, bucket_block)


if __name__ == "__main__":
    omdena_ungdc_etl_pdf_parsing_parent()
