import sqlite3
import os
import logging

from common.models.advert import Advert
from common.models.filter import Filter

def init_db():
    try:
        with get_connection() as con:
            cur = con.cursor()

            cur.execute('''
                CREATE TABLE IF NOT EXISTS Metadata_Bot (
                    id INTEGER PRIMARY KEY,
                    latest_poll_timestamp TIMESTAMP
                )
            ''')

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
                    created_at TIMESTAMP,
                    annonce_date DATE,
                    filter_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    FOREIGN KEY (filter_id) REFERENCES Filter(id),
                    FOREIGN KEY (user_id) REFERENCES User(id)
                )
            ''')
    except sqlite3.OperationalError as e:
        logging.error(f"Couldn't create tables: {e}")
        raise SystemExit
    except Exception as e:
        logging.error(f"Couldn't connect to db: {e}")
        raise SystemExit

def get_connection():
    return sqlite3.connect(os.path.dirname(os.path.realpath(__file__)) + '/../data/adverts.db')

def get_latest_poll_timestamp(con: sqlite3.Connection):
    cur = con.cursor()
    cur.execute('SELECT latest_poll_timestamp FROM Metadata_Bot')
    result = cur.fetchone()
    if result:
        return result[0]
    return None

def update_latest_poll_timestamp(new_timestamp, con: sqlite3.Connection):
    con.cursor().execute('INSERT OR REPLACE INTO Metadata_Bot (id, latest_poll_timestamp) VALUES (?, ?)', (1, new_timestamp,))

def get_user_count(con: sqlite3.Connection):
    cur = con.cursor()
    cur.execute('SELECT COUNT(*) FROM User')
    count = cur.fetchone()[0]
    return count

def add_user(user_id, user_name, user_limit, con: sqlite3.Connection) -> int:
    cur = con.cursor()
    if is_user_registered(user_id, con):
        return 2
    user_count = get_user_count(con)
    if user_count >= user_limit:
        print(f"Cannot add user. maximum user limit reached.")
        return 0
    
    cur.execute("INSERT INTO User (id, user_name) VALUES (?, ?)", (user_id, user_name,))
    print(f"User {user_name} ({user_id}) registered successfully.")
    logging.info(f"User {user_name} ({user_id}) registered successfully.")
    return 1

def add_filter(domain, filter_url, user_id, con: sqlite3.Connection):
    cur = con.cursor()
    cur.execute("INSERT INTO Filter (domain, filter_url, user_id) VALUES (?, ?, ?)", (domain, filter_url, user_id,))

def add_adverts(adverts: list[Advert], con: sqlite3.Connection) -> list[Advert]:
    cur = con.cursor()
    added_adverts = []
    for advert in adverts:
        if is_advert_in_db(advert, con):
            continue
        query = f"INSERT INTO Advert (title, author, price, url, size_m2, website, created_at, annonce_date, filter_id, user_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        cur.execute(query, (advert.title, advert.author, advert.price, advert.url, "N/A", "N/A", advert.created_at,"N/A", advert.filter_id, advert.user_id,))
        added_adverts.append(advert)
    return added_adverts

def get_adverts(con: sqlite3.Connection, timestamp=None) -> list[Advert]:
    if timestamp:
        query = f"SELECT * FROM Advert WHERE created_at > '{timestamp}'"
    else:
        query = "SELECT * FROM Advert"
    cur = con.cursor()
    cur.execute(query)
    return [Advert(*advert) for advert in cur.fetchall()]

def get_filters(con: sqlite3.Connection) -> list[Filter]:
    query = "SELECT * FROM Filter"
    cur = con.cursor()
    cur.execute(query)
    return [Filter(*filter) for filter in cur.fetchall()]

def is_advert_in_db(advert: Advert, con: sqlite3.Connection) -> bool:
    query = "SELECT * FROM Advert WHERE user_id = ? AND url = ?"
    cur = con.cursor()
    cur.execute(query, (advert.user_id, advert.url,))
    if cur.fetchone():
        return True
    return False

def is_user_registered(user_id, con: sqlite3.Connection) -> bool:
    query = "SELECT * FROM User WHERE id = ?"
    cur = con.cursor()
    cur.execute(query, (user_id,))
    if cur.fetchone():
        return True
    return False
