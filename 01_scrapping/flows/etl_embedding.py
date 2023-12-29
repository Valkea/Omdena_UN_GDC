#! /usr/bin/env python3

"""
TODO
"""

from pathlib import Path

import pandas as pd

from prefect import flow, task
from prefect_aws import S3Bucket

from etl_common import read_AWS, write_AWS

import chromadb
from chromadb.utils import embedding_functions


@task(name="Embed chunks", log_prints=True)
def embed_chunks(data:list) -> list:

    embed_model = "all-MiniLM-L6-v2"
    documents=data['chunk'].values.tolist()

    embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=embed_model
    )

    embeddings = embedding_func(documents)
    print("EMBEDDING:", embeddings[:5])

    return embeddings



@task(name="Insert in VectorDatabase", log_prints=True)
def populate_vectordb(embeddings:list, data:list, vectordb_path):

    collection_name = "omdena_ungdc_docs"
    client = chromadb.PersistentClient(path=str(vectordb_path))

    # Prepare Data for ChromaDB inserts
    documents=data['chunk'].values.tolist()
    indexes=[f"id{i}" for i in data.index]

    meta_columns = ['file_hash', 'file_name', 'page', 'level', 'type', 'header']
    metadatas = []
    for i, item in data.iterrows():
        metadict = {c:item[c] for c in meta_columns}
        metadatas.append(metadict)

    # Create collection
    collection = client.create_collection(
        name=collection_name,
        # embedding_function=embedding_func,
        metadata={"hnsw:space": "cosine"},
    )

    # Insert data
    collection.add(
        embeddings=embeddings,
        documents=documents,
        ids=[f"id{i}" for i in data.index],
        metadatas=metadatas
    )


@flow(log_prints=True)
def omdena_ungdc_etl_embedding_parent():

    bucket_block = S3Bucket.load("omdena-un-gdc-bucket")

    # Load the extracted chunks
    local_dir = "data"
    pd_chunk_path = Path(local_dir, "extracted_chunks.csv")
    read_AWS(pd_chunk_path, pd_chunk_path, bucket_block)
    data = pd.read_csv(pd_chunk_path)


    # Compute embeddings
    embeddings = embed_chunks(data)

    # Insert data into VectorDB
    chroma_data_path = Path(local_dir, "chroma_data")
    populate_vectordb(embeddings, data, chroma_data_path)


if __name__ == "__main__":
    omdena_ungdc_etl_embedding_parent()
