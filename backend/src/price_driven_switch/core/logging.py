import logging

from loguru import logger

# Log format
LOG_FORMAT = "{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"


class PropagateHandler(logging.Handler):
    def emit(self, record):
        logging.getLogger(record.name).handle(record)


def setup_logging() -> None:
    logger.add(PropagateHandler(), format="{message} {extra}")

    logger.add(
        "logs/fast_api.log",
        rotation="1 week",
        retention="7 days",
        level="DEBUG",
        enqueue=False,
        format=LOG_FORMAT,
    )
