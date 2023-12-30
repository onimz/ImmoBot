from bs4 import BeautifulSoup
from datetime import datetime

from crawler.crawlers.crawler import Crawler
from common.models.advert import Advert
from common.models.filter import Filter

# https://www.kleinanzeigen.de/s-wohnung-mieten/hannover/preis::800/c203l3155+wohnung_mieten.qm_d:35%2C


class KleinanzeigenCrawler(Crawler):

    def crawl(self, filter: Filter) -> list[Advert]:
        page = self.request(url=filter.filter_url)
        soup = BeautifulSoup(page.content, "html.parser")
        estate_items = soup.select('li[class^="j-adlistitem"]')

        # Find all offers on page one
        adverts = []
        for ad in estate_items[:self.MAX_AD_SIZE]:
            title = ad.find('strong', {'adlist--item--title'}).text.strip()
            url = "https://www.kleinanzeigen.de" + ad.find('a')['href']
            author = "N/A"
            price = ad.find('div', {'adlist--item--price'}).text.strip()
            m2, rooms = list(value.text.strip() for value in ad.find_all('span', {'simpletag'}))[:2]
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
