import asyncio
import json
import os
from pathlib import Path

from telegram import BotCommand, Update
from telegram.ext import (ApplicationBuilder, Application, PicklePersistence)
from src.service.s3_persistence import S3Persistence

from src import bootstrap


async def set_commands(application: Application):
    """
    Initializes a bot commands list.
    """
    await application.bot.set_my_commands(
        [
            BotCommand('upload', 'загрузить файл'),
            BotCommand('myfiles', 'список загруженных файлов'),
            BotCommand('contact', 'связаться с нами'),
            BotCommand('help', 'больше информации о боте'),
            BotCommand('demo', 'анализ демо-записи'),
            BotCommand('cancel', 'отменить текущую операцию'),
        ]
    )


def cloud_handler(event, context):
    return asyncio.run(cloud_run(event, context))


async def cloud_run(event, context):
    bootstrap.load()
    from src.hanlders import all_handlers

    persistence = S3Persistence(filepath=Path('persistence'), update_interval=1)

    application = ApplicationBuilder().token(os.getenv('TOKEN')).persistence(persistence).build()

    for handler in all_handlers:
        application.add_handler(handler)

    await application.initialize()
    await set_commands(application)

    async with application:
        await application.process_update(
            Update.de_json(json.loads(event["body"]), application.bot)
        )

    return {
        'statusCode': 200,
        'body': 'Success'
    }
