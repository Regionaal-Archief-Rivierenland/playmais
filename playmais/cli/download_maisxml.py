import argparse
import logging
from pathlib import Path
import playmais
from time import sleep

dim_s, dim_e = "\033[90m", "\033[0m"
example_usage = f"""Bijvoorbeeld:
  {dim_s}# Download meerdere groepen{dim_e}
  download_maisxml Affiches AV-collectie "Uitplaatsing Culemborg"

  {dim_s}# Download specifiecke toegangscodes{dim_e}
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
        "--toegangscodes",
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

    if args.list_toegangsgroepen:
        # be quiet
        log = logging.getLogger(__name__)
        logging.disable(logging.INFO)

    with playmais.Playmais(headless=not args.no_headless) as pm:
        if args.list_toegangsgroepen:
            print("\n".join(pm.list_toegangsgroepen()))
            return

        for groepnaam in args.groepnaam:
            pm.download_maisxml_van_toegangsgroep(groepnaam, args.output_directory)

        if args.toegangscodes:
            pm.download_maisxml_van_toegangscodes(args.toegangscodes, args.output_directory)

        pm.reload()
        sleep(1)
