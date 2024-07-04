from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import (ContextTypes, CommandHandler, CallbackQueryHandler)

from ..constants import (State, Stage, Emoji)
from ..repository.request_repository import RequestRepository
from ..repository.user_repository import UserRepository
from ..service_locator import ServiceLocator
from ..service.localization import Loc

locator = ServiceLocator()

user_repository: UserRepository = locator.get('user_repository')

request_repository: RequestRepository = locator.get('request_repository')


async def myfiles_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Returns a list of uploaded files.
    """
    query = update.callback_query

    if query is not None:
        await query.answer()

    # Check if user exists in the database
    try:
        user = user_repository.get_by_account_id(account_id=update.effective_user.id)

        if user is None:
            text = Loc.get_message('FILE_LIST_SIGN_UP')
            await context.bot.send_message(chat_id=update.effective_chat.id, text=text)
            return
    except Exception as e:
        print(f"Error: '{e}' occurred")

    user_id = user['id']

    # Get user's requests
    try:
        analysis_requests = request_repository.get_by_user_id(user_id)
    except Exception as e:
        print(f"Error: '{e}' occurred")
        return

    # Create keyboard markup
    keyboard = []
    row = []
    button = None

    for request in analysis_requests:

        if request['file_name'] is not None and request['operation_id'] is not None:

            if request['stage'] == Stage.SUCCESS.value:
                button_caption = Emoji.CHECK.value + ' ' + request['file_name']

                result_url = ''

                button = InlineKeyboardButton(button_caption, web_app=WebAppInfo(
                    url=f"{result_url}?file_id=" + request['operation_id']))
            else:
                button_caption = Emoji.WAIT.value + ' ' + request['file_name']

                button = InlineKeyboardButton(button_caption, callback_data='not_ready')

            row.append(button)

        keyboard.append(row)
        row = []

    reply_markup = InlineKeyboardMarkup(keyboard)

    if button is not None:
        text = Loc.get_message('FILE_LIST', {
            '#EMOJI_WAIT#': Emoji.WAIT.value,
            '#EMOJI_CHECK#': Emoji.CHECK.value
        })
    else:
        text = Loc.get_message('FILE_LIST_EMPTY')

    if query is not None:
        try:
            await query.edit_message_text(text=text, reply_markup=reply_markup)
        except:
            return
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text,
                                       reply_markup=reply_markup)


my_files = CommandHandler('myfiles', myfiles_callback)
back_to_list = CallbackQueryHandler(myfiles_callback, pattern='^' + State.BACK_TO_LIST.value + '$')
