import os
import argparse
from prefect.blocks.system import JSON
from prefect_aws import AwsCredentials, S3Bucket
# from prefect_gcp import GcpCredentials
# from prefect_gcp.cloud_storage import GcsBucket
# from prefect_gcp.bigquery import BigQueryWarehouse

from dotenv import load_dotenv, find_dotenv

_ = load_dotenv(find_dotenv())  # read local .env file


def register_blocks(project_id):

    # --- Register some variables

    json_block = JSON(value={"project_id": project_id})
    json_block.save(name="omdena-un-gdc-variables", overwrite=True)

    # --- Register AWS credential block

    credentials_block = AwsCredentials(
        aws_access_key_id=os.environ["AWS_ACCESS_KEY"],
        aws_secret_access_key=os.environ["AWS_SECRET_KEY"],
        aws_session_token=None,  # replace this with token if necessary
        region_name="eu-west-1"
    )
    credentials_block.save("omdena-un-gdc-creds", overwrite=True)

    # --- Register AWS-S3 bucket storage block

    bucket_block = S3Bucket(
        bucket_name="omdena-un-gdc-bucket",
        aws_credentials=AwsCredentials.load("omdena-un-gdc-creds")
    )
    bucket_block.save("omdena-un-gdc-bucket", overwrite=True)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('project_id', type=str, help="The AWS project id")
    args = parser.parse_args()

    register_blocks(args.project_id)

    # j = JSON.load("omdena-un-gdc-variables")
    # print("TEST:", j)
    # print("TEST:", j.value['project_id'])
