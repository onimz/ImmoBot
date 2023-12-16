import os
import logging
from logging.handlers import TimedRotatingFileHandler
import time


def init_logger(path, level=logging.DEBUG):
    log_directory = path
    log_file_path = os.path.join(log_directory, "app.log")
    os.makedirs(log_directory, exist_ok=True)
    logger = logging.getLogger()
    logger.setLevel(level)
    handler = TimedRotatingFileHandler(log_file_path, when="midnight", interval=1, backupCount=30)
    formatter = logging.Formatter("%(asctime)s (%(levelname)s): %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def exit_with_error(msg):
    logging.error(msg)
    exit(f"!!PROGRAM ENCOUNTERED AN ERROR: {msg}")


def timed(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"Crawl routine took {execution_time:.4f} seconds to execute.")
        logging.info(f"Crawl routine took {execution_time:.4f} seconds to execute.")
        return result
    return wrapper
