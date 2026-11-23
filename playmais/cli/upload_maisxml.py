import argparse
import logging
import playmais
from time import sleep

# TODO: return success status?
def main():
    log = logging.getLogger(__name__)

    # TODO: add n of workers (though this needs more smart matching with notifs etc)
    parser = argparse.ArgumentParser(
        description="Upload MAIS XML bestanden", color=True
    )
    parser.add_argument(
        "files",
        help="MAIS XML bestand(en) om te uploaden",
        nargs="+",
        metavar="FILE.txt",
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
        action="store_false",
    )
    args = parser.parse_args()
    with playmais.Playmais(headless=not args.no_headless) as pm:
        for file in args.files:
            pm.upload_maisxml(
                file,
                nieuwe_guids=args.behoud_guids,
                overschrijf_bestaande_inrichting=args.overschrijf_inrichting,
            )
            pm.reload()
            sleep(2)
