from .login import login
from .upload_maisxml import upload_maisxml

import logging

# register global logger object
_log = logging.getLogger(__name__)
_log.setLevel(logging.INFO)

# setup logging
logging.basicConfig(
    format="[%(asctime)s] %(levelname)s: %(message)s", datefmt="%d %b %H:%M:%S"
)
logging.addLevelName(
    # colorize warning messages
    logging.WARNING,
    "\033[1;33m%s\033[1;0m" % logging.getLevelName(logging.WARNING),
)
