from bs4 import BeautifulSoup
from datetime import datetime

from crawler.crawlers.crawler import Crawler
from common.models.advert import Advert
from common.models.filter import Filter

# https://www.wg-gesucht.de/1-zimmer-wohnungen-und-wohnungen-in-Hannover.57.1+2.1.0.html?offer_filter=1&city_id=57&sort_column=0&sort_order=0&noDeact=1&categories%5B%5D=1&categories%5B%5D=2&sMin=46&rMax=750


class WgGesuchtCrawler(Crawler):

    def crawl(self, filter: Filter) -> list[Advert]:
        page = self.request(url=filter.filter_url)
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
                adverts.append(
                    Advert(
                        None,
                        title,
                        author,
                        price,
                        url,
                        filter_id=filter.id,
                        created_at=datetime.now(),
                        user_id=filter.user_id
                    )
                )
        return adverts
