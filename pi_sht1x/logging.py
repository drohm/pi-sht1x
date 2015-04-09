from os import path
from logging import getLogger, Formatter, INFO
from logging.handlers import RotatingFileHandler


LOG_FORMAT = '[%(asctime)s] %(module)12s:%(funcName)12s:%(lineno)-4s %(levelname)-9s %(message)s'
LOG_FILE_NAME = 'pi_sht1x.log'


def create_logger(name):
    """
    Creates a logger for the given application. This function also removes all attached handlers
    in case there was a logger with the same name.
    """
    logger = getLogger(name)
    log_filename = path.join(path.dirname(path.realpath(__file__)), LOG_FILE_NAME)
    log_formatter = Formatter(LOG_FORMAT)

    file_handler = RotatingFileHandler(log_filename, mode='a', maxBytes=512000, backupCount=3)
    file_handler.setLevel(INFO)
    file_handler.setFormatter(log_formatter)

    del logger.handlers[:]
    logger.addHandler(file_handler)
    logger.setLevel(INFO)

    return logger
