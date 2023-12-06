import argparse
from prefect.blocks.system import JSON
from prefect_aws import AwsCredentials, S3Bucket
# from prefect_gcp import GcpCredentials
# from prefect_gcp.cloud_storage import GcsBucket
# from prefect_gcp.bigquery import BigQueryWarehouse


def register_blocks(cred_path, project_id):

    # --- Register some variables

    json_block = JSON(value={"project_id": project_id})
    json_block.save(name="omdena-un-gdc-variables", overwrite=True)

    # --- Register AWS credential block

    # credentials_block = GcpCredentials(service_account_file=cred_path)
    credentials_block = AwsCredentials(
    	aws_access_key_id="AKIA3YFNWW7FYFLMEI5R",
    	aws_secret_access_key="C/Ad+sdCX1+8JZzOjdwVtX7hfdBzG8Vl1WNXMbyr",
    	aws_session_token=None,  # replace this with token if necessary
    	region_name="eu-west-1"
    )
    credentials_block.save("omdena-un-gdc-creds", overwrite=True)

    # --- Register AWS-S3 bucket storage block

    # bucket_block = GcsBucket(
    #     gcp_credentials=GcpCredentials.load("omdena-un-gdc-creds"),
    #     bucket="omdena-un-gdc-bucket",
    # )
    bucket_block = S3Bucket(
        bucket_name="omdena-un-gdc-bucket",
        aws_credentials=AwsCredentials.load("omdena-un-gdc-creds")
    )
    bucket_block.save("omdena-un-gdc-bucket", overwrite=True)

    # --- Register GCP BigQuery block

    # bq_block = BigQueryWarehouse(
    #     gcp_credentials=GcpCredentials.load("eco2mix-de-project-creds"),
    #     fetch_size=1
    # )
    # bq_block.save("eco2mix-de-project-bigquery", overwrite=True)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    # parser.add_argument('cred_path', type=str, help="The path to the GCP credential JSON")
    parser.add_argument('project_id', type=str, help="The AWS project id")
    args = parser.parse_args()

    args.cred_path = "xxx" # TMP !
    register_blocks(args.cred_path, args.project_id)

    j = JSON.load("omdena-un-gdc-variables")
    print("TEST:", j)
    print("TEST:", j.value['project_id'])
