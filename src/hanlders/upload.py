import os.path
import tempfile
import time
import soundfile as sf

from telegram import Update
from telegram.ext import (ContextTypes, CommandHandler, MessageHandler, ConversationHandler, filters)

from ..constants import (Stage, State)
from ..repository.request_repository import RequestRepository
from ..repository.user_repository import UserRepository
from ..service_locator import ServiceLocator
from .cancel import cancel
from ..service.storage import Storage
from ..service.rest_client import RestClient
from ..service.localization import Loc

locator = ServiceLocator()

user_repository: UserRepository = locator.get('user_repository')

request_repository: RequestRepository = locator.get('request_repository')

file_storage: Storage = locator.get('file_storage')
rest_client: RestClient = locator.get('rest_client')


async def get_file_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Answers an audio file or voice message to analyze.
    """
    # Check if user exists in the database
    try:
        user = user_repository.get_by_account_id(account_id=update.effective_user.id)

        if user is None:
            text = Loc.get_message('UPLOAD_SIGN_UP')
            await context.bot.send_message(chat_id=update.effective_chat.id, text=text)

            return ConversationHandler.END

        analysis_requests = request_repository.get_by_user_id(user['id'])

        if len(analysis_requests) >= 5:
            text = Loc.get_message('FILE_LIMIT_REACHED')
            await context.bot.send_message(chat_id=update.effective_chat.id, text=text)

            return ConversationHandler.END

    except Exception as e:
        print(f"Error: '{e}' occurred")

    text = Loc.get_message('UPLOAD')
    await context.bot.send_message(chat_id=update.effective_chat.id, text=text)

    return State.UPLOAD.value


async def upload_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Uploads audio file into storage.
    """
    # Upload file into storage
    file_id = None

    if update.message.voice:
        file_id = update.message.voice.file_id
    elif update.message.audio:
        file_id = update.message.audio.file_id

    if file_id:
        file = await context.bot.get_file(file_id)

        if update.message.audio:
            filename = update.message.audio.file_name
        else:
            filename = os.path.basename(file.file_path)

        if not validate_file_ext(filename):
            text = Loc.get_message('FILE_TYPE_ERROR')
            await context.bot.send_message(chat_id=update.effective_chat.id, text=text)
            return State.UPLOAD.value

        if not validate_file_size(file.file_size):
            text = Loc.get_message('FILE_SIZE_ERROR')
            await context.bot.send_message(chat_id=update.effective_chat.id, text=text)
            return State.UPLOAD.value

        timestamp = str(int(time.time()))
        file_name, file_extension = os.path.splitext(filename)
        filename_with_timestamp = f"{file_name}_{timestamp}{file_extension}"

        filepath = tempfile.gettempdir() + '/' + filename_with_timestamp
        await file.download_to_drive(filepath)

        if not validate_channel_count(filepath):
            text = Loc.get_message('CHANNEL_COUNT_ERROR')
            await context.bot.send_message(chat_id=update.effective_chat.id, text=text)
            return State.UPLOAD.value

        file_storage.upload(filepath)

        # Get operationId from response
        operation_id = rest_client.upload_file(filename_with_timestamp, update.effective_user.id)

    # Find user in users table by telegram account id
    try:
        user = user_repository.get_by_account_id(account_id=update.effective_user.id)

        if user is not None:
            user_id = user['id']
        else:
            raise Exception('User not found')
    except Exception as e:
        print("Error: '{e}' occurred")

    # Create a row in the requests table
    try:
        result = request_repository.add({
            'user_id': user_id,
            'stage': Stage.PROCESS.value,
            'file_name': filename,
            'operation_id': operation_id
        })
        print('Request data saved to the database')
    except Exception as e:
        print(f"Error: '{e}' occurred")

    try:
        result
        text = Loc.get_message('UPLOAD_SUCCESS')
    except NameError:
        text = Loc.get_message('UPLOAD_ERROR')

    await context.bot.send_message(chat_id=update.effective_chat.id, text=text, parse_mode='markdown')

    return ConversationHandler.END


async def format_error_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Notifies about upload file format error.
    """
    text = Loc.get_message('FILE_FORMAT_ERROR')
    await context.bot.send_message(chat_id=update.effective_chat.id, text=text)

    return State.UPLOAD.value


def validate_file_ext(filename):
    """
    Validates upload file extension.
    """
    valid_extensions = ['.wav', '.ogg', '.mp3']
    file_extension = os.path.splitext(filename)[1].lower()
    return file_extension in valid_extensions


def validate_file_size(file_size):
    """
    Validates upload file size.
    """
    max_file_size_mb = 30 * 1000000
    return file_size < max_file_size_mb


def validate_channel_count(filepath):
    """
    Validates upload file channel count.
    """
    try:
        audio_file = sf.SoundFile(filepath)
        channels = audio_file.channels
        return channels >= 2
    except Exception as e:
        return False


upload = ConversationHandler(
    entry_points=[CommandHandler('upload', get_file_callback)],
    states={
        State.UPLOAD.value: [
            MessageHandler(filters.AUDIO | filters.VOICE, upload_callback),
            MessageHandler((filters.TEXT | filters.ATTACHMENT | filters.VIDEO) & ~filters.COMMAND,
                           format_error_callback)
        ],
    },
    fallbacks=[
        cancel
    ],
    name='upload',
    persistent=True
)
