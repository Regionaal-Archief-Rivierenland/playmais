import re
import logging
from playwright.sync_api import Playwright, sync_playwright, expect
from time import sleep
from pathlib import Path

log = logging.getLogger(__name__)

# TODO: maybe accept file streams?
# TODO: do we really need pogingen/retry mechanism?
def upload_maisxml(
    page: Page,
    maisxml: str | Path,
    logfile: str | Path = None,
    pogingen: int = 1,
    overschrijf_bestaande_inrichting: bool = False,
) -> bool:
    """Upload een MAIS XML bestand naar een toegang. De juiste toegang wordt uit
    de MAIS XML afgeleid.

    Deze functie gaat uit van een page object waarop al is ingelogd.

    Args:
        page (Page): playwright pagina-object. Wordt in-place aangepast; eindigt op de homepage.
        maisxml (str | Path): pad naar MAIS XML bestand (bijv. "1854_1_102_flexis.txt")
        logfile (Optional[str | Path]): Logfile om het eindresultaat naar te schrijven.
          Default is een .log bestand naast `maisxml`.
        pogingen (Optional[int]): Aantal upload pogingen
        overschrijf_bestaande_inrichting (Optional[bool]): Geeft aan of de
          inrichting van de toegang (ingerichte archiefeenheidsoorten en toegestane
          hiërarchie) overschreven dient te worden. Default is om dit uit te zetten.

    Returns:
        bool: Boolean die aangeeft of upload succesvol was of niet.

    """
    maisxml = Path(maisxml)
    if not maisxml.exists():
        raise FileNotFoundError(f"Het MAIS XML bestand {maisxml} is niet gevonden")

    # we don't do anything with the toegang code, but its nice to know where the file is going to go to
    target_toegang = re.match(r"^(\d+)_.*", maisxml.name)
    if not target_toegang:
        raise ValueError(f"{maisxml} begint niet met een toegangscode")

    page.get_by_role("treeitem", name="Beheren").click()
    page.get_by_role("treeitem", name="Toegangen", exact=True).click()

    # upload MAIS XML to the server
    while pogingen:
        log.info(f"{maisxml.name} naar toegang {target_toegang.group(1)} aan het uploaden")
        page.get_by_role("button", name="Importeren").click()
        uploadvenster = page.locator('iframe[title="Importeren"]').content_frame

        # TODO: do this for the other boxes as well?
        checkbox = uploadvenster.locator("#P218_OVERSCHRIJF_INRICHTING_CONTAINER > .t-Form-inputContainer")
        checkbox_state = checkbox.locator("input[type='hidden']").get_attribute("value") == "1"
        if overschrijf_bestaande_inrichting != checkbox_state:
            checkbox.locator("label").click()

        sleep(4)
        uploadvenster.locator("input[type='file']").set_input_files(maisxml)

        # check of filename in het uploadvenster voorkomt
        if not uploadvenster.get_by_text(maisxml.name).is_visible():
            log.warn(f"Upload van {maisxml.name} is niet geslaagd")
            sleep(5)
            uploadvenster.get_by_role("button", name="Annuleren").click()
            pogingen -= 1
            continue

        uploadvenster.get_by_role("button", name="Ok").click()
        log.info(f"Upload van {maisxml.name} is geslaagd; wachten tot MAIS de XML heeft verwerkt...")
        # TODO: this is a long wait, maybe inform the user?
        # TODO: maybe the timeout shouldn't be infinite?
        page.wait_for_function("document.querySelector('.js')?.textContent?.includes('Wacht op beoordeling')", timeout=0)

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
            "fout" in logtext.lower()
            or "error" in logtext.lower()
            or "Einde van importeren" not in logtext
            or len(logtext.split("\n")) > 22 # more than 22 lines is probably also problematic
        ):
            log.warn(f"MIAS heeft een fout gevonden in {maisxml}; zie {logfile} voor meer informatie")
            pogingen -= 1
            # The only way to cancel is to wait, for some reason, so wait 8min
            sleep(8 * 60)
            page.reload()
            sleep(3)
            page.get_by_role("button", name=" Sluiten").click()
            page.reload()
            continue
        else:
            page.get_by_role("button", name="OK").click()
            log.info(f"{maisxml} lijkt foutloos verwerkt ✅")
            return True

    # upload was niet succesvol
    return False
