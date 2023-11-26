from src.models.advert import Advert

class Crawler:
    
    def crawl(self, filter_url) -> list[Advert]:
        raise NotImplementedError("Subclasses must implement the crawl method")
