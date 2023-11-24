import os
import logging
from logging.handlers import TimedRotatingFileHandler

def init_logger():
    log_directory = f"{os.path.dirname(os.path.abspath(__file__))}/logs"
    log_file_path = os.path.join(log_directory, "app.log")
    os.makedirs(log_directory, exist_ok=True)
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    handler = TimedRotatingFileHandler(log_file_path, when="midnight", interval=1, backupCount=365)
    formatter = logging.Formatter("%(asctime)s (%(levelname)s): %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

def exit_with_error(msg):
    exit(f"PROGRAM STOPPED: {msg}")
