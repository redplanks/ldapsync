# ldapsync
This is a work-in-progress project to automate group syncing between various services on OCF infrastructure. LDAP should be a "source of truth" for the certain groups (like ocfstaff) within the OCF, and state of services (such as Google Apps mailing lists, Discourse groups, etc.) should be automatically updated to reflect this state.

Once this project is finished, it will run on a cronjob. It should look at LDAP state and add users to services based on that. As a failsafe, it will never remove users. Instead, if a user needs to be removed from a group, we will send an email that should be manually handled.

# Running
Run `ldapsync/ldapsync.py -n` for testing. The `-n` flag enables "dry-run" mode where no changes will actually be made. To run this for real, remove the `-n` flag.

The `--log-file` or `-l` optional flag logs everything (successful syncs, errors, and exceptions) to the given log file.

# Groups
## ocfstaff
ocfstaff is volunteer staff, and have limited access to OCF infrastructure. Most staff privileges are granted "automatically," but some access needs to be granted via this script. They should be added to RT and given access to the Google Drive.

## opstaff
Opstaff are paid front-desk staff. They should be added to the opstaff mailing list and GDrive.

## ocfofficers
Officers should be put on a Google mailing list for "external" OCF communications. They also have access to a Google Drive.

## ocfroot
Root staffers have full access to OCF infra. They should be given admin privileges on all services, like Discourse and RT.

# Services
## Google Admin (mailing list groups)
These forward emails to larger groups. We can modify this list by using the Google Admin API.

## RT
There doesn't appear to be an API for RT, but we can modify the staff group and admin groupby modifying the MySQL database directly.

## Discourse
Discourse has an API. We only use this to give admin access to root staffers.
