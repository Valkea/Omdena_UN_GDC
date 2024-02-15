import os
import argparse
import configparser

from prefect.blocks.system import JSON
from prefect.infrastructure.container import DockerContainer
from prefect_aws import AwsCredentials, S3Bucket

from dotenv import load_dotenv, find_dotenv

_ = load_dotenv(find_dotenv())  # read local .env file

config = configparser.ConfigParser()
config.read('config.cfg')


def register_blocks():

    # --- Register AWS credential block

    credentials_block = AwsCredentials(
        aws_access_key_id=os.environ["AWS_ACCESS_KEY"],
        aws_secret_access_key=os.environ["AWS_SECRET_KEY"],
        aws_session_token=None,  # replace this with token if necessary
        region_name=config['prefect.AWS']['region_name'],
    )
    credentials_block.save("omdena-un-gdc-creds", overwrite=True)

    # --- Register AWS-S3 bucket storage block

    bucket_block = S3Bucket(
        credentials=AwsCredentials.load("omdena-un-gdc-creds"),
        bucket_name=config['prefect.AWS']['bucket_name'],
    )
    bucket_block.save("omdena-un-gdc-bucket", overwrite=True)

    # --- Register Docker block
    docker_block = DockerContainer(
        # env={"EXTRA_PIP_PACKAGES": "s3fs prefect==2.14.12 pydantic==1.10.11 prefect-aws[S3]==0.4.6},
        env={"WEAVIATE_URL":"http://weaviate:8080"},
        networks=["prefect-network"],
        # image_registry="",
        image=config['prefect.Docker']['flows_image'],
        image_pull_policy='ALWAYS' # 'ALWAYS', 'NEVER', 'IF_NOT_PRESENT'

    )
    docker_block.save("omdena-un-gdc-docker", overwrite=True)


if __name__ == "__main__":
    register_blocks()
