import os

import boto3

from .storage import Storage


class S3Storage(Storage):
    """
    S3 storage service class.
    """

    def __init__(self, bucket, credentials=None):
        """
        Initializes the S3 object.
        """
        self.bucket = bucket
        self.credentials = credentials

        session = boto3.session.Session()

        session_params = {
            "service_name": 's3',
            "endpoint_url": 'https://storage.yandexcloud.net',
        }

        if credentials is not None:
            session_params['aws_access_key_id'] = credentials['access_key']
            session_params['aws_secret_access_key'] = credentials['secret_key']
            session_params['region_name'] = credentials['region_name']

        self.s3 = session.client(**session_params)

    def upload(self, filename):
        """
        Uploads a file to the bucket.
        """
        self.s3.upload_file(filename, self.bucket, f'input/{os.path.basename(filename)}')
