from telegram import Update
from telegram.ext import (ContextTypes, CommandHandler)
from ..service.localization import Loc


async def contact_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Provides contact data.
    """
    text = Loc.get_message('CONTACT')
    await context.bot.send_message(chat_id=update.effective_chat.id, text=text)


contact = CommandHandler('contact', contact_callback)
