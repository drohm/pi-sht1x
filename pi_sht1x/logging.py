from os import getenv, path, mkdir
from logging import getLogger, Formatter, WARNING
from logging.handlers import RotatingFileHandler


LOG_FORMAT = '[%(asctime)s] %(module)12s:%(funcName)12s:%(lineno)-4s %(levelname)-9s %(message)s'
LOG_FOLDER_NAME = '.pi_sht1x'
LOG_FILE_NAME = 'pi_sht1x.log'


def create_logger(name):
    """
    Creates a logger for the given application. This function also removes all attached handlers
    in case there was a logger with the same name.
    """
    logger = getLogger(name)
    log_filename = os.path.join(_get_log_folder(), LOG_FILE_NAME)
    log_formatter = Formatter(LOG_FORMAT)

    file_handler = RotatingFileHandler(log_filename, mode='a',
                                       maxBytes=512000, backupCount=3)
    file_handler.setLevel(WARNING)
    file_handler.setFormatter(log_formatter)

    del logger.handlers[:]
    logger.addHandler(file_handler)
    logger.setLevel(WARNING)

    return logger


def _get_log_folder() -> str:
    """
    Combine and return realpath of log folder. If the folder does not exist,
    then create it.
    """
    log_folder = path.join(getenv('HOME'), LOG_FOLDER_NAME)
    if path.exists(log_folder):
        pass
    else:
        mkdir(log_folder)

    return log_folder
