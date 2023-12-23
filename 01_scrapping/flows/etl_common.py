from prefect import flow, task
from prefect_aws import S3Bucket
# from prefect.tasks import task_input_hash

@task(
    name="Read Data from AWS-S3",
    log_prints=True,
    # cache_key_fn=task_input_hash,
    # cache_expiration=timedelta(days=1),
)
def read_AWS(remote_path: str, local_path: str, bucket_block: S3Bucket) -> None:
    """Download a remote AWS-S3 file to local folder"""

    try:
        print("Download from S3:", remote_path, ">", local_path)
        bucket_block.download_object_to_path(from_path=str(remote_path), to_path=str(local_path))

    except Exception as e:
        print(e, remote_path)


@task(
    name="Write Data on AWS-S3",
    log_prints=True,
    # cache_key_fn=task_input_hash,
    # cache_expiration=timedelta(days=1),
)
def write_AWS(local_path: str, remote_path: str, bucket_block: S3Bucket) -> None:
    """Upload a local file to AWS-S3"""

    try:
        print("Upload to S3:", local_path, ">", remote_path)
        bucket_block.upload_from_path(from_path=str(local_path), to_path=str(remote_path))

    except Exception as e:
        print(e, local_path)
