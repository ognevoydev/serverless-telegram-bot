from telegram import Update
from telegram.ext import (ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters)

from .cancel import cancel
from ..constants import State
from ..repository.user_repository import UserRepository
from ..service_locator import ServiceLocator
from ..service.localization import Loc

locator = ServiceLocator()

user_repository: UserRepository = locator.get('user_repository')


async def name_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Starts conversation for user sign up.
    """
    # Check if user exists in the database
    try:
        user = user_repository.get_by_account_id(account_id=update.effective_user.id)

        if user is not None:
            text = (Loc.get_message('SIGN_IN'))
            await context.bot.send_message(chat_id=update.effective_chat.id, text=text)
            return ConversationHandler.END

    except Exception as e:
        print(f"Error: '{e}' occurred")

    text = (Loc.get_message('SIGN_UP_NAME'))
    await context.bot.send_message(chat_id=update.effective_chat.id, text=text, parse_mode='markdown')

    return State.PHONE.value


async def phone_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Answers a username.
    """
    text = Loc.get_message('SIGN_UP_PHONE')

    context.user_data['name'] = update.message.text

    await context.bot.send_message(chat_id=update.effective_chat.id, text=text)

    return State.SIGN_UP.value


async def signup_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Answers a user phone.
    """

    context.user_data['phone'] = update.message.text

    user_id = None

    # Save user data to the database
    try:
        user_id = user_repository.add({
            'account_id': update.effective_user.id,
            'chat_id': update.effective_chat.id,
            'name': context.user_data['name'],
            'phone': context.user_data['phone'],
        })
        print('User data saved to the database')
    except Exception as e:
        print(f"Error: '{e}' occurred")

    if user_id is not None:
        text = Loc.get_message('SIGN_UP_SUCCESS')
    else:
        text = Loc.get_message('SIGN_UP_ERROR')

    await context.bot.send_message(chat_id=update.effective_chat.id, text=text)

    return ConversationHandler.END


sign_up = ConversationHandler(
    entry_points=[CommandHandler('start', name_callback)],
    states={
        State.PHONE.value: [MessageHandler(filters.TEXT & ~filters.COMMAND, phone_callback)],
        State.SIGN_UP.value: [MessageHandler(filters.TEXT & ~filters.COMMAND, signup_callback)],
    },
    fallbacks=[
        cancel
    ],
    name='sign_up',
    persistent=True
)
