# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014, 2015 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""Define authorization actions and checks."""

from invenio.base.globals import cfg
from invenio.legacy.bibrecord import get_fieldvalues
from invenio.modules.collections.cache import collection_reclist_cache, \
    get_collection_reclist, restricted_collection_cache


def check_email_or_group(user_info, email_or_group):
    """Check user email or group matches."""
    if email_or_group in user_info['group']:
        return True
    email = email_or_group.strip().lower()
    if user_info['email'].strip().lower() == email:
        return True


def check_uid(user_info, uid):
    """Check user id matches."""
    return unicode(user_info['id']) == uid


def check_authorized_tags(recid, tags, test_func):
    """Check if tags in record matches a given test."""
    authorized_values = []
    for tag in tags:
        authorized_values.extend(get_fieldvalues(recid, tag))

    for value in authorized_values:
        if test_func(value):
            return True
    return False


def is_user_in_tags(recid, user_info, user_id_tags, email_or_group_tags):
    """Check if user id or email is found in a records tags."""
    if check_authorized_tags(recid, user_id_tags,
                             lambda uid: check_uid(user_info, uid)):
        return True

    return check_authorized_tags(
        recid, email_or_group_tags,
        lambda val: check_email_or_group(user_info, val)
    )


def is_user_owner_of_record(user_info, recid):
    """Check if the user is owner of the record.

    I.e. he is the submitter and/or belongs to a owner-like group authorized
    to 'see' the record.

    :param user_info: the user_info dictionary that describe the user.
    :type user_info: user_info dictionary
    :param recid: the record identifier.
    :type recid: positive integer
    :return: True if the user is 'owner' of the record; False otherwise
    """
    from invenio.modules.access.local_config import \
        CFG_ACC_GRANT_AUTHOR_RIGHTS_TO_EMAILS_IN_TAGS, \
        CFG_ACC_GRANT_AUTHOR_RIGHTS_TO_USERIDS_IN_TAGS

    uid_tags = cfg.get('CFG_ACC_GRANT_AUTHOR_RIGHTS_TO_USERIDS_IN_TAGS',
                       CFG_ACC_GRANT_AUTHOR_RIGHTS_TO_EMAILS_IN_TAGS)

    email_tags = cfg.get('CFG_ACC_GRANT_AUTHOR_RIGHTS_TO_USERIDS_IN_TAGS',
                         CFG_ACC_GRANT_AUTHOR_RIGHTS_TO_USERIDS_IN_TAGS)

    return is_user_in_tags(recid, user_info, uid_tags, email_tags)


# FIXME: This method needs to be refactored
def is_user_viewer_of_record(user_info, recid):
    """Check if the user is allow to view the record based in the marc tags.

    Checks inside CFG_ACC_GRANT_VIEWER_RIGHTS_TO_EMAILS_IN_TAGS
    i.e. his email is inside the 506__m tag or he is inside an e-group listed
    in the 506__m tag

    :param user_info: the user_info dictionary that describe the user.
    :type user_info: user_info dictionary
    :param recid: the record identifier.
    :type recid: positive integer
    @return: True if the user is 'allow to view' the record; False otherwise
    @rtype: bool
    """
    from invenio.modules.access.local_config import \
        CFG_ACC_GRANT_VIEWER_RIGHTS_TO_EMAILS_IN_TAGS, \
        CFG_ACC_GRANT_VIEWER_RIGHTS_TO_USERIDS_IN_TAGS

    uid_tags = cfg.get('CFG_ACC_GRANT_VIEWER_RIGHTS_TO_USERIDS_IN_TAGS',
                       CFG_ACC_GRANT_VIEWER_RIGHTS_TO_USERIDS_IN_TAGS)

    email_tags = cfg.get('CFG_ACC_GRANT_VIEWER_RIGHTS_TO_EMAILS_IN_TAGS',
                         CFG_ACC_GRANT_VIEWER_RIGHTS_TO_EMAILS_IN_TAGS)

    return is_user_in_tags(recid, user_info, uid_tags, email_tags)


def get_restricted_collections_for_recid(recid, recreate_cache_if_needed=True):
    """Return the list of restricted collections to which recid belongs."""
    if recreate_cache_if_needed:
        restricted_collection_cache.recreate_cache_if_needed()
        collection_reclist_cache.recreate_cache_if_needed()
    return [collection for collection in restricted_collection_cache.cache
            if recid in get_collection_reclist(
                collection, recreate_cache_if_needed=False)]


def check_user_can_view_record(user_info, recid):
    """Check if the user is authorized to view the given recid.

    The function grants access in two cases: either user has author rights on
    this record, or he has view rights to the primary collection this record
    belongs to.

    :param user_info: the user_info dictionary that describe the user.
    :type user_info: user_info dictionary
    :param recid: the record identifier.
    :type recid: positive integer
    :return: (0, ''), when authorization is granted, (>0, 'message') when
    authorization is not granted
    """
    from invenio.modules.access.engine import acc_authorize_action
    from invenio.modules.access.local_config import VIEWRESTRCOLL
    from invenio.modules.collections.cache import is_record_in_any_collection
    from invenio.legacy.search_engine import record_public_p, record_exists

    policy = cfg['CFG_WEBSEARCH_VIEWRESTRCOLL_POLICY'].strip().upper()

    if isinstance(recid, str):
        recid = int(recid)
    # At this point, either webcoll has not yet run or there are some
    # restricted collections. Let's see first if the user own the record.
    if is_user_owner_of_record(user_info, recid):
        # Perfect! It's authorized then!
        return (0, '')

    if is_user_viewer_of_record(user_info, recid):
        # Perfect! It's authorized then!
        return (0, '')

    restricted_collections = get_restricted_collections_for_recid(
        recid, recreate_cache_if_needed=False
    )
    if not restricted_collections and record_public_p(recid):
        # The record is public and not part of any restricted collection
        return (0, '')
    if restricted_collections:
        # If there are restricted collections the user must be authorized to
        # all/any of them (depending on the policy)
        auth_code, auth_msg = 0, ''
        for collection in restricted_collections:
            (auth_code, auth_msg) = acc_authorize_action(
                user_info, VIEWRESTRCOLL, collection=collection
            )
            if auth_code and policy != 'ANY':
                # Ouch! the user is not authorized to this collection
                return (auth_code, auth_msg)
            elif auth_code == 0 and policy == 'ANY':
                # Good! At least one collection is authorized
                return (0, '')
        # Depending on the policy, the user will be either authorized or not
        return auth_code, auth_msg
    if is_record_in_any_collection(recid, recreate_cache_if_needed=False):
        # the record is not in any restricted collection
        return (0, '')
    elif record_exists(recid) > 0:
        # We are in the case where webcoll has not run.
        # Let's authorize SUPERADMIN
        (auth_code, auth_msg) = acc_authorize_action(
            user_info, VIEWRESTRCOLL, collection=None
        )
        if auth_code == 0:
            return (0, '')
        else:
            # Too bad. Let's print a nice message:
            return (
                1,
                "The record you are trying to access has just been "
                "submitted to the system and needs to be assigned to the "
                "proper collections. It is currently restricted for security "
                "reasons until the assignment will be fully completed. Please "
                "come back later to properly access this record.")
    else:
        # The record either does not exists or has been deleted.
        # Let's handle these situations outside of this code.
        return (0, '')
