"""Setup logger"""

import logging

logging.basicConfig(
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S',
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger()
