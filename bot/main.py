
import os
import logging
import sys
from dotenv import load_dotenv
load_dotenv()
project_root = os.path.dirname(os.path.abspath(__file__))+"/../"
sys.path.append(project_root)

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import filters, Application, MessageHandler, CommandHandler, ContextTypes
from common.utils import init_logger
from common.utils import exit_with_error
from notifier import Notifier
import strings as strings

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=strings.START
    )

async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    status = notifier.add_user(user.id, user.full_name)
    if status == 0:
        text = strings.REGISTER_FAILURE
    elif status == 1:
        text = strings.REGISTER_SUCCESS.format(user.full_name, ', '.join(notifier.portale))
    elif status == 2:
        text = strings.REGISTER_EXISTS
    
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text
    )

async def add_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        url = context.args[0]
        status = notifier.add_filter(url, update.effective_user.id)
        if status == 0:
            text = strings.NOT_REGISTERED
        elif status == 1:
            text = strings.ADD_SUCCESS
        elif status == 2:
            text = strings.ADD_FAILURE
    except IndexError:
        # FIXME NUR WENN SCHON REGISTRIERT IST ANZEIGEN
        text = strings.ADD_URL_MISSING
    
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text
    )

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=strings.COMMAND_NOT_FOUND)

async def polling_db(context: ContextTypes.DEFAULT_TYPE):
    new_adverts = notifier.check_for_new_adverts()
    for advert in new_adverts:
        text = f"[{advert.title} | {advert.price}]({advert.url})"
        await context.bot.send_message(chat_id=advert.user_id, text=text, parse_mode=ParseMode.MARKDOWN)
        
async def init_bot(context: ContextTypes.DEFAULT_TYPE):
    await context.bot.set_my_description("")
    await context.bot.set_my_short_description("Ich unterstütze Dich bei der Wohnungssuche.")
    await context.bot.set_my_commands([("add_filter", "Hinzufügen von Suchfiltern"), ("register", "Zum Registrieren")])
    

if __name__ == '__main__':
    init_logger(path=f"{os.path.dirname(os.path.abspath(__file__))}/logs", level=logging.INFO)

    notifier = Notifier()

    application = Application.builder().token(os.getenv('TELEGRAM_BOT_TOKEN')).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('register', register))
    application.add_handler(CommandHandler('add', add_filter))
    application.add_handler(MessageHandler(filters.COMMAND, unknown)) # This handler must be added last
    job_queue = application.job_queue
    job_init_bot_settings = job_queue.run_once(init_bot, when=1)
    job_scrape = job_queue.run_repeating(polling_db, interval=int(os.getenv('BOT_POLLING_RATE')), first=10)

    try:
        application.run_polling()
    except Exception as e:
        exit_with_error(f"Bot stopped with error: {e}")
