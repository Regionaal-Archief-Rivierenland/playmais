import re
import logging
from playwright.sync_api import Playwright, sync_playwright, expect
from time import sleep
from pathlib import Path

log = logging.getLogger(__name__)


def _set_checkbox_state(uploadvenster: Locator, checkbox_locator: string, state: bool):
    checkbox = uploadvenster.locator(f"{checkbox_locator} > .t-Form-inputContainer")
    checkbox_state = checkbox.locator("input[type='hidden']").get_attribute("value") == "1"
    if state != checkbox_state:
        checkbox.locator("label").click()

# TODO: i think we need a function that targets a notif by name
def upload_maisxml(
    page: Page,
    maisxml: str | Path,
    logfile: str | Path = None,
    overschrijf_bestaande_inrichting: bool = False,
    nieuwe_guids: bool = True,
) -> bool:
    """Upload een MAIS XML bestand naar een toegang. De juiste toegang wordt uit
    de MAIS XML afgeleid.

    Deze functie gaat uit van een page object waarop al is ingelogd.

    Args:
        page (Page): playwright pagina-object. Wordt in-place aangepast; eindigt op de homepage.
        maisxml (str | Path): pad naar MAIS XML bestand (bijv. "1854_1_102_flexis.txt")
        logfile (Optional[str | Path]): Logfile om het eindresultaat naar te schrijven.
          Default is een .log bestand naast `maisxml`.
        overschrijf_bestaande_inrichting (Optional[bool]): Geeft aan of de
          inrichting van de toegang (ingerichte archiefeenheidsoorten en toegestane
          hiërarchie) overschreven dient te worden. Default is om dit uit te zetten.
        nieuwe_guids: Maak nieuwe guids voor alle AETs en de top.
         Default is true, omdat GUIDs weinig inherente waarde hebben.

    Returns:
        bool: Boolean die aangeeft of upload succesvol was of niet.
    """
    maisxml = Path(maisxml)
    # we don't do anything with the toegang code, but its nice to know where the file is going to go to
    target_toegang = re.match(r"^(.*?)_", maisxml.name)

    page.get_by_role("treeitem", name="Beheren").click()
    page.get_by_role("treeitem", name="Toegangen", exact=True).click()
    sleep(2)

    # check if upload is already in progress
    upload_toast = page.locator(".toast-message", has_text=f"Bezig met importeren van {maisxml.name}")
    if not upload_toast.count():
        log.info(f"{maisxml.name} naar toegang {target_toegang.group(1)} aan het uploaden")
        page.get_by_role("button", name="Importeren").click()
        uploadvenster = page.locator('iframe[title="Importeren"]').content_frame
        sleep(4)
        _set_checkbox_state(uploadvenster, "#P218_OVERSCHRIJF_INRICHTING_CONTAINER", overschrijf_bestaande_inrichting)
        _set_checkbox_state(uploadvenster, "#P218_NIEUWE_GUIDS_CONTAINER", nieuwe_guids)

        uploadvenster.locator("input[type='file']").set_input_files(maisxml)
        if not uploadvenster.get_by_text(maisxml.name).is_visible(): # filename in uploadvenster?
            log.warn(f"Upload van {maisxml.name} is niet geslaagd")
            uploadvenster.get_by_role("button", name="Annuleren").click()
            return False

        uploadvenster.get_by_role("button", name="Ok").click()
        # TODO: either this or some kind of error will be visible (check for "(proxy) error" in frame)
        upload_toast.wait_for(timeout=0)
        log.info(f"Upload van {maisxml.name} is geslaagd")
        log.info("Wachten tot MAIS de XML heeft verwerkt...")
    elif "fout" in upload_toast.inner_text().lower():
        # TODO: add log? tho this branch is rare and logging adds a tiny bit of complexity
        log.warn(f"MIAS heeft een fout gevonden in {maisxml}")
        return False
    else:
        log.info(f"Wachten op verwerking van {maisxml.name} hervat")

    # TODO: maybe this shouldn't be infinite?
    while not "Wacht op beoordeling" in upload_toast.inner_text():
        page.reload()
        sleep(45)
        voortang = re.search(r"Voortgang:.*resterend", upload_toast.inner_text())
        print(f"\033[K{voortang.group() if voortang else ''}", end="\r", flush=True)

    sleep(7)
    logtext = (
        page.locator('iframe[title="Logging"]')
        .content_frame.locator("div.t-Region-body")
        .filter(has_text="Import gestart")
        .inner_text()
    )
    logfile = logfile or maisxml.parent / f"{maisxml.name.split(".")[0]}.log"
    Path(logfile).write_text(logtext)

    # FIXME: these are probably not all possible error cases
    if (
        re.match(r".*aantal fouten: [1-9]\d*", logtext.lower()) # one or more after fouten
        or re.search(r"\bfout\b", logtext.lower()) # e.g. "Fout:" or " fout:", but not "fouten"
        or "error" in logtext.lower()
        or "onbekende tag" in logtext.lower()
        or logtext.count("\n") > 42 # more than 42 lines is probably also problematic
    ):
        log.warn(f"MIAS heeft een fout gevonden in {maisxml}; zie {logfile} voor meer informatie")
        # The only way to cancel is to wait, for some reason, so wait 8min
        sleep(8 * 60)
        page.reload()
        sleep(3)
        page.get_by_role("button", name=" Sluiten").click()
        # upload was niet succesvol
        return False

    page.get_by_role("button", name="OK").click()

    try:  # keep the try since there may be mutiple close buttons
        # good habit to close things
        page.get_by_role("button", name=" Sluiten").click()
        page.get_by_role("button", name="×").click() # close the toast
    except:
        pass

    log.info(f"{maisxml} lijkt foutloos verwerkt ✅")
    return True
