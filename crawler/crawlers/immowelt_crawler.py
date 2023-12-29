from bs4 import BeautifulSoup
from datetime import datetime

from crawler.crawlers.crawler import Crawler
from common.models.advert import Advert
from common.models.filter import Filter

# https://www.immonet.de/immobiliensuche/beta?locationIds=7304&toprice=800&fromprice=500&toarea=65&fromarea=50&marketingtype=2


class ImmoweltCrawler(Crawler):

    def crawl(self, filter: Filter) -> list[Advert]:
        page = self.request(url=filter.filter_url)
        soup = BeautifulSoup(page.content, "html.parser")
        adverts = []
        estate_items = soup.select('div[class^="EstateItem"]')

        for ad in estate_items:
            title = ad.find('h2').text.strip()
            url = ad.find('a')['href'].strip()
            author = ad.select_one('div[class^=ProviderName]').span.text.strip()
            keyfacts = ad.select_one('div[class^=KeyFacts]')
            price = keyfacts.find('div', {'data-test': 'price'}).text.strip()
            m2 = keyfacts.find('div', {'data-test': 'area'}).text.strip()
            rooms = keyfacts.find('div', {'data-test': 'rooms'}).text.strip()

            adverts.append(
                Advert(
                    None,
                    title,
                    author,
                    price,
                    url,
                    size_m2=m2,
                    filter_id=filter.id,
                    created_at=datetime.now(),
                    user_id=filter.user_id
                )
            )
        return adverts
