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

from google.oauth2 import service_account
import googleapiclient.discovery

from ocflib.account.utils import list_staff


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


def sync(dry_run):
    admin_api = GAppsAdminAPI('ocf-ldap-sync-5ad44e88518c.json')
    for groupname, mailname in SYNC_PAIRS:
        group = set(list_staff(group=groupname))
        mailing_list = set(admin_api.list_members(mailname))

        to_add = group - mailing_list
        missing = mailing_list - group

        if missing:
            print(
                'The following users are in the {mailname} mailing list but '
                'are not in the {groupname} LDAP group:\n'.format(
                    mailname=mailname,
                    groupname=groupname,
                )
            )
            for m in missing:
                print(m)

            print()

        for username in to_add:
            if not dry_run:
                add_to_group(username, mailname)
            else:
                print('Add {} to group {}'.format(username, mailname))
    
if __name__ == '__main__':
    main()
