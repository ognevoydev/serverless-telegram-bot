from telegram import Update
from telegram.ext import (ContextTypes, CommandHandler, ConversationHandler)
from ..service.localization import Loc


async def cancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Cancels the current operation.
    """
    text = Loc.get_message('CANCEL')
    await context.bot.send_message(chat_id=update.effective_chat.id, text=text)

    return ConversationHandler.END

cancel = CommandHandler('cancel', cancel_callback)
