import os
from dotenv import load_dotenv
import logging

from telegram import Update
from telegram.ext import filters, Application, MessageHandler, CommandHandler, ContextTypes

from src.utils import init_logger
from src.utils import exit_with_error
from src.notifier import Notifier
import src.strings as strings

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
        text = strings.REGISTER_SUCCESS.format(user.full_name, ', '.join(notifier.portale.keys()))
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

async def list_adverts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"{notifier.get_advert_list()}"
    )

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=strings.COMMAND_NOT_FOUND)

async def scrape(context: ContextTypes.DEFAULT_TYPE):
    advert_dict = notifier.crawl_websites_routine()
    if len(advert_dict) <= 0:
        return
    nl = '\n\n'
    for user_id, ads in advert_dict.items():
        await context.bot.send_message(chat_id=user_id, text=f"{len(ads)} neue Annoncen wurden gefunden:"\
                                                              f"\n\n{(nl).join([ad.url for ad in ads])}")
        
async def init_bot(context: ContextTypes.DEFAULT_TYPE):
    await context.bot.set_my_description("")
    await context.bot.set_my_short_description("Ich unterstüze Dich bei der Wohnungssuche.")
    await context.bot.set_my_commands([("add_filter", "Hinzufügen von Suchfiltern"), ("register", "Zum Registrieren")])
    

if __name__ == '__main__':
    load_dotenv()
    init_logger(level=logging.INFO)

    notifier = Notifier()

    application = Application.builder().token(os.getenv('TELEGRAM_BOT_TOKEN')).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('register', register))
    application.add_handler(CommandHandler('add', add_filter))
    # application.add_handler(CommandHandler('list', list_adverts))
    application.add_handler(MessageHandler(filters.COMMAND, unknown)) # This handler must be added last
    job_queue = application.job_queue
    job_init_bot_settings = job_queue.run_once(init_bot, when=1)
    job_scrape = job_queue.run_repeating(scrape, interval=notifier.update_rate, first=10)

    try:
        application.run_polling()
    except Exception as e:
        exit_with_error(f"Bot stopped with error: {e}")
