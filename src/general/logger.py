import logging
import os

class Logger():
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(filename="logfile",
                            filemode='w',
                            format='%(asctime)s-%(levelname)s-%(message)s',
                            datefmt='%Y:%m:%d %H:%M:%S',
                            level=logging.INFO,
                            )
        os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
        self.logging = logging

    def log_and_print(self, message: str, level, logger: logging.Logger):
        self.logger.log(level=level, msg=message)  # log as normal
        print(message)  # prints to stdout by default

    def info(self, arg):
        self.logger.info(arg)




