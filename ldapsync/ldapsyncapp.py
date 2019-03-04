import abc
import argparse
import logging
import sys

class LDAPSyncApp(abc.ABC):
    def __init__(self):
        # Add required flags for all apps. Add new ones in child classes,
        # but don't forget to run parse_args() again.
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
        self.args = self.arg_parser.parse_known_args()[0]

        # Set logger format.
        # logging.basicConfig(format='%(asctime)s:%(levelname)s:%(module)s:%(message)s')
        formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(module)s:%(message)s')

        # Set logging options for the current module only.
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        # Always log to STDOUT.
        stream_handler = logging.StreamHandler(stream=sys.stdout)
        stream_handler.setFormatter(formatter)
        self.logger.addHandler(stream_handler)

        if self.args.log_file is not None:
            file_handler = logging.FileHandler(self.args.log_file)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)


    @abc.abstractmethod
    def sync(self):
        pass