import requests
from bs4 import BeautifulSoup

from src.crawlers.crawler import Crawler
from src.models.advert import Advert

class ImmoScout24Crawler(Crawler):
    
    def crawl(self, filter_url) -> list[Advert]:
        return []
   