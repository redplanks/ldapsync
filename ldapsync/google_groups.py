import logging

from google.oauth2 import service_account
import googleapiclient.discovery

from ocflib.account.utils import list_staff
from ocflib.misc import mail

from ldapsyncapp import LDAPSyncApp
"""LDAP -> GApps Group (mailing list) one-way sync.

This script adds users in an LDAP group to a Google Group.
"""

"""
Some reading material for understanding the Google APIs:
https://developers.google.com/api-client-library/python/auth/service-accounts
https://developers.google.com/admin-sdk/directory/v1/quickstart/python

https://developers.google.com/admin-sdk/directory/v1/reference/members/list
https://developers.google.com/admin-sdk/directory/v1/reference/members/insert
"""

"""
Questions:
How to do alerting? do we want to be silent on success? or do stderr for some things?
How to store the sync pairs? Config file or command line args?
"""

SYNC_PAIRS = [
    ('ocfofficers', 'officers@ocf.berkeley.edu'),
]


class GAppsAdminAPI:
    def __init__(self, service_account_file_path):
        scopes = [
            'https://www.googleapis.com/auth/admin.directory.group.member',
        ]
        credentials = service_account.Credentials.from_service_account_file(
            service_account_file_path,
            scopes=scopes,
        )
        delegated_credentials = credentials.with_subject(
            'ocfbot@ocf.berkeley.edu'
        )

        self.groupadmin = googleapiclient.discovery.build(
            'admin',
            'directory_v1',
            credentials=delegated_credentials,
        )

    def list_members(self, list_name):
        """List all the OCF members (@ocf.berkeley.edu emails) in a GApps
        mailing list. Strips email addresses, so this only returns usernames.
        Ignores non-ocf.berkeley.edu emails and ocfbot@ocf.berkeley.edu.
        """
        response = self.groupadmin.members().list(groupKey=list_name).execute()
        emails = (m['email'].split('@') for m in response['members'])

        return [
            username
            for username, domain in emails
            if domain == 'ocf.berkeley.edu'
            if username != 'ocfbot'
        ]

    def add_to_group(self, usernames, list_name):
        for username in usernames:
            self.groupadmin.members().insert(
                groupKey=list_name,
                body={'email': username + '@ocf.berkeley.edu'},
            ).execute()


class GoogleGroups(LDAPSyncApp):
    def __init__(self):
        super().__init__()
        # Add argument for the Google Apps service account JSON file.
        self.arg_parser.add_argument(
            'service_acct_json_path',
            help='Absolute path to GApps service account file.')
        self.args = self.arg_parser.parse_known_args()[0]

    def sync(self):
        try:
            admin_api = GAppsAdminAPI(self.args.service_acct_json_path)

            for groupname, mailname in SYNC_PAIRS:
                group = set(list_staff(group=groupname))
                mailing_list = set(admin_api.list_members(mailname))

                to_add = group - mailing_list
                missing = mailing_list - group

                if missing:
                    missing_header = 'The following users are in the {mailname} mailing list but are not in the {groupname} LDAP group:'.format(
                                         mailname=mailname,
                                         groupname=groupname)
                    self.logger.warning(missing_header)
                    # Alphabetically sort, so every email is the same
                    # if nothing changes about the list.
                    missing = sorted(missing)
                    for m in missing:
                        self.logger.warning(m)

                for username in to_add:
                    if not self.args.dry_run:
                        admin_api.add_to_group(username, mailname)
                    self.logger.info('Adding {} to group {}'.format(username, mailname))

            # Send an ocflib problem report email with all log messages.
            self.email_buffering_handler.flush()

        except Exception as e:
            self.logger.exception("Exception caught: {}".format(e))
            mail.send_problem_report("An exception occurred in ldapsync: \n\n{}".format(e))

if __name__ == '__main__':
    google_groups_app = GoogleGroups()
    google_groups_app.sync()
