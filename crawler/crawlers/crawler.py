from common.models.advert import Advert
from common.models.filter import Filter
import requests


class Crawler:
    MAX_AD_SIZE = 20

    def __init__(self) -> None:
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
        }

    def request(self, url: str, headers=None, timeout=3):
        headers = headers if headers else self.headers
        return requests.get(url, headers=headers, timeout=timeout)

    def crawl(self, filter: Filter) -> list[Advert]:
        raise NotImplementedError("Subclasses must implement the crawl method")
