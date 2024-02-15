#! /usr/bin/env python3

"""
ETL Pipeline for Document Embedding and Indexing

This script defines a Prefect flow for embedding document chunks using SentenceTransformer and
indexing them in ChromaDB. The flow includes tasks for embedding chunks, inserting data into
ChromaDB, and performing a query for testing.

Tasks:
- Embed chunks: Utilizes SentenceTransformer to embed document chunks.
- Insert in VectorDatabase: Inserts embedded data into ChromaDB.
- Query Test: Performs a query test on the inserted data.

Prefect Flow:
- omdena_ungdc_etl_embedding_parent: Orchestrates the embedding and indexing process for multiple files.
  - Reads file information and extracted chunks from an AWS S3 bucket.
  - Embeds the chunks using SentenceTransformer and inserts them into ChromaDB.
  - Performs a query test on the indexed data.

Note: Ensure that the 'prefect', 'prefect_aws', 'chromadb', and 'sentence_transformers' packages
are installed for proper execution.
"""

import os
from pathlib import Path

import pandas as pd

from prefect import flow, task
from prefect_aws import S3Bucket
from prefect.utilities.annotations import quote

from etl_common import read_AWS, write_AWS, get_arguments

import chromadb
from chromadb.utils import embedding_functions


@task(name="Embed chunks", log_prints=True)
def embed_chunks(data: list) -> list:
    """
    Task to embed document chunks using SentenceTransformer.

    Parameters:
    - data (list): List of document chunks.

    Returns:
    list: List of embeddings.
    """

    embed_model = "all-MiniLM-L6-v2"
    documents = data["chunk"].values.tolist()

    embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=embed_model
    )

    embeddings = embedding_func(documents)
    # print("EMBEDDING:", embeddings[:5])

    return embeddings


@task(name="Insert in VectorDatabase", log_prints=True)
def populate_vectordb(collection: "Collection", embeddings: list, data: list):
    """
    Task to insert embedded data into ChromaDB.

    Parameters:
    - collection ('Collection'): ChromaDB collection.
    - embeddings (list): List of embeddings.
    - data (list): List of document chunks.

    Returns:
    None
    """

    # Prepare Data for ChromaDB inserts
    documents = data["chunk"].values.tolist()
    # indexes=[f"id{i}" for i in data.index]
    indexes = [f"{i}_{j}" for i, j in zip(data.file_hash, data.index)]

    meta_columns = ["file_hash", "file_name", "page", "level", "type", "header"]
    metadatas = []
    for i, item in data.iterrows():
        metadict = {c: item[c] for c in meta_columns}
        metadatas.append(metadict)

    # Insert data
    # collection.add(
    collection.upsert(
        embeddings=embeddings, documents=documents, ids=indexes, metadatas=metadatas
    )

    print(collection.peek(1))  # returns a list of the first 10 items in the collection
    print(collection.count())  # returns the number of items in the collection


def query_test(collection: "Collection"):
    query_results = collection.query(
        query_texts=["Tell me about sustainability by design"],
        n_results=10,
    )

    distances = query_results["distances"][0]
    for i, dist in enumerate(distances):
        if dist < 0.5:
            print("TXT:", query_results["documents"][0][i])
            print("ID:", query_results["ids"][0][i])
            print("DISTANCE:", query_results["distances"][0][i])
            print("METADATAS:", query_results["metadatas"][0][i])
            print("***************")
        else:
            print("DISTANCE:", query_results["distances"][0][i])

    print("KEYS:", query_results.keys())
    # print("TXTS:",query_results["documents"])
    # print("IDS:", query_results["ids"])
    # print("DISTANCES:", query_results["distances"])
    # print("METADATAS:", query_results["metadatas"])


@flow(log_prints=True)
def omdena_ungdc_etl_embedding_parent(max_doc: int = None) -> None:
    """
    Prefect flow for orchestrating document Embedding and Indexing

    Parameters:
    - max_doc (int): The maximum number of documents to process

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

    # Get the existing vectordb or create it
    chroma_data_path = Path(local_dir, "chroma_data")
    if not os.path.exists(chroma_data_path):
        read_AWS(chroma_data_path, chroma_data_path, bucket_block)
    client = chromadb.PersistentClient(path=str(chroma_data_path))

    collection_name = "omdena_ungdc_docs"
    collection = client.get_or_create_collection(
        name=collection_name,
        # embedding_function=embedding_func,
        metadata={"hnsw:space": "cosine"},
    )

    # Iterate through files and embed the associated chunks
    i = 0
    for file in files_tracker.itertuples():
        # Check if the chunks of this file are alredy in the DB
        r = collection.get(where={"file_hash": file.file_hash})

        # Encode and inject them if they are not in the DB
        if len(r["ids"]) == 0 and file.present_in_last_update is True:
            # Select chunks
            doc_chunks = data[data["file_hash"] == file.file_hash]

            # Compute embeddings
            embeddings = embed_chunks(doc_chunks)
            files_tracker.at[file.Index, "embedded"] = True

            # Insert new embeddings in the VectorDB
            populate_vectordb(quote(collection), embeddings, doc_chunks)
            files_tracker.at[file.Index, "indexed"] = True

        else:
            print(
                f"The last version of {file.file_name} has already been embeded and indexed"
            )

        # Delete the chunks if they exist but the document was removed
        if file.present_in_last_update is False:
            collection.delete(where={"file_hash": file.file_hash})

        i += 1
        if max_doc is not None and i >= max_doc:
            break

    files_tracker.to_csv(files_tracker_path, index=False)
    write_AWS(files_tracker_path, files_tracker_path, bucket_block)
    write_AWS(chroma_data_path, chroma_data_path, bucket_block)

    print(
        "Num elements in the DB:", collection.count()
    )  # returns the number of items in the collection

    query_test(collection)


if __name__ == "__main__":
    max_doc = get_arguments()
    omdena_ungdc_etl_embedding_parent(max_doc)
