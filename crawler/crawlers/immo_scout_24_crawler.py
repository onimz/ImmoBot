import requests
from bs4 import BeautifulSoup

from crawlers.crawler import Crawler
from common.models.advert import Advert

class ImmoScout24Crawler(Crawler):
    
    def crawl(self, filter_url) -> list[Advert]:
        return []
   