import logging
import re
import zipfile
from pathlib import Path
from time import sleep

from playwright.sync_api import Playwright, expect, sync_playwright

log = logging.getLogger(__name__)

# FIXME: in obscure cases, a user (including RAR_ARA) may lack the required
# persmission to _see_ a toegang (at least on the Beheren page). These cases can
# be caught if you check the downloaded results
# FIXME: this may download the wrong thing if multiple downloads toast are present
def _download_all(page, folder):
    """Download alle toegang door ze allemaal tegelijk te selecteren"""
    folder = Path(folder)
    if folder.exists() and not folder.is_dir():
        raise ValueError(f"{folder} exists but is not a directory")

    # close all toast with status "finished", as they can obfuscate the export button
    for toast in page.locator(".toast", has_text=re.compile("Gereed")).all():
        # TODO: provide more info (bot not full inner_text, since that is tmi)
        # TODO: i18n
        log.info(f"Closing toast...")
        toast.get_by_role("button", name="×").click()

    page.get_by_role("columnheader", name="Row header ").click(force=True)
    sleep(1)
    page.get_by_role("button", name="Bewerkingen ").click(force=True)
    sleep(3)
    page.get_by_role("menuitem", name="Exporteren (uitwisselen naar").click(force=True)
    sleep(4)
    page.get_by_role("button", name="OK").click(force=True)
    sleep(5)

    export_toast = page.locator(".toast-message", has_text="Exporteren van")
    while export_toast.count() and not "Gereed" in export_toast.inner_text():
        voortang = re.search(r"(Voortgang:.*)|(Bezig met.*)", export_toast.inner_text())
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

    try:
        # good habit to close things
        page.get_by_role("button", name="×").click()
    except:
        pass

# FIXME: account for pagination
def download_maisxml_van_toegangcodes(page: Page, toegangcodes: list[str], folder: str | Path):
    """Download MAIS XML van de gegeven toegangscodes."""
    page.locator("div").filter(has_text=re.compile(r"^Beheren$")).click()
    page.get_by_role("link", name=" Toegangen Beheren van").click()
    sleep(1)
    page.get_by_role("button", name="Acties ").click()
    sleep(3)
    page.locator("span").filter(has_text="Filter").click()
    sleep(4)
    page.get_by_label("Operator").select_option("REGEXP")
    sleep(6)
    page.get_by_role("textbox", name="Waarde").click()

    toegangcodes_regex = "|".join(toegangcodes)
    page.get_by_role("textbox", name="Waarde").fill(f"^({toegangcodes_regex})$")
    page.get_by_role("button", name="Opslaan").click()
    sleep(5)

    if page.locator("#toegangen_ig_ig_grid_vc").get_by_text("Er zijn geen gegevens").is_visible():
        raise ValueError(f"Toegang(en) {','.join(toegangcodes)} lijken niet te bestaan")
        
    log.info(f"Toegang(en) {", ".join(toegangcodes)} aan het downloaden...")
    _download_all(page, folder)
    log.info(f"Toegang(en) {", ".join(toegangcodes)} zijn gedownload ✅")
    sleep(2)
    # cleanup filter we just applied
    page.get_by_role("button", name="Remove Filter").click()
    sleep(3)

def download_maisxml_van_toegansgroep(page: Page, groepnaam: str, folder: str | Path):
    """Download alle MAIS XML uit een bepaalde toegangsgroep."""
    page.locator("div").filter(has_text=re.compile(r"^Beheren$")).click()
    page.get_by_role("link", name=" Toegangen Beheren van").click()
    sleep(3)
    try:
        # click op de dropdown
        page.get_by_label("Toegangsgroep").select_option(label=groepnaam)
    except:
        raise ValueError(f"De toegangsgroep '{groepnaam}' lijkt niet te bestaan; "
        "zie `playmais.list_toegangsgroepen()` voor alle toegangsgroepen")

    sleep(5)
    log.info(f"Toegangsgroep '{groepnaam}' aan het downloaden...")
    _download_all(page, folder)
    log.info(f"Toegangsgroep '{groepnaam}' is gedownload ✅")
    # Reset toegansgroep filter
    page.get_by_label("Toegangsgroep").select_option("")
    sleep(3)
