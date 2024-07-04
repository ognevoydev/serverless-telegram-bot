from telegram import Update
from telegram.ext import (ContextTypes, CommandHandler)
from ..service.localization import Loc


async def help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Provides help data.
    """
    text = (Loc.get_message('HELP'))
    await context.bot.send_message(chat_id=update.effective_chat.id, text=text)


help = CommandHandler('help', help_callback)
