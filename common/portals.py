def get_portal_domains() -> list[str]:
    return [
        "wg-gesucht.de",
        "immowelt.de",
        "immobilien.de",
        "wohnungsboerse.net"
    ]


def get_portal_dict() -> dict:
    from crawler.crawlers.wg_gesucht_crawler import WgGesuchtCrawler
    from crawler.crawlers.immowelt_crawler import ImmoweltCrawler
    from crawler.crawlers.immobilien_crawler import ImmobilienCrawler
    from crawler.crawlers.wohnungsboerse_crawler import WohnungsboerseCrawler

    return {
        "wg-gesucht.de": WgGesuchtCrawler(),
        "immowelt.de": ImmoweltCrawler(),
        "immobilien.de": ImmobilienCrawler(),
        "wohnungsboerse.net": WohnungsboerseCrawler()
    }
