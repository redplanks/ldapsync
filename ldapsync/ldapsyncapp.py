import abc
import argparse
import logging
import logging.handlers
import sys

import emailbufferinghandler


class LDAPSyncApp(abc.ABC):
    def __init__(self):
        # Add required flags for all apps. Add new ones in child classes,
        # but don't forget to run parse_known_args() again.
        self.arg_parser = argparse.ArgumentParser(description=__doc__)
        self.arg_parser.add_argument(
            '--dry-run',
            '-n',
            action='store_true',
            help='Do not make changes, but show what would be done.'
        )
        self.arg_parser.add_argument(
            '--log-file',
            '-l',
            default=None,
            help='Log any changes and any errors to the specified file.'
        )
        self.arg_parser.add_argument(
            '--log-level',
            choices=(
                'CRITICAL',
                'ERROR',
                'WARNING',
                'INFO',
                'DEBUG',
            ),
            default='WARNING',
            help='Logging level to set for app.',
        )
        # parse_known_args() gives a tuple; we only care about parsed args,
        # which is the first element.
        self.args = self.arg_parser.parse_known_args()[0]

        # Set logger format.
        formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(module)s:%(message)s')

        # Set logging options for the current module only.
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.getLevelName(self.args.log_level))

        # Always log to STDOUT.
        stream_handler = logging.StreamHandler(stream=sys.stdout)
        stream_handler.setFormatter(formatter)
        self.logger.addHandler(stream_handler)

        # Log everything to an email buffer, so we can email all log messages
        # at the end of a sync.
        self.email_buffering_handler = emailbufferinghandler.EmailBufferingHandler()
        self.email_buffering_handler.setFormatter(formatter)
        self.logger.addHandler(self.email_buffering_handler)

        if self.args.log_file is not None:
            file_handler = logging.handlers.WatchedFileHandler(self.args.log_file)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)


    @abc.abstractmethod
    def sync(self):
        pass
