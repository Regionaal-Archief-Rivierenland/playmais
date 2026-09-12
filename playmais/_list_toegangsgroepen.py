import re
from playwright.sync_api import Playwright, sync_playwright
from time import sleep

def list_toegangsgroepen(page: Page) -> list[str]:
    """Return lijst met alle namen van toegansgroepen."""
    page.locator("div").filter(has_text=re.compile(r"^Beheren$")).click()
    page.get_by_role("link", name=" Toegangen Beheren van").click()
    sleep(1)

    return [
        groep.inner_text()
        for groep in page.get_by_label("Toegangsgroep").locator("option").all()
        if groep.inner_text()
    ]

