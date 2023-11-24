from src.utils import init_logger

from src.notifier import Notifier


if __name__ == '__main__':
    init_logger()
    
    notify = Notifier()
    notify.start_crawl_loop()
