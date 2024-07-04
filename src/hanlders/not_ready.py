from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (ContextTypes, CallbackQueryHandler)

from ..constants import State
from ..service.localization import Loc


async def not_ready_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Returns a file not ready message.
    """
    query = update.callback_query

    await query.answer()

    text = Loc.get_message('FILE_NOT_READY')

    keyboard = [
        [InlineKeyboardButton('Назад к списку', callback_data=State.BACK_TO_LIST.value)],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(text=text, reply_markup=reply_markup)


not_ready = CallbackQueryHandler(not_ready_callback, pattern='^' + 'not_ready' + '$')
