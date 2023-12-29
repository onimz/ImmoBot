from common.models.advert import Advert
from common.models.filter import Filter


class Crawler:

    def crawl(self, filter: Filter) -> list[Advert]:
        raise NotImplementedError("Subclasses must implement the crawl method")
