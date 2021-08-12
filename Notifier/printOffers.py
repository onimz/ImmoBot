from Notifier.db import DB


if __name__ == '__main__':
    db = DB()
    offers = db.get_offers()
    print(f"{len(db.get_offers()[1])} offers stored in db")
    print(offers[0])
    for cnt, offer in enumerate(offers[1], start=1):
        print(str(cnt) + ": " + str(offer))
        
    db.close_con()