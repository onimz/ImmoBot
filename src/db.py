import sqlite3
import os
import logging

from src.models.advert import Advert
from src.models.filter import Filter

def init_db():
    try:
        with get_connection() as con:
            cur = con.cursor()
            cur.execute('''
                CREATE TABLE IF NOT EXISTS User (
                    id INTEGER PRIMARY KEY,
                    user_name TEXT NOT NULL
                )
            ''')

            cur.execute('''
                CREATE TABLE IF NOT EXISTS Filter (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    domain TEXT,
                    filter_url TEXT,
                    user_id INTEGER NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES Users(id)
                )
            ''')

            cur.execute('''
                CREATE TABLE IF NOT EXISTS Advert (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    author TEXT,
                    price TEXT,
                    url TEXT,
                    size_m2 TEXT,
                    website TEXT,
                    annonce_date DATE,
                    filter_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    FOREIGN KEY (filter_id) REFERENCES Filter(id),
                    FOREIGN KEY (user_id) REFERENCES User(id)
                )
            ''')
            con.commit()
    except sqlite3.OperationalError as e:
        logging.error(f"Couldn't create tables: {e}")
        raise SystemExit
    except Exception as e:
        logging.error(f"Couldn't connect to db: {e}")
        raise SystemExit

def get_connection():
    return sqlite3.connect(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'adverts.db'))

def get_user_count(con):
    cur = con.cursor()
    cur.execute('SELECT COUNT(*) FROM User')
    count = cur.fetchone()[0]
    return count

def add_user(user_id, user_name, user_limit, con) -> int:
    cur = con.cursor()

    if is_user_registered(user_id, con):
        return 2

    user_count = get_user_count(con)
    if user_count >= user_limit:
        print(f"Cannot add user. maximum user limit reached.")
        return 0
    
    cur.execute("INSERT INTO User (id, user_name) VALUES (?, ?)", (user_id, user_name,))
    con.commit()
    print(f"User {user_name} ({user_id}) registered successfully.")
    logging.info(f"User {user_name} ({user_id}) registered successfully.")
    return 1

def add_filter(domain, filter_url, user_id, con):
    cur = con.cursor()
    cur.execute("INSERT INTO Filter (domain, filter_url, user_id) VALUES (?, ?, ?)", (domain, filter_url, user_id,))
    con.commit()

def add_adverts(adverts, con) -> list[Advert]:
    cur = con.cursor()
    added_adverts = []
    for advert in adverts:
        if is_advert_in_db(advert, con):
            continue
        query = f"INSERT INTO Advert (title, author, price, url, size_m2, website, annonce_date, filter_id, user_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
        cur.execute(query, (advert.title, advert.author, advert.price, advert.url, "N/A", "N/A", "N/A", advert.filter_id, advert.user_id,))
        con.commit()
        added_adverts.append(advert)
    return added_adverts

def get_adverts(con) -> list[Advert]:
    query = "SELECT * FROM Advert ORDER BY title ASC"
    cur = con.cursor()
    cur.execute(query)
    return [Advert(*advert) for advert in cur.fetchall()]

def get_filters(con) -> list[Filter]:
    query = "SELECT * FROM Filter"
    cur = con.cursor()
    cur.execute(query)
    return [Filter(*filter) for filter in cur.fetchall()]

def is_advert_in_db(advert, con) -> bool:
    query = "SELECT * FROM Advert WHERE url = ?"
    cur = con.cursor()
    cur.execute(query, (advert.url,))
    if len(cur.fetchall()) > 0:
        return True
    return False

def is_user_registered(user_id, con) -> bool:
    query = "SELECT * FROM User WHERE id = ?"
    cur = con.cursor()
    cur.execute(query, (user_id,))
    if len(cur.fetchall()) > 0:
        return True
    return False
