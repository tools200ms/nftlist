import logging


class Log:
    @staticmethod
    def init(level: logging):
        logging.basicConfig(level=level, format='%(levelname)s: %(message)s')

    @staticmethod
    def debug(msg: str):
        if __debug__:
            logging.debug(msg)

    @staticmethod
    def warn(msg: str):
        logging.warn(msg)

    @staticmethod
    def info(msg: str):
        logging.info(msg)

    @staticmethod
    def error(msg: str):
        logging.error(msg)

    @staticmethod
    def critical(msg: str):
        logging.critical(msg)

