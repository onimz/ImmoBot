from Notifier.notifier import Notifier
from time import sleep

if __name__ == '__main__':
    notify = Notifier()
    while True:
        notify.crawl_site()
        sleep(notify.update_rate)
