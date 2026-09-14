import logging
import re
import zipfile
from pathlib import Path
from time import sleep

from playwright.sync_api import Playwright, expect, sync_playwright

log = logging.getLogger(__name__)

def _download_all(page, folder):
    """Download alle toegang door ze allemaal tegelijk te selecteren"""
    folder = Path(folder)
    if folder.exists() and not folder.is_dir():
        raise ValueError(f"{folder} exists but is not a directory")

    page.get_by_role("columnheader", name="Row header ").click()
    sleep(1)
    page.get_by_role("button", name="Bewerkingen ").click()
    sleep(3)
    page.get_by_role("menuitem", name="Exporteren (uitwisselen naar").click()
    sleep(4)
    page.get_by_role("button", name="OK").click()

    links = page.get_by_role("link", name=re.compile(r"^\[.*Download exportbestand "))
    expect(links.first).to_be_visible(timeout=0)

    for link in links.all():
        with page.expect_download() as download_info:
            link.click()

        download = download_info.value
        download_dst = folder / download.suggested_filename
        download.save_as(download_dst)

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

# TODO: account for max rows etc.
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
    page.get_by_role("textbox", name="Waarde").fill(f"({toegangcodes_regex})")
    page.get_by_role("button", name="Opslaan").click()
    sleep(5)

    if page.locator("#toegangen_ig_ig_grid_vc").get_by_text("Er zijn geen gegevens").is_visible():
        raise ValueError(f"Toegang(en) {','.join(toegangcodes)} lijken niet te bestaan")
        
    log.info(f"Toegang(en) {", ".join(toegangcodes)} aan het downloaden...")
    _download_all(page, folder)
    log.info(f"Toegang(en) {", ".join(toegangcodes)} zijn gedownload ✅")
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
