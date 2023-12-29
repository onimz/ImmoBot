class Advert:
    def __init__(self,
                 id,
                 title,
                 author,
                 price,
                 url,
                 size_m2=None,
                 website=None,
                 created_at=None,
                 advert_date=None,
                 filter_id=None,
                 user_id=None):
        self.id = id
        self.title = title
        self.author = author
        self.price = price
        self.url = url
        self.size_m2 = size_m2
        self.website = website
        self.created_at = created_at
        self.advert_date = advert_date
        self.filter_id = filter_id
        self.user_id = user_id
