import argparse
import logging
import playmais
from time import sleep
from playwright.sync_api import sync_playwright
from playwright.sync_api import Error as PlaywrightError

# TODO: return success status?
def main():
    default_retries = 8
    log = logging.getLogger(__name__)

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
        help="Overschrijf bestaande inrichting",
        action="store_true",
    )
    parser.add_argument(
        "-r",
        "--retries-on-error",
        help=f"Hoe vaak de upload opnieuw moet worden geprobeerd na een error (default: {default_retries})",
        default=default_retries,
        type=int,
    )
    args = parser.parse_args()

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=not args.no_headless)
        context = browser.new_context()
        page = context.new_page()
        playmais.login(page)

        for file in args.files:
            retries_on_error = args.retries_on_error
            upload_in_progress = True
            while retries_on_error and upload_in_progress:
                try:
                    playmais.upload_maisxml(
                        page,
                        file,
                        nieuwe_guids=args.behoud_guids,
                        overschrijf_bestaande_inrichting=args.overschrijf_inrichting,
                    )
                    upload_in_progress = False
                except PlaywrightError as e:
                    increment_delay = ((args.retries_on_error - retries_on_error) + 1)**1.2
                    retries_on_error -= 1
                    retry_after_mins = 3 * increment_delay
                    log.warning(f"Playwright-error tijdens het uploaden:\n\t{str(e).rstrip()}")

                    if retries_on_error == 0:
                        log.error(f"Teveel errors tijdens upload van {file}; upload geannuleerd")
                        exit(-1)

                    log.info(f"Upload wordt over {int(retry_after_mins)} minuten opnieuw geprobeerd")
                    sleep(60 * retry_after_mins)
                    # login again, to be safe
                    page = context.new_page()
                    playmais.login(page)
                    continue

            page.reload()
            sleep(2)
