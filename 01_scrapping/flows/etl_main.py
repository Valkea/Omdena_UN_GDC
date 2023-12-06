#! /usr/bin/env python3

from prefect import flow
from etl_web_to_aws import omdena_ungdc_etl_web_to_aws_parent


@flow(log_prints=True)
def omdena_ungdc_etl_main_flow() -> None:
    """
    The base flow that sequentially calls the other scripts / flows.

    (I could merge both script into one single script, but I prefer
    to keep them separated as an example of the possibilites for
    incoming projects...)
    """

    print("Call Web to AWS-S3")
    omdena_ungdc_etl_web_to_aws_parent()
    # print("Call GCS2BQ")
    # etl_gcs_to_bq_parent()


if __name__ == "__main__":
    omdena_ungdc_etl_main_flow()
