import logging
import os

import tldextract

from src.db import init_db, get_connection, add_adverts, get_adverts, add_user, add_filter, get_filters, is_user_registered
from src.utils import exit_with_error
from src.utils import timed
from src.models.advert import Advert
from src.crawlers.wg_gesucht_crawler import WgGesuchtCrawler
from src.crawlers.immo_scout_24_crawler import ImmoScout24Crawler


class Notifier:
    def __init__(self):
        init_db()
        self.portale = {"wg-gesucht.de": WgGesuchtCrawler(), 
                        "immobilienscout24.de": ImmoScout24Crawler()}
        try:
            self.user_limit = int(os.getenv('user_limit'))
            self.update_rate = int(os.getenv('update_rate'))
        except ValueError as e:
            exit_with_error(f"Couldn't parse .env value to int: {e}")
        except Exception as e:
            exit_with_error(f"Unexpected error while reading in env values: {e}")
    
    def add_user(self, user_id, user_name) -> int:
        """
        0: limit reached,
        1: user added,
        2: user already added
        """
        with get_connection() as con:
            return add_user(user_id, user_name, self.user_limit, con)
    
    def add_filter(self, filter_url, user_id) -> int:
        """
        0: not registered,
        1: filter added,
        2: faulty filter url
        """
        with get_connection() as con:
            if not is_user_registered(user_id, con):
                return 0
            domain = tldextract.extract(filter_url).registered_domain
            if domain not in self.portale.keys():
                return 2
            add_filter(domain, filter_url, user_id, con)
            return 1

    def get_advert_list(self):
        with get_connection() as con:
            adverts = get_adverts(con)
            result = ""
            for advert in adverts:
                result += f"{str(advert.url)}\n"
            return result

    @timed
    def crawl_websites_routine(self) -> list[Advert]:
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
                user_adverts += self.portale.get(f.domain).crawl(f.filter_url, f.id, user_id)
            with get_connection() as con:
                new_user_adverts = add_adverts(user_adverts, con)
                if len(new_user_adverts) > 0:
                    advert_dict[user_id] = new_user_adverts
                    logging.info(f"Found {len(new_user_adverts)} new adverts for user {user_id}")
            

        return advert_dict
