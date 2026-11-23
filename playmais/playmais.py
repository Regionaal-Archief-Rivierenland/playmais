import logging
import sys
import os
import weakref
from playwright.sync_api import sync_playwright, expect
from ._helpers import retry_on_playwright_error

log = logging.getLogger(__name__)

## Login helpers
def _resolve_password(user):
    if pw := os.environ.get(f"MAIS_PASSWORD") or os.environ.get(f"MAIS_PASS"):
        return pw
    if not sys.stdin.isatty():
        raise RuntimeError(f"not running in an interactive shell; set MAIS_PASSWORD")
    return getpass.getpass(f"Password ({user}): ", echo_char="*")

def _resolve_2fa(user):
    # TODO: i guess people may want to enter 2fa codes in the browser?
    if not sys.stdin.isatty():
        raise RuntimeError(f"encountered 2fa prompt, but not running in an interactive shell")
    return input(f"2FA code ({user}): ")

def _resolve_username():
    return os.environ.get(f"MAIS_USER") or input("MAIS gebruikersnaam: ")

# TODO: maybe move login documentation here?
# Maybe move example to main module docstring?
class Playmais():
    """Create a new playmais object. Zie quickstart voor een korte
    introductie.

    Sectie over inloggen

    Example:
       ```python
       playmais = Playmais()
       playmais.download_maisxml_van_toegangscodes(["1853", "1854"])
       ```

    Args:
        browser[Optional]: use this to change e.g. screensize
    """
    def __init__(self, username: Optional[str] = None, password: Optional[str] = None, headless=True, browser=None, context_kwargs=None):
        self._playwright = sync_playwright().start()
        self.browser = browser if browser else self._playwright.chromium.launch(headless=headless)
        # TODO: use context_kwargs (maybe do the same for browser?)
        self.context = self.browser.new_context(viewport={"width": 1920, "height": 1080})
        # weakref.finalize has the "side-effect" of associating `self` with a
        # custom cleanup method during garbage collection
        self._stop_playwright = weakref.finalize(self, self._playwright.stop)
        self.login(username, password)

    def close(self):
        """Teardown playwright instance. Optional, but safes memory
        if a program performs a lot of work *after* browser automation.
        """
        self._stop_playwright()

    # __enter__ and __exit__ are used for with blocks
    def __enter__(self):
        return self # within `with X() as y`, __enter__ handles assigning `y`

    def __exit__(self, *_): # __exit__ expects 3 extra params we don't need
        self.close()

    def reload(self):
        """Herlaad de huidige pagina."""
        self.page.reload()

    from ._upload_maisxml import upload_maisxml
    from ._download_maisxml import download_maisxml_van_toegangscodes, download_maisxml_van_toegangsgroep
    from ._list_toegangscodes import list_toegangscodes
    from ._list_toegangsgroepen import list_toegangsgroepen


    # Why even expose this in first place if __init__ handles this?
    # FIXME: if we expose this, we may need to handle logging out
    @retry_on_playwright_error(retries=12, minutes_to_sleep=10)
    def login(self, gebruikersnaam=None, wachtwoord=None):
        """Log in op MAIS. Als inloggen goed gaat kom je op de hoofdpagina.

        Als `gebruikersnaam` en `wachtwoord` niet zijn opgegeven, haalt deze functie
        je inloggegevens uit de *environment variables* `MAIS_USER` en `MAIS_PASSWORD`.
        Als deze variabelen niet bestaan vraagt de functie om je inloggegevens via een
        interactieve prompt.

        Args:
            user: Je MAIS gebruikersnaam.
            wachtwoord: Je MAIS wachtwoord.

        Raises:
            RuntimeError: Login is gefaald
        """
        self.page = self.context.new_page()
        gebruikersnaam = gebruikersnaam or _resolve_username()
        wachtwoord = wachtwoord or _resolve_password(gebruikersnaam)

        # FIXME: this URL breaks for other organisations
        self.page.goto("https://rar.maisflexis.com/ords/f?p=200102:LOGIN_DESKTOP::::::")
        self.page.get_by_role("textbox", name="Inlognaam").click()
        self.page.get_by_role("textbox", name="Inlognaam").fill(gebruikersnaam)
        self.page.get_by_role("textbox", name="Inlognaam").press("Tab")
        self.page.get_by_role("textbox", name="Wachtwoord").fill(wachtwoord)
        self.page.get_by_role("button", name="Inloggen").click()

        foutmelding = self.page.get_by_text("Ongeldige login naam of")
        _2fa = self.page.get_by_role("textbox", name="Geef code in")
        homepage = self.page.locator("#uBreadcrumbs").get_by_text("Welkom")

        expect(foutmelding.or_(_2fa).or_(homepage)).to_be_visible()

        if foutmelding.is_visible():
            raise RuntimeError("Ongeldige gebruikersnaam of wachtwoord")

        if _2fa.is_visible():
            _2fa.fill(_resolve_2fa(gebruikersnaam))
            self.page.get_by_role("button", name="Inloggen").click()
            expect(foutmelding.or_(homepage)).to_be_visible()
            if foutmelding.is_visible():
                raise RuntimeError(f"Ongeldige 2fa code voor {gebruikersnaam}")

        log.info(f"Succesvol ingelogd als {gebruikersnaam}!")
