import re
import logging
from time import sleep
from pathlib import Path
from maisxml import maisxml_has_been_fixed
from maisxml import defix as defix_maisxml
from maisxml import extract_toegangscode
from playwright.sync_api import Page
from ._helpers import retry_on_playwright_error

log = logging.getLogger(__name__)

def _set_checkbox_state(uploadvenster: Locator, checkbox_locator: string, state: bool):
    checkbox = uploadvenster.locator(f"{checkbox_locator} > .t-Form-inputContainer")
    checkbox_state = checkbox.locator("input[type='hidden']").get_attribute("value") == "1"
    if state != checkbox_state:
        checkbox.locator("label").click()

def _close_toast_and_uploadvenster(page: Page):
    sleep(3)
    page.get_by_role("button", name="OK").click()
    sleep(5)
    try:  # keep the try since there may be mutiple close buttons
        # good habit to close things
        page.get_by_role("button", name=" Sluiten").click()
        sleep(1)
        page.get_by_role("button", name="×").click() # close the toast
    except:
        pass

def _start_new_upload(
    page: Page,
    maisxml: str | Path,
    overschrijf_bestaande_inrichting: bool,
    nieuwe_guids: bool,
):
    log.info(f"{maisxml.name} naar toegang {extract_toegangscode(maisxml)} aan het uploaden")

    page.get_by_role("button", name="Importeren").click()
    uploadvenster = page.locator('iframe[title="Importeren"]').content_frame
    sleep(4)
    _set_checkbox_state(uploadvenster, "#P218_OVERSCHRIJF_INRICHTING_CONTAINER", overschrijf_bestaande_inrichting)
    _set_checkbox_state(uploadvenster, "#P218_NIEUWE_GUIDS_CONTAINER", nieuwe_guids)

    uploadvenster.locator("input[type='file']").set_input_files(maisxml)
    if not uploadvenster.get_by_text(maisxml.name).is_visible():  # filename in uploadvenster?
        log.warn(
            f"Upload van {maisxml.name} is niet geslaagd"
            f" (hint: misschien bevat {maisxml} geen MAIS XML)"
        )
        uploadvenster.get_by_role("button", name="Annuleren").click()
        return False

    uploadvenster.get_by_role("button", name="Ok").click()
    # uploadvenster may show an error, but since its an iframe, checking 'toast or error?' becomes complex
    upload_toast = page.locator(".toast", has_text=re.compile(f"Bezig met importeren van {maisxml.name}"))
    upload_toast.wait_for(timeout=3_000_000) # hence we wait for ± an hour max
    if not upload_toast.is_visible():
        log.error(f"Error tijdens het uploaden van {maisxml.name} (is {maisxml.name} te groot?)")
        return False
    log.info(f"Upload van {maisxml.name} is geslaagd")
    log.info("Wachten tot MAIS de XML heeft verwerkt...")

@retry_on_playwright_error()
def upload_maisxml(
    self,
    maisxml: str | Path,
    logfile: str | Path = None,
    overschrijf_bestaande_inrichting: bool = False,
    nieuwe_guids: bool = True,
) -> bool:
    """Upload een MAIS XML bestand naar een toegang. De juiste toegang wordt uit
    de MAIS XML afgeleid. Wanneer een upload sessie reeds gestart is, wordt die
    sessie hervat.

    Args:
        maisxml (str | Path): pad naar MAIS XML bestand om te uploaden (bijv. "1854_1_102_flexis.txt")
        logfile (Optional[str | Path]): Logfile om het eindresultaat naar te schrijven.
          Default is een .log bestand naast het bestand in `maisxml`.
        overschrijf_bestaande_inrichting (Optional[bool]): Geeft aan of de
          inrichting van de toegang (ingerichte archiefeenheidsoorten en toegestane
          hiërarchie) overschreven dient te worden. Default is om dit uit te zetten.
        nieuwe_guids (Optional[bool]): Maak nieuwe guids voor alle AETs en de top.
         Default is true, omdat GUIDs weinig inherente waarde hebben.

    Returns:
        bool: Boolean die aangeeft of upload succesvol was of niet.
    """
    maisxml = Path(maisxml)
    # TODO: move to general validation function that also inspects inrichting and top info
    # MAIS doesn't accept fixed/real xml!
    if maisxml_has_been_fixed(maisxml):
        log.info(f"{maisxml.name} lijkt normale XML; "
                 "het bestand wordt terug getransformeerd naar MAIS XML...")
        defix_maisxml(maisxml)

    self.page.get_by_role("treeitem", name="Beheren").click()
    self.page.get_by_role("treeitem", name="Toegangen", exact=True).click()
    sleep(2)

    # check if upload is already in progress
    upload_toast = self.page.locator(".toast", has_text=re.compile(f"Bezig met importeren van {maisxml.name}"))
    if not upload_toast.count():
        _start_new_upload(self.page, maisxml, overschrijf_bestaande_inrichting, nieuwe_guids)
    elif "fout" in upload_toast.inner_text().lower():
        # not sure which one of these is true, but a toast may hold either "geannuleerd" or "fout"
        log.warn(f"Een eerdere upload van {maisxml.name} ging verkeerd, of er zat een fout in het bestand")
        upload_toast.get_by_role("button", name="×").click()
        _start_new_upload(self.page, maisxml, overschrijf_bestaande_inrichting, nieuwe_guids)
    elif "geannuleerd" in upload_toast.inner_text().lower():
        # closely previously failed toast
        log.info("Toast van eerdere, gefaalde upload sessie gesloten")
        upload_toast.get_by_role("button", name="×").click()
        _start_new_upload(self.page, maisxml, overschrijf_bestaande_inrichting, nieuwe_guids)
    else:
        log.info(f"Wachten op verwerking van {maisxml.name} hervat")

    # TODO: maybe this shouldn't be infinite?
    while not "Wacht op beoordeling" in upload_toast.inner_text():
        self.page.reload()
        sleep(40)
        voortang = re.search(r"Voortgang:.*resterend", upload_toast.inner_text())
        print(f"\033[K{voortang.group() if voortang else ''}", end="\r", flush=True)

    sleep(7)
    logtext = (
        self.page.locator('iframe[title="Logging"]')
        .content_frame.locator("div.t-Region-body")
        .filter(has_text="Import gestart")
        .inner_text()
    )
    logfile = logfile or maisxml.parent / f"{maisxml.name.split(".")[0]}.log"
    Path(logfile).write_text(logtext)
    logtext = logtext.lower()

    # these are probably not all possible error cases
    if (
        re.search(r"fouten: [1-9]", logtext) # e.g. "aantal fouten: 1"
        or re.search(r"\bfout\b", logtext) # e.g. "Fout:" or " fout:", but not "fouten"
        or "error" in logtext
        or "onbekende tag" in logtext
        or logtext.count("\n") > 42 # more than 42 lines is probably also problematic
        or "ora-" in logtext
    ):
        warning = (
            f"uploaden van {maisxml} gaf foutmelding ORA-01555, wat meestal "
            "betekent dat er data verloren is gegaan.\n "
            "Hint: Soms werkt het om de toegang kleiner te maken"
            if "ora-01555" in logtext
            else f"MIAS heeft een fout gevonden in {maisxml.name}"
        )
        log.warn(f"{warning}; zie {logfile} voor meer informatie")
        _close_toast_and_uploadvenster(self.page)
        return False

    _close_toast_and_uploadvenster(self.page)
    log.info(f"{maisxml.name} lijkt foutloos verwerkt ✅")
    return True
