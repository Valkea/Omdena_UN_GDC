import os
import argparse
from prefect.blocks.system import JSON
from prefect_aws import AwsCredentials, S3Bucket

from dotenv import load_dotenv, find_dotenv

_ = load_dotenv(find_dotenv())  # read local .env file


def register_blocks():
    # --- Register AWS credential block

    credentials_block = AwsCredentials(
        aws_access_key_id=os.environ["AWS_ACCESS_KEY"],
        aws_secret_access_key=os.environ["AWS_SECRET_KEY"],
        aws_session_token=None,  # replace this with token if necessary
        region_name="eu-west-1",
    )
    credentials_block.save("omdena-un-gdc-creds", overwrite=True)

    # --- Register AWS-S3 bucket storage block

    bucket_block = S3Bucket(
        credentials=AwsCredentials.load("omdena-un-gdc-creds"),
        bucket_name="omdena-un-gdc-bucket",
    )
    bucket_block.save("omdena-un-gdc-bucket", overwrite=True)


if __name__ == "__main__":
    register_blocks()
