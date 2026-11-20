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
    upload_succesvol = playmais.upload_maisxml(page, "1843_1_102_flexis.txt")
    if upload_succesvol:
        # download wat we net geupload hebben
        playmais.download_maisxml_van_toegangscodes(page, toegangscodes=["1843"], folder="/tmp")
    else:
        ...
```

# CLI gebruik

Als je deze library installeert, installeer je ook de commandline programma's `download_maisxml` en `upload_maisxml` mee. Ze werken ongeveer hetzelfde als de python functies:

``` shell
# upload 1843 en alle toegangen die beginnen met 17
$ upload_maisxml 1843_1_102_flexis.txt 17*_1_102_flexis.txt
```

.. note::
    Als je niet de hele tijd je wachtwoord en gebruikersnaam wilt invoeren, kun je deze in de environment variabelen `MAIS_USER` en `MAIS_PASSWORD` zetten. Deze worden opgepikt door alle CLI programma's en python-functies die gebundeld zijn met playmais.

Zie de `--help`-tekst van beide programma's voor alle mogelijke opties.
"""

from .playmais import Playmais
