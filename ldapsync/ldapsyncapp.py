import abc
import argparse
import logging.handlers
import sys

from ocflib.account.utils import list_staff


class DestinationService(abc.ABC):
    """
    Abstract class for services that LDAPSync will sync to LDAP groups, such
    as Google Groups, RT, and Discourse.

    The two abstract methods list_members() and add_to_group() must be
    implemented.
    """

    @abc.abstractmethod
    def list_members(self, destination_group):
        """
        This method must list the OCF usernames of all OCF members in a
        destination group, such as a Google Groups group, or RT admin list.
        This method should also ignore bot accounts, such as ocfbot.
        """
        pass

    @abc.abstractmethod
    def add_to_group(self, username, destination_group):
        """
        This method must add the account associated with the OCF username
        provided to the destination group.
        """
        pass


class LDAPSyncApp(abc.ABC):

    SYNC_PAIRS = None

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
        # logging.basicConfig(format='%(asctime)s:%(levelname)s:%(module)s:%(message)s')
        formatter = logging.Formatter(
            '%(asctime)s:%(levelname)s:%(module)s:%(message)s')

        # Set logging options for the current module only.
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.getLevelName(self.args.log_level))

        # Always log to STDERR.
        stream_handler = logging.StreamHandler(stream=sys.stderr)
        stream_handler.setFormatter(formatter)
        self.logger.addHandler(stream_handler)

        if self.args.log_file is not None:
            file_handler = logging.handlers.WatchedFileHandler(
                self.args.log_file)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    @property
    @abc.abstractmethod
    def dest_service(self):
        """Return the destination service to sync to."""
        pass

    def sync(self):
        try:
            for ldap_group, dest_group in self.SYNC_PAIRS:
                ldap_members = set(list_staff(group=ldap_group))
                dest_members = set(
                    self.dest_service().list_members(dest_group))

                to_add = ldap_members - dest_members
                missing = dest_members - ldap_members

                if missing:
                    missing_header = '''The following users are in the {dest}
                            destination group but are not in the {ldap}
                            LDAP group:'''.format(
                        dest=dest_group,
                        ldap=ldap_group)
                    self.logger.warning(missing_header)
                    for m in missing:
                        self.logger.warning(m)

                for username in to_add:
                    if not self.args.dry_run:
                        self.dest_service().add_to_group(username, dest_group)
                    self.logger.info(
                        'Adding {} to group {}'.format(username, dest_group))

        except Exception as e:
            self.logger.exception('Exception caught: {}'.format(e))
