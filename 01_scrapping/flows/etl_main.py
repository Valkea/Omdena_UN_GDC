#! /usr/bin/env python3

from prefect import flow
from etl_web_to_aws import omdena_ungdc_etl_web_to_aws_parent
from etl_deepsearch_pdf_parsing import omdena_ungdc_etl_pdf_parsing_parent


@flow(log_prints=True)
def omdena_ungdc_etl_main_flow() -> None:
    """
    The base flow that sequentially calls the other scripts / flows.
    """

    print("Call Web to AWS-S3")
    omdena_ungdc_etl_web_to_aws_parent()

    print("Call PDF parser")
    omdena_ungdc_etl_pdf_parsing_parent()

    # Another source ?


if __name__ == "__main__":
    omdena_ungdc_etl_main_flow()
