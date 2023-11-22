import logging
from os import getenv
from typing import Optional

from dotenv import load_dotenv


load_dotenv("splitwise.env")

logger = logging.getLogger("splitwise")

logging.basicConfig(
    format="%(asctime)s %(message)s",
    filename="splitwise.log",
    encoding="utf-8",
    level=logging.DEBUG,
)


def log_and_print(msg: str, level: str = "warn") -> None:
    """
    This function can be used for printing an error message, as well as for logging it by passing the level to the level parameter.

    This function looks for the env variable `KEEP_A_LOG`, to check whether it should keep logs to the file.

    Printing always happens, irrespective of the value of `KEEP_A_LOG`.

    #### Parameters
        `msg` - The message to print/log.
        `
    """
    print(msg)

    log_to_file: Optional[str] = getenv("KEEP_A_LOG")

    if str(log_to_file).casefold() not in ("false", "no", "none"):
        if level == "warn":
            logger.warning(msg)
        elif level == "critical":
            logger.critical(msg)
        elif level == "info":
            logger.info(msg)
        else:
            logger.debug(msg)
