
import os
import logging
import sys
import pytz
from queue import Queue

from dotenv import load_dotenv
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import filters, Application, MessageHandler, CommandHandler, ContextTypes, Defaults

from common.utils import init_logger
from common.utils import exit_with_error
from notifier import Notifier
import strings as strings

load_dotenv()
project_root = os.path.dirname(os.path.abspath(__file__))+"/../"
sys.path.append(project_root)


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
        text = strings.REGISTER_SUCCESS.format(
            user.full_name, ', '.join(notifier.portale))
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


async def list_filters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Not implemented."
    )


async def delete_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Not implemented."
    )


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=strings.COMMAND_NOT_FOUND)


async def _send_out_adverts(adverts, context):
    for advert in adverts:
        text = f"[{advert.title} | {advert.price}]({advert.url})"
        await context.bot.send_message(chat_id=advert.user_id, text=text)


async def polling_db(context: ContextTypes.DEFAULT_TYPE):
    """ Retrieve new ads from the database 
        for all users and deliver them 
    """
    new_adverts = notifier.get_new_adverts()
    outgoing = []

    if queue_outgoing.empty():
        outgoing += new_adverts[:MAX_SENDS]
        for element in new_adverts[MAX_SENDS:]:
            queue_outgoing.put(element)
    else:
        diff = MAX_SENDS - queue_outgoing.qsize()

        if diff < 0:
            for ad in new_adverts:
                queue_outgoing.put(ad)
            for _ in range(MAX_SENDS):
                outgoing.append(queue_outgoing.get())
        elif diff > 0:
            while not queue_outgoing.empty():
                outgoing.append(queue_outgoing.get())
            outgoing += new_adverts[:diff]
            for element in new_adverts[diff:]:
                queue_outgoing.put(element)

    await _send_out_adverts(outgoing, context)


async def init_bot(context: ContextTypes.DEFAULT_TYPE):
    await context.bot.set_my_description("")
    await context.bot.set_my_short_description(strings.BOT_SHORT_DESCRIPTION)
    await context.bot.set_my_commands([("add", "Hinzufügen von Suchfiltern"),
                                       ("list", "Anzeigen von Suchfiltern"),
                                       ("delete", "Löschen von Suchfiltern"),
                                       ("register", "Zum Registrieren")])


if __name__ == '__main__':
    init_logger(path=f"{os.path.dirname(os.path.abspath(__file__))}/logs", level=logging.INFO)
    logging.getLogger('httpx').setLevel(logging.INFO)
    logging.getLogger('apscheduler').setLevel(logging.WARNING)

    # For rate limiting
    # API got a limitation of sending up to 30 messages per second
    # MAX_SENDS sets max threshold for new advert messages
    # The rest are reserved for user interaction
    MAX_SENDS = 22
    queue_outgoing = Queue()

    notifier = Notifier()
    defaults = Defaults(parse_mode=ParseMode.MARKDOWN,
                        tzinfo=pytz.timezone('Europe/Berlin'))

    application = Application   \
        .builder()  \
        .token(os.getenv('TELEGRAM_BOT_TOKEN')) \
        .defaults(defaults) \
        .build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('register', register))
    application.add_handler(CommandHandler('add', add_filter))
    application.add_handler(CommandHandler('list', list_filters))
    application.add_handler(CommandHandler('delete', delete_filter))
    # This handler must be added last
    application.add_handler(MessageHandler(filters.COMMAND, unknown))
    job_queue = application.job_queue
    job_init_bot_settings = job_queue.run_once(init_bot, when=1)
    job_scrape = job_queue.run_repeating(polling_db, interval=int(os.getenv('BOT_POLLING_RATE')), first=10)

    try:
        application.run_polling()
    except Exception as e:
        exit_with_error(f"Bot stopped with error: {e}")
