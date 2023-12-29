import logging
from time import sleep
import os
import sys
from queue import Queue, Empty
import threading

from dotenv import load_dotenv
load_dotenv()
project_root = os.path.dirname(os.path.abspath(__file__))+"/../"
sys.path.append(project_root)

from common.utils import timed
from common.utils import init_logger
from common.db import (
    get_connection, 
    get_filters, 
    add_adverts, 
    init_db
)
from common.models.filter import Filter
from crawlers.wg_gesucht_crawler import WgGesuchtCrawler
from crawlers.immowelt_crawler import ImmoweltCrawler


def process_filter(thread_num: int, filter: Filter) -> None:
    portale = {"wg-gesucht.de": WgGesuchtCrawler(),
               "immowelt.de": ImmoweltCrawler()}

    user_adverts = portale.get(filter.domain).crawl(filter)
    with get_connection() as con:
        add_adverts(user_adverts, con)
    print(f"Thread {thread_num}: Processing filter with id {filter.id}")


@timed
def crawl_websites_routine() -> None:
    logging.info("Start crawling")

    # Get all filters from db
    with get_connection() as con:
        filters = get_filters(con)

    filter_queue = Queue()

    for filter in filters:
        filter_queue.put(filter)

    threads = []

    def thread_worker(thread_num):
        while True:
            try:
                filter = filter_queue.get(timeout=0.01)
            except Empty:
                # Queue is empty, thread can exit
                break
            else:
                process_filter(thread_num, filter)

    for i in range(THREADS):
        thread = threading.Thread(target=thread_worker, args=(i+1,))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()


if __name__ == '__main__':
    init_logger(path=f"{os.path.dirname(os.path.abspath(__file__))}/logs", level=logging.INFO)
    init_db()
    UPDATE_RATE = int(os.getenv('UPDATE_RATE'))
    THREADS = int(os.getenv('THREADS'))
    while True:
        crawl_websites_routine()
        sleep(UPDATE_RATE)
