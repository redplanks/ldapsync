from google.oauth2 import service_account
import googleapiclient.discovery

import ldapsyncapp
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

class GAppsAdminAPI(ldapsyncapp.DestinationService):
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

    def list_members(self, destination_group):
        """List all the OCF members (@ocf.berkeley.edu emails) in a GApps
        mailing list. Strips email addresses, so this only returns usernames.
        Ignores non-ocf.berkeley.edu emails and ocfbot@ocf.berkeley.edu.
        """
        response = self.groupadmin.members().list(groupKey=destination_group).execute()
        emails = (m['email'].split('@') for m in response['members'])

        return [
            username
            for username, domain in emails
            if domain == 'ocf.berkeley.edu'
            if username != 'ocfbot'
        ]

    def add_to_group(self, usernames, destination_group):
        for username in usernames:
            self.groupadmin.members().insert(
                groupKey=destination_group,
                body={'email': username + '@ocf.berkeley.edu'},
            ).execute()


class GoogleGroups(ldapsyncapp.LDAPSyncApp):

    SYNC_PAIRS = [
        ('ocfofficers', 'officers@ocf.berkeley.edu'),
    ]

    def __init__(self):
        super().__init__()
        # Add argument for the Google Apps service account JSON file.
        self.arg_parser.add_argument(
            'service_acct_json_path',
            help='Absolute path to GApps service account file.')
        self.args = self.arg_parser.parse_known_args()[0]

        self.__gapps_admin_api = GAppsAdminAPI(self.args.service_acct_json_path)

    def dest_service(self):
        return self.__gapps_admin_api


if __name__ == '__main__':
    google_groups_app = GoogleGroups()
    google_groups_app.sync()
