from common.models.advert import Advert


class Crawler:

    def crawl(self, filter_url, filter_id, user_id) -> list[Advert]:
        raise NotImplementedError("Subclasses must implement the crawl method")
