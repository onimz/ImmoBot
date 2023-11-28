import requests
from bs4 import BeautifulSoup
from datetime import datetime

from crawlers.crawler import Crawler
from common.models.advert import Advert

class WgGesuchtCrawler(Crawler):

    def crawl(self, filter_url, filter_id, user_id) -> list[Advert]:
        page = requests.get(filter_url)
        soup = BeautifulSoup(page.content, "html.parser")
        results = soup.find_all("div", class_="col-sm-8 card_body")
        # Find all offers on page one
        adverts = []
        for result in results:
            author = result.find("span", class_="ml5")
            is_ad = author is None or result.find("span", class_="label_verified ml5")

            if not is_ad:
                author = author.text.strip()
                title = result.find("a").text.strip()
                price = result.find("div", class_="col-xs-3").find("b").text.strip()
                url = "https://www.wg-gesucht.de" + result.find('a')['href']
                adverts.append(Advert(1, title, author, price, url, filter_id=filter_id, created_at=datetime.now(), user_id=user_id))
        return adverts
   