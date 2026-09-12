import argparse
import logging
from pathlib import Path
import playmais
from time import sleep
from playwright.sync_api import sync_playwright

dim_s, dim_e = "\033[90m", "\033[0m"
example_usage = f"""Bijvoorbeeld:
  {dim_s}# Download meerdere groepen{dim_e}
  download_maisxml Affiches AV-collectie "Uitplaatsing Culemborg"

  {dim_s}# Download specifiecke toegangcodes{dim_e}
  download_maisxml -c 1854 1722

  {dim_s}# Zowel codes als groepnamen{dim_e}
  download_maisxml AV-collectie -c 1854"""

# TODO: return success status?
def main():
    # TODO: add n of workers (though this needs more smart matching with notifs etc)
    parser = argparse.ArgumentParser(
        description="Download MAIS XML bestanden op basis van toegangscodes of toegangsgroepnamen",
        epilog=example_usage,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "groepnaam", help="Naam of namen van toegangsgroepen om te downloaden", nargs="*"
    )
    parser.add_argument(
        "-c",
        "--toegangcodes",
        help="Toegangcode(s) om te downloaden. Niet verplicht, en kan samen met groepnamen worden gebruikt.",
        metavar="CODE",
        nargs="+",
    )
    parser.add_argument(
        "-o",
        "--output-directory",
        help="Locatie voor gedownloade MAIS XML bestanden. Default is huidige directory",
        default=Path.cwd()
    )
    parser.add_argument(
        "-d",
        "--no-headless",
        help="Run playwright in niet-headless mode",
        action="store_true",
    )
    # todo: maybe this needs to be another endpoint
    # FIXME: unimplemented
    parser.add_argument(
        "-l",
        "--list-toegangsgroepen",
        help="Print alle toegangsgroepen & exit",
        action="store_true",
    )
    args = parser.parse_args()

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=not args.no_headless)
        context = browser.new_context()
        page = context.new_page()

        if args.list_toegangsgroepen:
            # be quiet
            log = logging.getLogger(__name__)
            logging.disable(logging.INFO)

        playmais.login(page)

        if args.list_toegangsgroepen:
            print("\n".join(playmais.list_toegangsgroepen(page)))
            return

        for groepnaam in args.groepnaam:
            playmais.download_maisxml_van_toegansgroep(page, groepnaam, args.output_directory)
        
        if args.toegangcodes:
            playmais.download_maisxml_van_toegangcodes(page, args.toegangcodes, args.output_directory)

        page.reload()
        sleep(1)
