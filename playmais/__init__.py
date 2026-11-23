"""
Playmais is een library om MAIS-Flexis aan te sturen via playwright.

# Quickstart

MAIS XML uploaden is een kwestie van een `Playmais`-object aanmaken, en de
`upload_maisxml`-methode aanroepen:

```python
from playmais import Playmais

playmais = Playmais()
upload_succesvol = playmais.upload_maisxml("1854_1_102_flexis.txt")
if upload_succesvol:
     # download wat we net geupload hebben
     playmais.download_maisxml_van_toegangcodes(toegangcodes=["1854"], folder="/tmp")
 else:
     ...
 # calling .close() is optional, but recommended if you need to do a lot of
 # work *after* all playwright automation is finished
 playmais.close() # tear down browser and playwright controller

 # Alternatively, you can use with-block, which will automatically run .close()
 with Playmais() as pm:
     pm.upload_maisxml("1854_1_102_flexis.txt")
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

# Browser-instanties managen

Elk object wat je met `Playmais()` aanmaakt start op de achtergrond nieuwe browser
op, plus een javascript process wat met deze browser-instantie communiceert. In de
meeste gevallen zal Python deze processen automatisch voor je sluiten wanneer je
script stopt.

Soms wil je niet dat deze achtergrond-processen kostbaar werkgeheugen in beslag
nemen terwijl je script ze niet meer nodig heeft. In dat geval kun je deze
processen in kwestie vervroeg afsluiten via

```python
from playmais import Playmais
playmais = Playmais()
# doe dingen in MAIS
...
# dingen gedaan, tijd om af te sluiten
playmais.close()
# doe dingen *buiten* MAIS
...
```

Ditzelfde kun je ook met een `with`-block doen:

```python
with Playmais() as playmais:
    playmais.upload_maisxml(...)
```
"""

from .playmais import Playmais
import os
import logging

# register global logger object
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

# TODO: maybe log submodule name as well?
# logger config
if os.environ.get("MAIS_LOGGING_MODE") == "systemd":
    # systemd already prints timestamps
    logging.basicConfig(format="%(levelname)s: %(message)s")
else:
    logging.basicConfig(
        format="[%(asctime)s] %(levelname)s: %(message)s", datefmt="%d %b %H:%M:%S"
    )

# colorize warning and error messages
logging.addLevelName(
    logging.WARNING,
    "\033[1;33m%s\033[1;0m" % logging.getLevelName(logging.WARNING),
)
logging.addLevelName(
    logging.ERROR,
    "\033[1;31m%s\033[1;0m" % logging.getLevelName(logging.ERROR),
)
