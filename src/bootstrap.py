import logging
import os

import ydb
from dotenv import load_dotenv

from .database.yandex_database import YandexDatabase
from .repository.request_repository import RequestRepository
from .repository.user_repository import UserRepository
from .service.s3_storage import S3Storage
from .service.rest_client import RestClient
from .service_locator import ServiceLocator
from .service.localization import Loc


def load():
    # Enable logging
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
    )

    # Load .env variables
    load_dotenv()

    # Configure service locator
    config = {
        'user_repository': {
            'className': UserRepository,
            'constructorParams': [YandexDatabase({
                'endpoint': os.getenv('YDB_ENDPOINT'),
                'database': os.getenv('YDB_DATABASE'),
                'credentials': ydb.iam.MetadataUrlCredentials(),
            }, 'users')]
        },
        'request_repository': {
            'className': RequestRepository,
            'constructorParams': [YandexDatabase({
                'endpoint': os.getenv('YDB_ENDPOINT'),
                'database': os.getenv('YDB_DATABASE'),
                'credentials': ydb.iam.MetadataUrlCredentials(),
            }, 'requests')]
        },
        'file_storage': {
            'className': S3Storage,
            'constructorParams': [
                os.getenv('API_S3_BUCKET'),
                {
                    'access_key': os.getenv('API_S3_ACCESS_KEY'),
                    'secret_key': os.getenv('API_S3_SECRET_KEY'),
                    'region_name': 'ru-central1'
                }
            ]
        },
        'rest_client': {
            'className': RestClient,
            'constructorParams': [
                os.getenv('API_URL'),
                os.getenv('API_TOKEN')
            ]
        },
    }

    locator = ServiceLocator()
    locator.register_by_config(config)

    Loc.load_messages()
