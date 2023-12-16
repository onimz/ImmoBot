import logging
from time import sleep
import os
import sys
from collections import defaultdict

from dotenv import load_dotenv

from common.utils import timed
from common.utils import init_logger
from common.db import get_connection, get_filters, add_adverts, init_db
from crawlers.wg_gesucht_crawler import WgGesuchtCrawler
from crawlers.immo_scout_24_crawler import ImmoScout24Crawler

load_dotenv()
project_root = os.path.dirname(os.path.abspath(__file__))+"/../"
sys.path.append(project_root)


@timed
def crawl_websites_routine() -> None:
    logging.info("Start crawling")
    portale = {"wg-gesucht.de": WgGesuchtCrawler(),
               "immobilienscout24.de": ImmoScout24Crawler()}

    # Get all filters in db
    with get_connection() as con:
        filters = get_filters(con)

    # Group filters to users
    user_filters = defaultdict(list)
    for f in filters:
        user_filters[f.user_id].append(f)

    # Scrape user filters
    for user_id, filters in user_filters.items():
        user_adverts = []
        for f in filters:
            user_adverts += portale.get(f.domain).crawl(f.filter_url, f.id, user_id)
        with get_connection() as con:
            new_user_adverts = add_adverts(user_adverts, con)
            if len(new_user_adverts) > 0:
                logging.info(f"Found {len(new_user_adverts)} new adverts for user {user_id}")


if __name__ == '__main__':
    init_logger(path=f"{os.path.dirname(os.path.abspath(__file__))}/logs", level=logging.INFO)
    init_db()
    update_rate = int(os.getenv('UPDATE_RATE'))
    while True:
        crawl_websites_routine()
        sleep(update_rate)
