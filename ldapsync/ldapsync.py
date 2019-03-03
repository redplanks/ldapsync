#!/usr/bin/env python3
"""Script for syncing OCF LDAP groups with various services."""

import argparse
import logging
import pkgutil
import sys
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
    parser.add_argument(
        '--log-file',
        '-l',
        help='Log any changes and any errors to the specified file.'
    )

    args = parser.parse_args()

    logging_handlers = []
    # Always log to STDOUT.
    logging_handlers.append(logging.StreamHandler(stream=sys.stdout))

    if not args.log_file:
        logging_handlers.append(logging.FileHandler(args.log_file))

    logging.basicConfig(
        format='%(asctime)s:%(levelname)s:%(module)s:%(message)s',
        handlers=logging_handlers)

    for importer, mod_name, _ in pkgutil.iter_modules(['ldapsync/apps']):
        mod = importer.find_module(mod_name).load_module(mod_name)
        try:
            # logging functions called in sync() will inherit this one's
            # options.
            mod.sync(args.dry_run)
        except Exception as e:
            logging.exception("Exception caught: ")
            mail.send_problem_report("An exception occurred in ldapsync: \n\n{}".format(
                traceback.format_exc()))

if __name__ == '__main__':
    main()
