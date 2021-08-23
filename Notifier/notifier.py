from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib

import configparser
import os

import requests
from bs4 import BeautifulSoup

from Notifier.offer import Offer
from Notifier.db import DB


class Notifier:
    def __init__(self):
        # Read in config values
        config = configparser.ConfigParser(interpolation=None)
        try:
            config.read(os.path.dirname(os.path.realpath(__file__)) + "/../config.ini")
            self.sender = config.get('MAIL', 'mail_user')
            self.receiver = config.get('MAIL', 'mail_to')
            self.pw = config.get('MAIL', 'mail_pw')
            self.host = config.get('MAIL', 'mail_smtp_host')
            self.port = config.get('MAIL', 'mail_smtp_port')
            self.filter_url = config.get('WG-GESUCHT', 'filter_url')
            self.update_rate = config.getint('WG-GESUCHT', 'update_rate')
        except Exception as e:
            print(f"(Config-File Error) {e}")
            raise SystemExit

    def crawl_site(self):
        page = requests.get(self.filter_url)
        soup = BeautifulSoup(page.content, "html.parser")
        results = soup.find_all("div", class_="col-sm-8 card_body")

        # Find all WG-Gesucht offers on page one
        offers = []
        for result in results:
            user_name = result.find("span", class_="ml5")
            is_ad = user_name is None or result.find("span", class_="label_verified ml5")

            if not is_ad:
                user_name = user_name.text.strip()
                title = result.find("a").text.strip()
                price = result.find("div", class_="col-xs-3").find("b").text.strip()
                url = "https://www.wg-gesucht.de" + result.find('a')['href']
                offers.append(Offer(title, user_name, price, url))

        # Add new offers to db & build mail string
        db = DB()
        new_offers = 0
        mail_string = f"Neue Anzeige/n Ihres <a href=\"{self.filter_url}\">Suchauftrags</a>:<br><br>"
        for cnt, offer in enumerate(offers, start=1):
            if not db.check_if_in_db(offer):
                db.add_offer(offer)
                new_offers += 1
                trim = 29  # Trim length for title
                title = (offer.title[:trim - 2] + '..') if len(offer.title) > trim else offer.title
                mail_string += f"<pre>{(str(new_offers) + '.'):3} <a href=\"{offer.url}\">{title}</a>{''.ljust(trim - len(title))} ({offer.price})</pre>"
        mail_string += "<br><br>Viel Erfolg beim Bewerben!"
        db.close_con()

        # Send out new offers via mail
        if new_offers > 0:
            s = smtplib.SMTP(host=self.host, port=self.port)
            s.starttls()
            s.login(self.sender, self.pw)

            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"{new_offers} neue WG-Gesucht Anzeige/n"
            msg["From"] = self.sender
            msg["To"] = self.receiver
            msg.attach(MIMEText(mail_string, 'html'))
            s.sendmail(self.sender, self.receiver, msg.as_string())

            s.quit()
            print("Sent mail")

