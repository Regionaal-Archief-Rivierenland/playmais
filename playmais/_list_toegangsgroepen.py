import re
from ._helpers import retry_on_playwright_error
from time import sleep

@retry_on_playwright_error(retries=3)
def list_toegangsgroepen(self) -> list[str]:
    """Vraag alle toegangsgroepen op.

    Returns:
       list[str]: lijst met de namen van alle toegangsgroepen.
    """
    self.page.locator("div").filter(has_text=re.compile(r"^Beheren$")).click()
    self.page.get_by_role("link", name=" Toegangen Beheren van").click()
    sleep(1)

    return [
        groep.inner_text()
        for groep in self.page.get_by_label("Toegangsgroep").locator("option").all()
        if groep.inner_text()
    ]

