# Playmais - MAIS Playwright library (en scripts)

Playmaisis een op playwright-gebasseerde python library om MAIS aan te sturen.

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
    playmais.upload_maisxml(page, "/srv/share/maisxml/1843_1_102_flexis.txt")
    # download wat we net geupload hebben
    playmais.download_maisxml(page, toegang="1843")
```

Alle beschikbare functies en documentatie kun je hier vinden:

<!-- documentatie URL is nog te maken -->
...

