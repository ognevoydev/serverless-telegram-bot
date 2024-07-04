from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from telegram.ext import (ContextTypes, CommandHandler)
from ..service.localization import Loc


async def demo_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Provides demo call analysis result.
    """
    text = Loc.get_message('DEMO')

    keyboard = []
    row = []

    demo_url = ''

    button = InlineKeyboardButton('demo.mp3', web_app=WebAppInfo(
        url=demo_url))

    row.append(button)

    keyboard.append(row)

    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(chat_id=update.effective_chat.id, text=text, reply_markup=reply_markup)


demo = CommandHandler('demo', demo_callback)
