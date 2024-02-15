#! /usr/bin/env python3

import json
import argparse

import weaviate

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

    return client


def query_test(client: weaviate.Client, collection_name: str, query_text: str) -> None:
    """
    Task to perform a test query on the Vector Database.

    Parameters:
    - client (weaviate.Client): The Vector Database client.
    - collection_name (str): The name of the collection in the Vector Database.
    - query_text (str): The sentence we want to use for the retrieval.

    Returns:
    None
    """

    # query_text = "Tell me about sustainability by design"

    response = (
        client.query.get(
            collection_name,
            ["file_hash", "file_name", "page", "type", "header", "chunk"],
        )
        .with_limit(10)
        .with_near_text({"concepts": query_text})
        .with_additional(["distance", "certainty", "id"])
        .do()
    )

    print(json.dumps(response, indent=4))
    print(f"The query text was: {query_text}")

def get_arguments() -> str:
    """
    Initialize the argparse module and return the expected arguments.

    Returns:
    str: The value of the 'query' argument if provided, otherwise None.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "query",
        type=str,
        help="The query we want to use for the Weaviate retrival",
    )
    args = parser.parse_args()

    return args.query

if __name__ == "__main__":
    collection_name = "OmdenaUngdcDocs"
    query_text = get_arguments()

    client = initialize_vectordb(collection_name)
    query_test(client, collection_name, query_text)
