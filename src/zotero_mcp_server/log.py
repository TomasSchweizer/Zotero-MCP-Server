"""
Setting up logging 
"""
import logging

def setup_logging() -> logging.Logger:
    """Setting up the logger

    """

    logging.basicConfig(
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S',
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    logger = logging.getLogger()

    return logger
