import sqlite3
import os


class DB:
    def __init__(self):
        directory = os.path.dirname(os.path.realpath(__file__))
        try:
            self.con = sqlite3.connect(directory + '/offers.db')
        except Exception as e:
            print(e)
            raise SystemExit
        self.cur = self.con.cursor()
        self.cur.execute("CREATE TABLE IF NOT EXISTS Offers (title TEXT, user TEXT, price TEXT, url TEXT)")

    def add_offer(self, offer) -> None:
        sql = f"INSERT INTO Offers VALUES ('{offer.title}', '{offer.user}', '{offer.price}', '{offer.url}')"
        self.cur.execute(sql)
        self.con.commit()

    def get_offers(self) -> (list, list):
        sql = "SELECT * FROM Offers ORDER BY title ASC"
        self.cur.execute(sql)
        colmns = list(map(lambda x: x[0], self.cur.description))
        return colmns, self.cur.fetchall()

    def check_if_in_db(self, offer) -> bool:
        sql = f"SELECT * FROM Offers WHERE title='{offer.title}' AND user='{offer.user}' AND price='{offer.price}'"
        self.cur.execute(sql)
        if len(self.cur.fetchall()) > 0:
            return True
        return False

    def close_con(self) -> None:
        self.con.close()
