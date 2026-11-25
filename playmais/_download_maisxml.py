import logging
import re
import zipfile
from pathlib import Path
from time import sleep
from ._list_toegangscodes import _all_toegangscodes_paginate
from ._helpers import retry_on_playwright_error
from playwright.sync_api import Page

log = logging.getLogger(__name__)

# TODO: now that we know what toegangscodes are in a toegangsgroep, we can actually resume downloads!

# FIXME: in obscure cases, a user (including RAR_ARA) may lack the required
# persmission to _see_ a toegang (at least on the Beheren page). These cases can
# be caught if you check the downloaded results
# FIXME: this may download the wrong thing if multiple downloads toast are present
def _download_all(page: Page, folder, toegangsgroep=None):
    """Download alle toegang door ze allemaal tegelijk te selecteren"""
    folder = Path(folder)
    if folder.exists() and not folder.is_dir():
        raise ValueError(f"{folder} exists but is not a directory")

    # close all toast with status "finished", as they can obfuscate the export button
    for toast in page.locator(".toast", has_text=re.compile("Gereed")).all():
        toast.get_by_role("button", name="×").click()
        log.info(f"Toast van een oude download sessie gesloten")

    toegangscodes_to_be_downloaded = _all_toegangscodes_paginate(page) # NOTE: sets a high row count
    # Is one of the toegangscodes to be downloaded present in the body of the toast?
    # If so, we can resume a previous export
    export_toast = page.locator(
        ".toast-message",
        has_text=re.compile(
            rf'Exporteren van \w+ "({"|".join(toegangscodes_to_be_downloaded)}) '
        ),
    )

    if export_toast.count():
        if toegangsgroep:
            log.info(f"Download van toegangsgroep '{toegangsgroep}' hervat...")
        else:
            log.info(f"Download van toegang(en) {', '.join(toegangscodes_to_be_downloaded)} hervat...")
    else:
        # start new download
        page.get_by_role("columnheader", name="Row header ").click(force=True) # select all
        sleep(1)
        page.get_by_role("button", name="Bewerkingen ").click(force=True)
        sleep(3)
        page.get_by_role("menuitem", name="Exporteren (uitwisselen naar").click(force=True)
        sleep(4)
        page.get_by_role("button", name="OK").click(force=True)
        if toegangsgroep:
            log.info(f"Toegangsgroep '{toegangsgroep}' aan het downloaden...")
        else:
            log.info(f"Toegang(en) {', '.join(toegangscodes_to_be_downloaded)} aan het downloaden...")

    # wait for toast to show up
    export_toast.wait_for(timeout=20_000) # wait 20s max
    if not export_toast.is_visible():
        raise RuntimeError("Kan juiste export toast niet vinden")

    while export_toast.count() and "Gereed" not in export_toast.inner_text():
        voortang = re.search(r"(Voortgang:.*)|(Exporteren van.*)", export_toast.inner_text())
        print(f"\033[K{voortang.group() if voortang else ''}", end="\r", flush=True)
        page.reload()
        sleep(20)

    # click available download links
    links = page.get_by_role("link", name=re.compile(r"^\[.*Download exportbestand "))
    for link in links.all():
        with page.expect_download() as download_info:
            link.click()

        download = download_info.value
        download_dst = folder / download.suggested_filename
        download.save_as(download_dst)

        # a download may come in the form of a zip or a .txt file
        if download_dst.suffix == ".zip":
            with zipfile.ZipFile(download_dst, 'r') as zip_ref:
                zip_ref.extractall(folder)
            # delete original zip
            download_dst.unlink()

    # good habit to close things
    sleep(5)
    try:
        # this is a best effor currently because there can be any number of close
        # buttons, not all of which have something to do with this download
        # session
        page.get_by_role("button", name="×").click()
    except:
        pass

# FIXME: account for pagination
@retry_on_playwright_error(retries=5, minutes_to_sleep=1, sleep_exponent=1)
def download_maisxml_van_toegangscodes(self, toegangscodes: list[str], folder: str | Path):
    """Download MAIS XML van de gegeven toegangscodes.

    Args:
        toegangscodes (list[str]): lijst van toegangscodes om te downloaden
        folder (str | Path): Folder om de MAIS XML in te downloaden
    """
    self.page.locator("div").filter(has_text=re.compile(r"^Beheren$")).click()
    self.page.get_by_role("link", name=" Toegangen Beheren van").click()
    sleep(1)
    self.page.get_by_role("button", name="Acties ").click()
    sleep(3)
    self.page.locator("span").filter(has_text="Filter").click()
    sleep(4)
    self.page.get_by_label("Operator").select_option("REGEXP")
    sleep(6)
    self.page.get_by_role("textbox", name="Waarde").click()

    toegangscodes_regex = "|".join(toegangscodes)
    self.page.get_by_role("textbox", name="Waarde").fill(f"^({toegangscodes_regex})$")
    self.page.get_by_role("button", name="Opslaan").click()
    sleep(5)

    if self.page.locator("#toegangen_ig_ig_grid_vc").get_by_text("Er zijn geen gegevens").is_visible():
        raise ValueError(f"Toegang(en) {','.join(toegangscodes)} lijken niet te bestaan")
        
    _download_all(self.page, folder)
    log.info(f"Toegang(en) {", ".join(toegangscodes)} zijn gedownload ✅")
    sleep(2)
    # cleanup filter we just applied
    self.page.get_by_role("button", name="Remove Filter").click()
    sleep(1)

@retry_on_playwright_error(retries=5, minutes_to_sleep=1, sleep_exponent=1)
def download_maisxml_van_toegangsgroep(self, groepnaam: str, folder: str | Path):
    """Download alle MAIS XML uit een bepaalde toegangsgroep.

    Args:
        toegangscodes (str): Naam van de toegangsgroep om te downloaden
        folder (str | Path): Folder om de MAIS XML in te downloaden
    """
    self.page.locator("div").filter(has_text=re.compile(r"^Beheren$")).click()
    self.page.get_by_role("link", name=" Toegangen Beheren van").click()
    sleep(3)
    try:
        # click op de dropdown
        self.page.get_by_label("Toegangsgroep").select_option(label=groepnaam)
    except:
        raise ValueError(f"De toegangsgroep '{groepnaam}' lijkt niet te bestaan; "
        "zie `playmais.list_toegangsgroepen()` voor alle toegangsgroepen")

    sleep(5)
    _download_all(self.page, folder, groepnaam)
    log.info(f"Toegangsgroep '{groepnaam}' is gedownload ✅")
    # Reset toegangsgroep filter
    self.page.get_by_label("Toegangsgroep").select_option("")
    sleep(1)
