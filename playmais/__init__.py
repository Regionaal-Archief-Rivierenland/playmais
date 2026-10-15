"""
Library om MAIS-Flexis aan te sturen via playwright.

# Quickstart

Simpel voorbeeld van de stappen die je nodig hebt om een toegang te uploaden:

```python
import playmais
from playwright.sync_api import sync_playwright

with sync_playwright() as playwright:
    browser = playwright.chromium.launch()
    context = browser.new_context()
    page = context.new_page()

    playmais.login(page)

    # upload gecorrigeerde toegang
    upload_succesvol = playmais.upload_maisxml(page, "/srv/share/maisxml/1843_1_102_flexis.txt")
    if upload_succesvol:
        # download wat we net geupload hebben
        playmais.download_maisxml_van_toegangcodes(page, toegangcodes=["1843"], folder="/tmp")
    else:
        ...
```

# CLI gebruik

Als je deze library installeert, installeer je ook de commandline programma's `download_maisxml` en `upload_maisxml` mee. Ze werken ongeveer hetzelfde als de python functies:

``` shellsession
# upload 1843 en alle toegangen die beginnen met 17
$ upload_maisxml 1843_1_102_flexis.txt 17*_1_102_flexis.txt
```

.. tip::  Als je niet de hele tijd je wachtwoord en gebruikersnaam wilt invoeren, kun je deze in de environment variabelen `MAIS_USER` en `MAIS_PASSWORD` zetten. Deze worden opgepikt door alle CLI programma's en python-functies die gebundeld zijn met playmais.

Zie de `--help`-tekst van beide programma's voor alle mogelijke opties.
"""

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
