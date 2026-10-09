from ._login import login
from ._upload_maisxml import upload_maisxml
from ._download_maisxml import download_maisxml_van_toegangcodes, download_maisxml_van_toegansgroep
from ._list_toegangsgroepen import list_toegangsgroepen

import logging as _logging
import os

__all__ = [
    "download_maisxml_van_toegansgroep",
    "download_maisxml_van_toegangcodes",
    "upload_maisxml",
    "login",
    "list_toegangsgroepen",
]

# register global logger object
_log = _logging.getLogger(__name__)
_log.setLevel(_logging.INFO)

# logger config
if os.environ.get("MAIS_LOGGING_MODE") == "systemd":
    # systemd already prints timestamps
    _logging.basicConfig(format="%(levelname)s: %(message)s")
else:
    _logging.basicConfig(
        format="[%(asctime)s] %(levelname)s: %(message)s", datefmt="%d %b %H:%M:%S"
    )
_logging.addLevelName(
    # colorize warning messages
    _logging.WARNING,
    "\033[1;33m%s\033[1;0m" % _logging.getLevelName(_logging.WARNING),
)

_logging.addLevelName(
    # colorize warning messages
    _logging.ERROR,
    "\033[1;31m%s\033[1;0m" % _logging.getLevelName(_logging.ERROR),
)
