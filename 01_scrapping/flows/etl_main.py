#! /usr/bin/env python3

"""
ETL Main Flow for Omdena UN GDC Project

This script defines the main Prefect flow for the Omdena UN GDC project.
The main flow sequentially calls other scripts/flows for web data collection to AWS-S3, PDF parsing with DeepSearch etc.

Flows:
- omdena_ungdc_etl_web_to_aws_parent: Flow for collecting files from a source URL and uploading them to AWS S3.
- omdena_ungdc_etl_pdf_parsing_parent: Flow for parsing PDF documents using IBM DeepSearch.

Prefect Flow:
- omdena_ungdc_etl_main_flow: The base flow that sequentially calls the other scripts/flows.
  - Calls the web data collection to AWS-S3 flow (omdena_ungdc_etl_web_to_aws_parent).
  - Calls the PDF parsing flow (omdena_ungdc_etl_pdf_parsing_parent).

Note: Ensure that the necessary dependencies and packages are installed for proper execution.
"""

import argparse

from prefect import flow
from etl_web_to_aws import omdena_ungdc_etl_web_to_aws_parent
from etl_deepsearch_pdf_parsing import omdena_ungdc_etl_pdf_parsing_parent


@flow(log_prints=True)
def omdena_ungdc_etl_main_flow(max_doc:int = None) -> None:
    """
    The base flow that sequentially calls the other scripts/flows.

    Parameters:
    - max_doc (int): The maximum number of documents to process

    Returns:
    None
    """

    print("Call Web to AWS-S3")
    omdena_ungdc_etl_web_to_aws_parent(max_doc)

    print("Call PDF parser")
    omdena_ungdc_etl_pdf_parsing_parent(max_doc)

    # Another source ?


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--max_doc', help="The max number of documents to process (for testing purpose)")
    args = parser.parse_args()

    max_doc = None
    if args.max_doc:
        max_doc = args.max_doc
        print(f"Max document to process: {max_doc}")

    omdena_ungdc_etl_main_flow(max_doc)
