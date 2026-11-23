import logging
import re
from ._helpers import retry_on_playwright_error
from time import sleep
from playwright.sync_api import Page

log = logging.getLogger(__name__)


# returns a list because toegangcodes can be duplicates??
def _extract_toegangscodes_from_table(page: Page) -> list[str]:
    # we need a fairly specific locator because there are 4(!) tables on this page
    return [
        td.inner_html()
        for td in page.locator("tr[data-rownum] > td:nth-child(2)").all()
    ]


# TODO: get this from the table is kinda inefficient. You could rewrite this to
# analyze the csv you get if you click "Acties>download rapport".
# While the superior approach, this whole function isn't super useful atm
@retry_on_playwright_error(retries=7, minutes_to_sleep=2, sleep_exponent=1)
def list_toegangscodes(self, groepnaam: Optional[str | None] = None) -> set[str]:
    """Vind ("list") toegangscodes, bijvoorbeeld alle codes binnen de toegangsgroep
    `groepnaam`.

    Args: groepnaam (Optional[str | None]): Wanneer je dit leeg laat, krijg alle
       bestaande toegangsgroepen terug.

    """
    self.page.locator("div").filter(has_text=re.compile("^Beheren$")).click()
    self.page.get_by_role("link", name=" Toegangen Beheren van").click()
    sleep(2)

    try:
        if groepnaam:
            self.page.get_by_label("Toegangsgroep").select_option(label=groepnaam)
    except:
        raise ValueError(
            f"De toegangsgroep '{groepnaam}' lijkt niet te bestaan; "
            "zie `list_toegangsgroepen()` voor alle toegangsgroepen"
        )
    sleep(4)

    # high max. since we may need to find _all_ toegangscodes
    self.page.get_by_role("button", name="Acties ").click()
    self.page.get_by_role("menuitem", name="Rapport indeling").hover()
    self.page.get_by_role("menuitem", name="Rijen per pagina").hover()
    self.page.locator("span").filter(has_text=re.compile(r"^1000$")).click()
    sleep(1)

    toegangscodes = []
    volgende_btn = self.page.get_by_role("button", name="Volgende")
    toegangscodes.extend(_extract_toegangscodes_from_table(self.page))
    while volgende_btn.is_enabled():
        volgende_btn.click()
        sleep(4)
        toegangscodes.extend(_extract_toegangscodes_from_table(self.page))

    # TODO: is this log useful at all?
    log.info(
        f"{len(toegangscodes)} toegangscodes gevonden{'in ' + toegangsgroep if groepnaam else ''}"
    )
    return toegangscodes
