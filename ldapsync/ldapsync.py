#!/usr/bin/env python3
"""Script for syncing OCF LDAP groups with various services."""

import argparse
import logging
import pkgutil
import traceback
from ocflib.misc import mail


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--dry-run',
        '-n',
        action='store_true',
        help='Do not make changes, but show what would be done.'
    )

    args = parser.parse_args()

    logging.basicConfig(format='%(asctime)s:%(levelname)s:%(module)s:%(message)s')

    for importer, mod_name, _ in pkgutil.iter_modules(['ldapsync/apps']):
        mod = importer.find_module(mod_name).load_module(mod_name)
        try:
            mod.sync(args.dry_run)
        except Exception as e:
            print(traceback.format_exc())
            logging.exception("Exception caught: ")
            mail.send_problem_report(f"An exception occurred in ldapsync: \n\n
                    {traceback.format_exc()}")

if __name__ == '__main__':
    main()
