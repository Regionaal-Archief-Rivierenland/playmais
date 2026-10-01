import argparse
import playmais
from time import sleep
from playwright.sync_api import sync_playwright

# TODO: return success status?
def main():
    # TODO: add n of workers (though this needs more smart matching with notifs etc)
    parser = argparse.ArgumentParser(description="Upload MAIS XML bestanden", color=True)
    parser.add_argument(
        "files", help="MAIS XML bestand(en) om te uploaden", nargs="+", metavar="FILE.txt"
    )
    parser.add_argument(
        "-d",
        "--no-headless",
        help="Run playwright in niet-headless mode",
        action="store_true",
    )
    parser.add_argument(
        "-b",
        "--behoud-guids",
        help="Maak geen nieuwe GUIDs aan (GUIDs hebben weinig inherent waarde, dus kan meestal uit)",
        action="store_false",
    )
    parser.add_argument(
        "-o",
        "--overschrijf-inrichting",
        help="Overschrijf bestaande inrichting.",
        action="store_true",
    )
    args = parser.parse_args()

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=not args.no_headless)
        context = browser.new_context()
        page = context.new_page()
        playmais.login(page)

        for f in args.files:
            playmais.upload_maisxml(page, f, nieuwe_guids=args.behoud_guids)
            page.reload()
            sleep(2)
