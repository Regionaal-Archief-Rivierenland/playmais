import getpass
import os
import sys
import logging

from time import sleep
from playwright.sync_api import Playwright, sync_playwright, expect

log = logging.getLogger(__name__)

def _resolve_username():
    return os.environ.get(f"MAIS_USER") or input("MAIS gebruikersnaam: ")

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

# if we get booted, we have to redo the password. I guess one more advantage for an object-oriented model??
def login(page: Page, gebruikersnaam=None, wachtwoord=None):
    """Log in op MAIS. Als inloggen goed gaat kom je op de hoofdpagina.

    Als `gebruikersnaam` en `wachtwoord` niet zijn opgegeven, haalt deze functie
    je inloggegevens uit de _environment variables_ `MAIS_USER` en `MAIS_PASSWORD`.
    Als deze variabelen niet bestaan vraagt de functie om je inloggegevens via een
    interactieve prompt.

    Args:
        page: Page-object; wordt _in-place_ veranderd.
        user: Je MAIS gebruikersnaam. Start meestal met `RAR_`.
        wachtwoord: Je MAIS wachtwoord.

    Raises:
        RuntimeError: Login is gefaald
    """
    gebruikersnaam = gebruikersnaam or _resolve_username()
    wachtwoord = wachtwoord or _resolve_password(gebruikersnaam)

    # always move to the login page, just to be sure
    # FIXME: this URL breaks for other organisations
    page.goto("https://rar.maisflexis.com/ords/f?p=200102:LOGIN_DESKTOP::::::")
    page.get_by_role("textbox", name="Inlognaam").click()
    page.get_by_role("textbox", name="Inlognaam").fill(gebruikersnaam)
    page.get_by_role("textbox", name="Inlognaam").press("Tab")
    page.get_by_role("textbox", name="Wachtwoord").fill(wachtwoord)
    page.get_by_role("button", name="Inloggen").click()

    foutmelding = page.get_by_text("Ongeldige login naam of")
    _2fa = page.get_by_role("textbox", name="Geef code in")
    homepage = page.locator("#uBreadcrumbs").get_by_text("Welkom")
    
    expect(foutmelding.or_(_2fa).or_(homepage)).to_be_visible()

    if foutmelding.is_visible():
        raise RuntimeError("Ongeldige gebruikersnaam of wachtwoord")

    if _2fa.is_visible():
        _2fa.fill(_resolve_2fa(gebruikersnaam))
        page.get_by_role("button", name="Inloggen").click()
        expect(foutmelding.or_(homepage)).to_be_visible()
        if foutmelding.is_visible():
            raise RuntimeError(f"Ongeldige 2fa code voor {gebruikersnaam}")

    log.info(f"Succesvol ingelogd als {gebruikersnaam}!")
