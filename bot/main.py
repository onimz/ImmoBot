
import os
import logging
import sys
import pytz
from queue import Queue
from urllib.parse import urlparse

from dotenv import load_dotenv
load_dotenv()
project_root = os.path.dirname(os.path.abspath(__file__))+"/../"
sys.path.append(project_root)
from telegram import (
    Update, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    ReplyKeyboardMarkup
)
from telegram.ext import (
    filters, 
    Application, 
    MessageHandler, 
    CommandHandler, 
    ContextTypes, 
    Defaults, 
    CallbackQueryHandler,
    ConversationHandler
)
from telegram.constants import ParseMode

from common.utils import init_logger
from common.utils import exit_with_error
from notifier import Notifier
import strings as strings


# Stages
START_ROUTES, END_ROUTES = range(2)
# Callback data
ONE, TWO, THREE, FOUR = range(4)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_markup = ReplyKeyboardMarkup([[InlineKeyboardButton(text="Register", callback_data="register")],
                                        [InlineKeyboardButton(text="Help", callback_data="Help")]],
                                       resize_keyboard=True)

    await update.message.reply_text(text="Options: ", reply_markup=reply_markup)


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

    await update.message.reply_text(text)


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

    await update.message.reply_text(text)


async def show_filters(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    filters = notifier.get_user_filters(update.effective_user.id)
    if not filters:
        await update.message.reply_text("Du hast noch keine Suchfilter. Füge erst welche mit /add hinzu.")
        return

    grouped_filters = {}
    for filter in filters:
        key = filter.domain
        if key not in grouped_filters:
            grouped_filters[key] = []
        grouped_filters[key].append(filter)

    keyboard = []
    for domain, values in grouped_filters.items():
        keyboard.append([InlineKeyboardButton(text=f"🌐 {domain}", url=domain)])

        for value in values:
            formatted_url_string = urlparse(value.filter_url).path
            keyboard.append([InlineKeyboardButton(text=f"👉 {formatted_url_string[:28]}..", url=value.filter_url)])
            keyboard.append([InlineKeyboardButton(text="🗑️", callback_data=f'DELETE_FILTER {value.id}')])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("Deine Suchfilter:", reply_markup=reply_markup)


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    data = query.data.split(' ')

    match data[0]:
        case 'DELETE_FILTER':
            notifier.delete_filter(filter_id=data[1])
            # await query.edit_message_text(text="Start handler, Choose a route", reply_markup=reply_markup)
            pass
        case _:
            logging.warning(
                f"Something unexpected happened in button callback routine with callback data: {query.data}")

    # CallbackQueries need to be answered, even if no notification to the user is needed
    await query.answer()

    # await query.edit_message_text(text=f"Selected option: {query.data}")


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(strings.COMMAND_NOT_FOUND)


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
    await context.bot.set_my_commands([("add_filter", "Hinzufügen von Suchfiltern"),
                                       ("show", "Anzeigen und Bearbeiten von Suchfiltern und Annoncen"),
                                       ("register", "Zum Registrieren")])


if __name__ == '__main__':
    init_logger(path=f"{os.path.dirname(os.path.abspath(__file__))}/logs", level=logging.INFO)
    logging.getLogger('httpx').setLevel(logging.WARNING)
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

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("show_filters", show_filters)],
        states={
            START_ROUTES: [
                CallbackQueryHandler(show_filters, pattern="^" + str(ONE) + "$"),
                """CallbackQueryHandler(two, pattern="^" + str(TWO) + "$"),
                CallbackQueryHandler(three, pattern="^" + str(THREE) + "$"),
                CallbackQueryHandler(four, pattern="^" + str(FOUR) + "$"),"""
            ],
            END_ROUTES: [
                CallbackQueryHandler(start, pattern="^" + str(ONE) + "$"),
                """ CallbackQueryHandler(start_over, pattern="^" + str(ONE) + "$"),
                CallbackQueryHandler(end, pattern="^" + str(TWO) + "$"),"""
            ],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    # Add ConversationHandler to application that will be used for handling updates
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('register', register))
    application.add_handler(CommandHandler('add', add_filter))
    application.add_handler(CommandHandler('show', show_filters))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.COMMAND, unknown)) # must be added last
    job_queue = application.job_queue
    job_init_bot_settings = job_queue.run_once(init_bot, when=1)
    job_scrape = job_queue.run_repeating(polling_db, interval=int(os.getenv('BOT_POLLING_RATE')), first=10)

    try:
        application.run_polling()
    except Exception as e:
        exit_with_error(f"Bot stopped with error: {e}")
