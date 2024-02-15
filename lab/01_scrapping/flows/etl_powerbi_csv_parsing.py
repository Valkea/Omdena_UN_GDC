#!/usr/bin/env python3

"""
ETL Pipeline for PowerBI CSV Parsing

This script defines a Prefect flow for parsing a PowerBI CSV file and updating the chunks dataframe.

Tasks:
- PBI_parse_csv: Parses PowerBI CSV data and updates the chunks dataframe.

Prefect Flow:
- omdena_ungdc_etl_powerbi_csv_parsing_parent: Orchestrates the process of parsing PowerBI CSV data.
  - Initializes variables for local directory, S3 bucket, and file paths.
  - Reads the existing files tracker CSV and extracted chunks CSV from AWS S3.
  - Parses PowerBI CSV data and updates the chunks dataframe.
  - Saves the updated chunks dataframe and files tracker CSV to local and uploads to AWS S3.

Note: Ensure that the required packages are installed for proper execution.
"""

import os
from pathlib import Path
from typing import Optional, Tuple

import pandas as pd
from llmsherpa.readers import LayoutPDFReader

from prefect import flow, task
from prefect_aws import S3Bucket

from etl_common import read_AWS, write_AWS, get_arguments

# from llama_index import VectorStoreIndex


@task(name="PowerBI Parse CSV", log_prints=True)
def PBI_parse_csv( powerbi_data: pd.DataFrame, pd_chunks: pd.DataFrame, files_tracker: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Task to parse PowerBI CSV data and update the chunks dataframe.

    Parameters:
    - powerbi_data (pd.DataFrame): PowerBI CSV data.
    - pd_chunks (pd.DataFrame): Existing chunks dataframe.
    - files_tracker (pd.DataFrame): Existing files tracker dataframe.

    Returns:
    Tuple[pd.DataFrame, pd.DataFrame]: Updated chunks dataframe and files tracker dataframe.
    """

    num_new = num_update = 0
    for i, row in powerbi_data.iterrows():

        v_file_hash = row["Record ID"]
        v_file_name = f"{row['Type']}, \
                {row['Location formatted']}, \
                {row['Contact Name']}, \
                {row['Entity Name']}"

        v_page = 0
        v_level = 0
        v_type = "PowerBI"

        # Add a new line to the file tracker

        new_row = {
            "file_hash": v_file_hash,
            "file_name": f"PowerBI_{str(row['Record ID'])}",
            # "file_creation_time": file_creation_time,
            "present_in_last_update": True,
            "parsed": True,
            "embedded": False,
            "indexed": False,
        }

        files_tracker = pd.concat(
            [files_tracker, pd.DataFrame([new_row])], ignore_index=True
        )

        # print(v_file_hash, v_file_name, v_page, v_level, v_type)

        for col_name in powerbi_data.columns[5:]:
            v_header = col_name.replace("_", " ")
            v_chunk = row[col_name]

            if v_chunk == None or v_chunk == "" or str(v_chunk) == "nan":
                continue

            probe = pd_chunks.index[
                    (pd_chunks['file_hash'] == str(v_file_hash)) &
                    (pd_chunks['file_name'] == v_file_name) &
                    (pd_chunks['header'] == v_header)
                    ].tolist()

            if len(probe) > 0:
                # print("The line already exists, we only update the Chunk", probe)
                pd_chunks.loc[probe,'chunk'] = v_chunk
                num_update += 1

            else:
                # print("The line doesn't exists, we add it to the DF")

                new_line = pd.DataFrame([{
                    "file_hash": str(v_file_hash),
                    "file_name": v_file_name,
                    "page": v_page,
                    "level": v_level,
                    "type": v_type,
                    "header": v_header,
                    "chunk": v_chunk,
                    "bloc": None
                }])

                pd_chunks = pd.concat(
                     [pd_chunks, new_line], axis="index", ignore_index=True
                )
                # pd_chunks = pd.concat(
                #     [
                #         pd_chunks.astype(new_line.dtypes),
                #         new_line.astype(pd_chunks.dtypes)
                #     ], axis="index", ignore_index=True
                # )

                num_new += 1


    print(f"{num_new} rows were added, {num_update} rows were updated")

    pd_chunks.drop_duplicates(inplace=True)
    return pd_chunks, files_tracker


@flow(log_prints=True)
def omdena_ungdc_etl_powerbi_csv_parsing_parent(max_doc: Optional[int] = None) -> None:
    """
    Prefect flow for orchestrating PowerBI CSV parsing.

    Parameters:
    - max_doc (Optional[int]): The maximum number of documents to process.

    Returns:
    None
    """

    print("ETL | CSV parsing")

    # Get the list of files to ingest
    bucket_block = S3Bucket.load("omdena-un-gdc-bucket")

    local_dir = "data"
    if not os.path.exists(local_dir):
        raise Exception("The source folder doesn't exist")

    files_tracker_path = Path(local_dir, "files_tracker.csv")
    if not os.path.exists(files_tracker_path):
        read_AWS(files_tracker_path, files_tracker_path, bucket_block)
    files_tracker = pd.read_csv(files_tracker_path)

    # Define the file to save the chunks
    pd_chunk_path = Path(local_dir, "extracted_chunks.csv")
    if not os.path.exists(pd_chunk_path):
        read_AWS(pd_chunk_path, pd_chunk_path, bucket_block)

    if os.path.exists(pd_chunk_path):
        pd_chunks = pd.read_csv(pd_chunk_path)
    else:
        columns = [
            "file_hash",
            "file_name",
            "page",
            "level",
            "type",
            "header",
            "chunk",
            "bloc",
        ]
        pd_chunks = pd.DataFrame(columns=columns)

    # Load PowerBI.csv
    powerbi_path = Path(local_dir, "powerBI.csv")
    powerbi_data = pd.read_csv(powerbi_path)

    # Add CSV rows to the Chunks dataframe
    pd_chunks, files_tracker = PBI_parse_csv(powerbi_data, pd_chunks, files_tracker)

    # Save
    pd_chunks.to_csv(pd_chunk_path, index=False)
    files_tracker.to_csv(files_tracker_path, index=False)

    write_AWS(files_tracker_path, files_tracker_path, bucket_block)
    write_AWS(pd_chunk_path, pd_chunk_path, bucket_block)


if __name__ == "__main__":
        omdena_ungdc_etl_powerbi_csv_parsing_parent()
