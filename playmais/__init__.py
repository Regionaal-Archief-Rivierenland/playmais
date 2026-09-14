from ._login import login
from ._upload_maisxml import upload_maisxml
from ._download_maisxml import download_maisxml_van_toegangcodes, download_maisxml_van_toegansgroep
from ._list_toegangsgroepen import list_toegangsgroepen

import logging
import os

# register global logger object
_log = logging.getLogger(__name__)
_log.setLevel(logging.INFO)

# logger config
if os.environ.get("MAIS_LOGGING_MODE") == "systemd":
    # systemd already prints timestamps
    logging.basicConfig(format="%(levelname)s: %(message)s")
else:
    logging.basicConfig(
        format="[%(asctime)s] %(levelname)s: %(message)s", datefmt="%d %b %H:%M:%S"
    )
logging.addLevelName(
    # colorize warning messages
    logging.WARNING,
    "\033[1;33m%s\033[1;0m" % logging.getLevelName(logging.WARNING),
)
