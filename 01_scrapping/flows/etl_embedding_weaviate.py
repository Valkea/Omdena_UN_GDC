#! /usr/bin/env python3

"""
ETL Pipeline for Document Embedding and Indexing

This script defines the Prefect flow for orchestrating document embedding and indexing.

Functions:
- initialize_vectordb: Function to initialize the Vector Database for document embedding.
- add_object: Function to add an object to the Vector Database.
- populate_vectordb: Task to populate the Vector Database with document information.
- query_test: Task to perform a test query on the Vector Database.

Flow:
- omdena_ungdc_etl_embedding_parent: Prefect flow for orchestrating document embedding and indexing.
  - Initializes the Vector Database.
  - Populates the Vector Database with document information.
  - Performs a test query on the Vector Database.

Parameters:
- max_doc (int): The maximum number of documents to process.

Returns:
None
"""

import os
import json
from pathlib import Path

import numpy as np
import pandas as pd

from prefect import flow, task
from prefect_aws import S3Bucket
from prefect.utilities.annotations import quote

import weaviate

from etl_common import read_AWS, write_AWS, get_arguments


@task(name="Initialize VectorDatabase", log_prints=True)
def initialize_vectordb(collection_name: str) -> weaviate.Client:
    """
    Function to initialize the Vector Database for document embedding & indexing.

    Parameters:
    - collection_name (str): The name of the collection in the Vector Database.

    Returns:
    weaviate.Client: The initialized Vector Database client.
    """

    client = weaviate.Client(
        url="http://0.0.0.0:8080"
    )  # Needs a Docker instance of Weaviate

    try:
        class_obj = {
            "class": collection_name,
            "vectorizer": "text2vec-transformers",
            # If set to "none" you must always provide vectors yourself.
            # Could be any other "text2vec-*" also.
            "moduleConfig": {
                "text2vec-transformers": {},
                "generative-openai": {}
                # Ensure the `generative-openai` module is used for generative queries
            },
        }

        # client.schema.delete_class("Question")  # ⚠️
        client.schema.create_class(class_obj)
    except Exception as e:
        print("Exception:", e)

    return client


def add_object(collection_name: str, client: weaviate.Client, obj: dict) -> None:
    """
    Function to add an object to the Vector Database.
    This is a sub-function of the populate_vectordb Task.

    Parameters:
    - collection_name (str): The name of the collection in the Vector Database.
    - client (weaviate.Client): The Vector Database client.
    - obj (dict): The object to be added to the Vector Database.

    Returns:
    None
    """

    global counter
    print_interval = 20

    properties = {
        "file_hash": obj["file_hash"],
        "file_name": obj["file_name"],
        "page": obj["page"],
        "level": obj["level"],
        "type": obj["type"],
        "header": obj["header"],
        "chunk": obj["chunk"],
    }

    client.batch.configure(batch_size=100)
    with client.batch as batch:
        # Add the object to the batch
        batch.add_data_object(
            data_object=properties,
            class_name=collection_name,
            # If you Bring Your Own Vectors, add the `vector` parameter here
            # vector=obj.vector
        )

        # Calculate and display progress
        counter += 1
        if counter % print_interval == 0:
            print(f"Imported {counter} articles...")


@task(name="Populate VectorDatabase", log_prints=True)
def populate_vectordb(
    collection_name: str,
    client: weaviate.Client,
    files_tracker: pd.DataFrame,
    data: pd.DataFrame,
    max_doc: int,
) -> None:
    """
    Task to populate the Vector Database with document information.

    Parameters:
    - collection_name (str): The name of the collection in the Vector Database.
    - client (weaviate.Client): The Vector Database client.
    - files_tracker (pd.DataFrame): DataFrame containing file tracking information.
    - data (pd.DataFrame): DataFrame containing document information.
    - max_doc (int): The maximum number of documents to process.

    Returns:
    None
    """

    global counter
    counter = i = 0

    for file in files_tracker.itertuples():
        print(f"Dealing with {file.file_name}")

        doc_chunks = data[data["file_hash"] == file.file_hash]

        where = {
            "path": ["file_hash"],
            "operator": "Equal",
            "valueText": file.file_hash,
        }

        # Check if file_hash si already in the VectorDB
        r = (
            client.query.get(collection_name, ["file_hash"])
            .with_limit(10000)
            .with_additional(["distance"])
            .with_where(where)
            .do()
        )
        # print(json.dumps(r, indent=4))

        try:
            num_chunks_db = len(r["data"]["Get"][collection_name])
        except KeyError:
            num_chunks_db = 0

        print(f"There are {num_chunks_db} entries from {file.file_name}")

        # Delete the previous entries
        if len(doc_chunks) != num_chunks_db and num_chunks_db > 0:
            print(f"Deleting {num_chunks_db} entries")

            del_result = client.batch.delete_objects(
                class_name=collection_name, where=where, dry_run=False
            )
            num_chunks_db = 0

        # Push the new entries
        if num_chunks_db == 0:
            print(f"Adding the {len(doc_chunks)} entries")
            for index, row in doc_chunks.iterrows():
                add_object(collection_name, client, row)

        else:
            print(
                f"The last version of {file.file_name} has already been embedded and indexed"
            )

        i += 1
        if max_doc is not None and i >= max_doc:
            break

    # Check VectorDB content
    classes = [d["class"] for d in client.schema.get()["classes"]]

    for class_name in classes:
        class_size = client.query.aggregate(class_name).with_meta_count().do()
        print(f"Num elements in [{class_name}]: {class_size['data']}")


@task(name="Test Query VectorDatabase", log_prints=True)
def query_test(client: weaviate.Client, collection_name: str) -> None:
    """
    Task to perform a test query on the Vector Database.

    Parameters:
    - client (weaviate.Client): The Vector Database client.
    - collection_name (str): The name of the collection in the Vector Database.

    Returns:
    None
    """

    query_texts = "Tell me about sustainability by design"

    response = (
        client.query.get(
            collection_name,
            ["file_hash", "file_name", "page", "type", "header", "chunk"],
        )
        .with_limit(10)
        .with_near_text({"concepts": query_texts})
        .with_additional(["distance", "certainty", "id"])
        .do()
    )

    print(json.dumps(response, indent=4))


@flow(log_prints=True)
def omdena_ungdc_etl_embedding_parent(max_doc: int = None) -> None:
    """
    Prefect flow for orchestrating document Embedding and Indexing.

    Parameters:
    - max_doc (int): The maximum number of documents to process.

    Returns:
    None
    """

    print("ETL | Embedding & Indexing")

    # Get the list of files to ingest
    bucket_block = S3Bucket.load("omdena-un-gdc-bucket")

    local_dir = "data"
    if not os.path.exists(local_dir):
        raise Exception("The source folder doesn't exist")

    files_tracker_path = Path(local_dir, "files_tracker.csv")
    if not os.path.exists(files_tracker_path):
        read_AWS(files_tracker_path, files_tracker_path, bucket_block)
    files_tracker = pd.read_csv(files_tracker_path)

    # Load the extracted chunks
    pd_chunk_path = Path(local_dir, "extracted_chunks.csv")
    if not os.path.exists(pd_chunk_path):
        read_AWS(pd_chunk_path, pd_chunk_path, bucket_block)
    data = pd.read_csv(pd_chunk_path)
    data = data.replace(np.nan, None)

    collection_name = "OmdenaUngdcDocs"
    client = initialize_vectordb(collection_name)
    populate_vectordb(collection_name, client, files_tracker, data, max_doc)

    files_tracker.to_csv(files_tracker_path, index=False)
    write_AWS(files_tracker_path, files_tracker_path, bucket_block)

    weaviate_db_path = Path(local_dir, "weaviate_data")
    write_AWS(weaviate_db_path, weaviate_db_path, bucket_block)

    # Query
    query_test(client, collection_name)

    # Check VectorDB content
    classes = [d["class"] for d in client.schema.get()["classes"]]

    for class_name in classes:
        class_size = client.query.aggregate(class_name).with_meta_count().do()
        print(f"Num elements in [{class_name}]: {class_size['data']}")


if __name__ == "__main__":
    max_doc = get_arguments()
    omdena_ungdc_etl_embedding_parent(max_doc)
