import requests
from bs4 import BeautifulSoup
from datetime import datetime

from crawler.crawlers.crawler import Crawler
from common.models.advert import Advert
from common.models.filter import Filter

# https://www.immobilien.de/Wohnen/Suchergebnisse-51797.html?search._digest=true&search._filter=wohnen&search.flaeche_von=20&search.objektart=wohnung&search.preis_bis=1500&search.typ=mieten&search.wo=city%3A14600&block=1


class ImmobilienCrawler(Crawler):

    def crawl(self, filter: Filter) -> list[Advert]:
        page = requests.get(filter.filter_url)
        soup = BeautifulSoup(page.content, "html.parser")
        estate_items = soup.select('a[class^="_ref"]')

        # Find all offers on page one
        adverts = []
        for ad in estate_items:
            title = ad.find('h3').text.strip()
            url = "https://www.immobilien.de" + ad.get('href')
            author = "N/A"
            price = ad.find('div', {'immo_preis'}).find('span', {'label_info'}).text.strip()
            m2 = ad.find('div', {'flaeche'}).find('span', {'label_info'}).text.strip()
            rooms = ad.find('div', {'zimmer'}).find('span', {'label_info'}).text.strip()
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
