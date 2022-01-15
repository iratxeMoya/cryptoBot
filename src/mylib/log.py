import logging
from colorama import Fore, Style

FORMAT = '[%(filename)s -> %(funcName)s():%(lineno)s] %(levelname)s - %(message)s'

class CustomFormatter(logging.Formatter):

    format = FORMAT

    FORMATS = {
        logging.DEBUG: Fore.WHITE + format + Fore.RESET,
        logging.INFO: Fore.WHITE + format + Fore.RESET,
        logging.WARNING: Fore.YELLOW + format + Fore.RESET,
        logging.ERROR: Fore.RED + format + Fore.RESET,
        logging.CRITICAL: Fore.RED + Style.BRIGHT + format + Fore.RESET
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

LEVEL = logging.DEBUG
logger = logging.getLogger("cryptoBot")
logging.basicConfig(format=FORMAT, level = LEVEL)

ch = logging.StreamHandler()
ch.setLevel(LEVEL)
ch.setFormatter(CustomFormatter())

logger.addHandler(ch)