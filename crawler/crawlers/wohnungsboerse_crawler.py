import requests
from bs4 import BeautifulSoup
from datetime import datetime

from crawler.crawlers.crawler import Crawler
from common.models.advert import Advert
from common.models.filter import Filter


# https://www.wohnungsboerse.net/searches/index?estate_marketing_types=miete%2C1&marketing_type=miete&estate_types%5B0%5D=1&is_rendite=0&estate_id=&zipcodes%5B%5D=&cities%5B%5D=Hannover&districts%5B%5D=&term=Hannover&umkreiskm=&pricetext=bis+800+%E2%82%AC&minprice=&maxprice=800&sizetext=ab+35+m%C2%B2&minsize=35&maxsize=&roomstext=&minrooms=&maxrooms=


class WohnungsboerseCrawler(Crawler):

    def crawl(self, filter: Filter) -> list[Advert]:
        page = requests.get(filter.filter_url)
        soup = BeautifulSoup(page.content, "html.parser")
        estate_items = soup.select('a[class^="estate"]')

        # Find all offers on page one
        adverts = []
        for ad in estate_items:
            title = ad.find('h3').text.strip()
            url = ad.get('href')
            author = "N/A"
            price, m2, rooms = (value.text.strip() for value in ad.find_all('dd'))

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
