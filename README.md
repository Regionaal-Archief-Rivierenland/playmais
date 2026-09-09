# Playmais - MAIS Playwright library (en scripts)

Playmais is een op playwright-gebaseerde python library om MAIS aan te sturen.

Simpel voorbeeld:

``` python
import playmais
from playwright.sync_api import sync_playwright

with sync_playwright() as playwright:
    browser = playwright.chromium.launch()
    context = browser.new_context()
    page = context.new_page()

    # login en upload
    playmais.login(page)

    # upload gecorrigeerde toegang
    upload_succesvol = playmais.upload_maisxml(page, "/srv/share/maisxml/1843_1_102_flexis.txt")
    if upload_succesvol:
        # download wat we net geupload hebben
        playmais.download_maisxml(page, toegang="1843")
    else:
        ...
```

Alle beschikbare functies en functie documentatie kun je hier vinden:

<!-- documentatie URL is nog te maken -->
...

# Installatie

```
git clone git@github.com:Regionaal-Archief-Rivierenland/playmais.git && sudo pip install . 
```

(of zonder sudo als je het voor je gebruiker wilt houden, of met `uv`, etc.) 
