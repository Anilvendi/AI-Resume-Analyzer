import os
from aws.aws_config import s3_client

S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")


def upload_resume(file, user_id):

    file_key = f"users/{user_id}/{file.name}"

    s3_client.upload_fileobj(
        file,
        S3_BUCKET_NAME,
        file_key
    )

    return True