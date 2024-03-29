import os
from datetime import datetime

import tldextract

from common.db import (
    init_db, get_connection,
    get_adverts,
    add_user,
    get_filters,
    add_filter,
    delete_filter,
    is_user_registered,
    get_latest_poll_timestamp,
    update_latest_poll_timestamp)
from common.models.filter import Filter
from common.models.advert import Advert
from common.utils import exit_with_error
from common.portals import get_portal_domains


class Notifier:
    def __init__(self):
        init_db()
        self.portals = get_portal_domains()
        try:
            self.user_limit = int(os.getenv('USER_LIMIT'))
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
            if domain not in self.portals:
                return 2
            add_filter(domain, filter_url, user_id, con)
            return 1

    def get_user_filters(self, user_id) -> list[Filter]:
        with get_connection() as con:
            return get_filters(con, user_id=user_id)

    def delete_filter(self, filter_id) -> int:
        with get_connection() as con:
            delete_filter(con, filter_id)

    """def get_advert_list(self) -> list[Advert]:
        with get_connection() as con:
            adverts = get_adverts(con)
            result = ""
            for advert in adverts:
                result += f"{str(advert.url)}\n"
            return result"""

    def get_new_adverts(self) -> list[Advert]:
        with get_connection() as con:
            new_timestamp = datetime.now()
            latest_poll = get_latest_poll_timestamp(con)
            new_adverts = get_adverts(con, latest_poll)
            update_latest_poll_timestamp(new_timestamp, con)
            return new_adverts
