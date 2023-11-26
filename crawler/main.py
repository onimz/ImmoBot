import logging
from time import sleep
import os
import sys
project_root = os.path.dirname(os.path.abspath(__file__))+"/../"
sys.path.append(project_root)

from common.utils import timed
from common.utils import init_logger
from common.models.advert import Advert
from common.db import get_connection, get_filters, add_adverts
from crawlers.wg_gesucht_crawler import WgGesuchtCrawler
from crawlers.immo_scout_24_crawler import ImmoScout24Crawler

@timed
def crawl_websites_routine() -> list[Advert]:
    init_logger(level=logging.INFO)

    portale = {"wg-gesucht.de": WgGesuchtCrawler(), 
               "immobilienscout24.de": ImmoScout24Crawler()}

    logging.info("Start crawling")

    # Group user filters
    with get_connection() as con:
        filters = get_filters(con)
    filter_dict = {}
    for f in filters:
        if f.user_id not in filter_dict:
            filter_dict[f.user_id] = [f]
        else:
            filter_dict[f.user_id].append(f)

    # Scrape user filters
    advert_dict = {}
    for user_id, filters in filter_dict.items():
        user_adverts = []
        for f in filters:
            user_adverts += portale.get(f.domain).crawl(f.filter_url, f.id, user_id)
        with get_connection() as con:
            new_user_adverts = add_adverts(user_adverts, con)
            if len(new_user_adverts) > 0:
                advert_dict[user_id] = new_user_adverts
                logging.info(f"Found {len(new_user_adverts)} new adverts for user {user_id}")
        

    return advert_dict

if __name__ == '__main__':
    update_rate = int(os.getenv('UPDATE_RATE'))
    while True:
        crawl_websites_routine()
        sleep(update_rate)