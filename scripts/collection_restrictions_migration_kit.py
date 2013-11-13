## This file is part of Invenio.
## Copyright (C) 2007, 2008, 2009, 2010, 2011 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""
This script will migrate collection restriction rules from previous
Apache-only method (column restricted in the collection table) to
enhanced FireRole/WebAccess aware mode.
"""

import sys

if sys.hexversion < 0x2040000:
    # pylint: disable=W0622
    from sets import Set as set
    # pylint: enable=W0622

from invenio.legacy.dbquery import run_sql
from invenio.access_control_admin import acc_add_authorization, acc_add_role, \
    acc_get_action_id
from invenio.access_control_firerole import compile_role_definition, serialize
from invenio.access_control_config import VIEWRESTRCOLL

CFG_PROPOSED_ROLE_NAME = "%s group"
CFG_PROPOSED_ROLE_DESCRIPTION = "Group to access the following restricted collection(s): %s."

def retrieve_restricted_collection():
    """Return a dictionary with collectionname -> apache group."""

    res = run_sql('SELECT name, restricted FROM collection WHERE restricted<>""')
    if res:
        return dict(res)
    else:
        return {}

def get_collections_for_group(restrictions, given_group):
    """Return a list of collections name accessible by the given group."""
    collections = []
    for collection, group in restrictions.iteritems():
        if group == given_group:
            collections.append(collection)
    return collections

def create_needed_roles(restrictions, apache_group):
    """Create a role for the corresponding apache_group."""

    role_name = CFG_PROPOSED_ROLE_NAME % apache_group
    role_description = CFG_PROPOSED_ROLE_DESCRIPTION % ', '.join(get_collections_for_group(restrictions, apache_group))
    role_definition_src = 'allow apache_group "%s"' % apache_group
    print "Creating role '%s' ('%s') with firerole '%s'..." % (role_name, role_description, role_definition_src),
    res = acc_add_role(role_name, role_description, serialize(compile_role_definition(role_definition_src)), role_definition_src)
    if res == 0:
        print "Already existed!"
    else:
        print "OK!"
    return role_name

def migrate_restricted_collection(collection_name, role_name):
    """Migrate a single collection restriction."""

    print "Adding authorization to role '%s' for viewing collection '%s'..." % (role_name, collection_name),
    acc_add_authorization(role_name, VIEWRESTRCOLL, collection=collection_name)
    print "OK!"

def check_viewrestrcoll_exists():
    """Security check for VIEWRESTRCOLL to exist."""
    res = acc_get_action_id(VIEWRESTRCOLL)
    if not res:
        print "ERROR: %s action does not exist!" % VIEWRESTRCOLL
        print "Please run first webaccessadmin -a in order to update the system"
        print "to newly added actions."
        sys.exit(1)

def migrate():
    """Core."""
    check_viewrestrcoll_exists()
    restrictions = retrieve_restricted_collection()
    apache_groups = set(restrictions.values())

    print "%i restrictions to migrate" % len(restrictions.keys())
    print "%i roles to create" % len(apache_groups)
    role_names = {}
    for apache_group in apache_groups:
        role_names[apache_group] = create_needed_roles(restrictions, apache_group)
    for collection_name, apache_group in restrictions.iteritems():
        migrate_restricted_collection(collection_name, role_names[apache_group])

if __name__ == "__main__":
    migrate()
