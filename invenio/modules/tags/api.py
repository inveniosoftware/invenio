
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

"""API for the tags."""

from flask_login import current_user
from sqlalchemy.exc import DBAPIError
from invenio.ext.sqlalchemy import db
from invenio.modules.accounts.models import Usergroup
import invenio.modules.tags.errors as tags_errors
from .models import WtgTAG, WtgTAGRecord


def create_tag_for_user(uid, tag_name):
    """Create a new tag for a user.

    :param uid: user identifier
    :param tag_name: name of tag to create
    """
    if not uid:
        uid = current_user.get_id()
    # check if tag is already created
    tag = WtgTAG.query.filter(
        WtgTAG.name == tag_name,
        WtgTAG.id_user == uid
    ).first()

    # check if tag is already created
    if tag:
        # raise an error
        raise tags_errors.TagNotCreatedError(
            "User has already created this tag '{0}'".
            format(tag_name))
    else:
        # create the tag
        tag = WtgTAG(name=tag_name, id_user=uid)
        try:
            db.session.add(tag)
            db.session.commit()
        except DBAPIError:
            db.session.rollback()
            raise tags_errors.TagNotCreatedError(
                "Error while saving the new tag '{0}'".
                format(tag_name))
        return tag


def delete_tag_from_user(uid, tag_name):
    """Delete a user's tag.

    :param uid: user identifier
    :param tag_name: name of tag to delete
    """
    if not uid:
        uid = current_user.get_id()
    # find tag
    tag = WtgTAG.query.filter(
        WtgTAG.name == tag_name,
        WtgTAG.id_user == uid
    ).first()
    if not tag:
        raise tags_errors.TagNotFoundError(
            "Tag '{0}' to be deleted could not be found".
            format(tag_name))
    else:
        # check if tag is attached to records
        associations = WtgTAGRecord.query.filter(
            WtgTAGRecord.id_tag == tag.id
        ).all()
        if associations:
            # remove every association that tag is involved in
            for association in associations:
                detach_tag_from_record(uid, tag_name, association.id_bibrec)
        try:
            db.session.delete(tag)
            db.session.commit()
        except DBAPIError:
            db.session.rollback()
            raise tags_errors.TagNotDeletedError(
                "Tag '{0}' could not be deleted".
                format(tag_name))


def get_tag_of_user(uid, tag_name):
    """Retrieve a user's tag.

    :param uid: user identifier
    :param tag_name: name of tag to retrieve
    """
    if uid is None:
        uid = current_user.get_id()
    tag = WtgTAG.query.filter(
        WtgTAG.name == tag_name,
        WtgTAG.id_user == uid
    ).first()
    if not tag:
        raise tags_errors.TagNotFoundError(
            "Tag '{0}' could not be found".
            format(tag_name))
    else:
        return tag


def update_tag_of_user(uid, tag_name, dictionary_to_update):
    """Update a user's tag.

    The dictionary contains the values in order
    to update the tag.

    The attributes that can be updated are:
        -   group name
        -   group access rights
        -   show_in_description

    :param uid: user identifier
    :param tag_name: name of tag to create
    :param dictionary_to_update: dictionary from which tag is updated
    """
    if not uid:
        uid = current_user.get_id()
    tag_retrieved = WtgTAG.query.filter(
        WtgTAG.name == tag_name,
        WtgTAG.id_user == uid
    ).first()
    if not tag_retrieved:
        raise tags_errors.TagNotFoundError(
            "Tag '{0}' could not be found".format(tag_name))
    if uid != tag_retrieved.id_user:
        raise tags_errors.TagOwnerError(
            "The tag's owner id does not match the given id")
    # initialize variables to default values
    usergroup_id = 0
    group_rights = WtgTAG.ACCESS_LEVELS['View']
    show_in_description = True
    # get the values that user uploaded
    if 'groupname' in dictionary_to_update:
        usergroup = Usergroup.query.\
            filter(Usergroup.name == dictionary_to_update['groupname'])
        usergroup_id = usergroup.id
    if 'rights' in dictionary_to_update:
        group_rights = dictionary_to_update['rights']
    if 'show_in_description' in dictionary_to_update:
        show_in_description = dictionary_to_update['show_in_description']
    # perform update of tag
    try:
        tag_retrieved.id_usergroup = usergroup_id
        tag_retrieved.group_access_rights = group_rights
        tag_retrieved.show_in_description = show_in_description
        db.session.merge(tag_retrieved)
        db.session.commit()
    except DBAPIError:
        db.session.rollback()
        raise tags_errors.TagNotUpdatedError(
            "The tag '{0}' could not be updated".
            format(tag_name))
    return tag_retrieved


def get_all_tags_of_user(uid):
    """Get all tags of a user.

    :param uid: user identifier
    """
    if not uid:
        uid = current_user.get_id()
    tags_of_user = WtgTAG.query.filter(WtgTAG.id_user == uid).all()
    if tags_of_user:
        return sorted(tags_of_user, key=lambda t: t.name, reverse=False)
    else:
        raise tags_errors.TagsNotFetchedError(
            "Tags of user could not be fetched")


def delete_all_tags_from_user(uid):
    """Delete a user's tags.

    :param uid: user identifier
    """
    if not uid:
        uid = current_user.get_id()
    tags_of_user = WtgTAG.query.filter(WtgTAG.id_user == uid).all()
    if tags_of_user:
        for tag in tags_of_user:
            delete_tag_from_user(uid, tag.name)
    else:
        raise tags_errors.TagNotDeletedError(
            "Tags could not be deleted because no tags exist")


def attach_tag_to_record(uid, tag_name, record_id):
    """Attach a tag to a record.

    :param uid: user identifier
    :param tag_name: name of tag to be attached to record
    :param record_id: record identifier
    """
    from invenio.legacy.search_engine import record_exists
    if not uid:
        uid = current_user.get_id()
    if record_exists(record_id) != 1:
        raise tags_errors.RecordNotFoundError(
            "Tag error: Record with id={0} does not exist".
            format(record_id))
    tag = WtgTAG.query.filter(
        WtgTAG.name == tag_name,
        WtgTAG.id_user == uid
    ).first()
    # check if tag is not created
    if not tag:
        # create the tag
        tag = WtgTAG(name=tag_name, id_user=uid)
        try:
            db.session.add(tag)
            db.session.commit()
        except DBAPIError:
            db.session.rollback()
            raise tags_errors.TagNotCreatedError(
                "Error while saving the new tag '{0}'".format(tag_name))
        # attach the tag to the record
        association = WtgTAGRecord(id_tag=tag.id, id_bibrec=record_id)
        try:
            db.session.add(association)
            db.session.commit()
        except DBAPIError:
            db.session.rollback()
            raise tags_errors.TagRecordAssociationError(
                "Error when saving association between \
                tag '{0}' and record with id={1}".format(tag_name, record_id))
        return tag
    else:
        # tag already exists
        # check if tag is not attached to the record
        association = WtgTAGRecord.query.filter(
            WtgTAGRecord.id_tag == tag.id,
            WtgTAGRecord.id_bibrec == record_id)
        if not association:
            # create an association between the tag and the record
            association = WtgTAGRecord(id_tag=tag.id, id_bibrec=record_id)
            try:
                db.session.add(association)
                db.session.commit()
            except DBAPIError:
                db.session.rollback()
                raise tags_errors.TagRecordAssociationError(
                    "Error when saving association between \
                    tag '{0}' and record with id={1}".
                    format(tag_name, record_id))
        else:
            # tag exists and is attached to the record
            return None


def attach_tags_to_record(uid, list_of_tags, record_id):
    """Attach a list of tags to a record.

    :param uid: a user id
    :param list_of_tags: a list of tags to be attached to a record
    :param record_id: record identifier
    """
    from invenio.legacy.search_engine import record_exists
    # find record
    if record_exists(record_id) != 1:
        raise tags_errors.RecordNotFoundError(
            "Tag error: Record with id={0} does not exist".
            format(record_id))
    if not uid:
        uid = current_user.get_id()
    # sort the list of tags
    list_of_tags.sort()
    tags_to_return = []
    for tag_name in list_of_tags:
        tag = attach_tag_to_record(uid, tag_name, record_id)
        # if tag is not None
        if tag:
            # append tag to the list that will be returned to user
            tags_to_return.append(tag)
    return tags_to_return


def detach_tag_from_record(uid, tag_name, record_id):
    """Detach a tag from a record.

    :param uid: user identifier
    :param record_id: record identifier
    """
    from invenio.legacy.search_engine import record_exists
    if not uid:
        uid = current_user.get_id()
    # find record
    if record_exists(record_id) != 1:
        raise tags_errors.RecordNotFoundError(
            "Tag error: Record with id={0} does not exist".
            format(record_id))
    # find tag
    retrieved_tag = WtgTAG.query.filter(
        WtgTAG.name == tag_name,
        WtgTAG.id_user == uid
    ).first()
    if not retrieved_tag:
        raise tags_errors.TagNotFoundError(
            "Tag '{0}' cannot be detached because it was not found".
            format(tag_name))
    association = WtgTAGRecord.query.filter(
        WtgTAGRecord.id_bibrec == record_id,
        WtgTAGRecord.id_tag == retrieved_tag.id
    ).first()
    # if there is an association between tag and record
    if association:
        # remove association
        try:
            db.session.delete(association)
            db.session.commit()
        except DBAPIError:
            db.session.rollback()
            raise tags_errors.TagRecordAssociationError(
                "Error while detaching tag '{0}' from record with id={1}".
                format(tag_name, record_id))
    else:
        raise tags_errors.TagRecordAssociationError(
            "Tag '{0} is not attached to record with id={1}".
            format(tag_name, record_id))


def get_attached_tags_on_record(record_id):
    """Get all the user's tags that are attached to the record.

    :param record_id: record identifier
    """
    from invenio.legacy.search_engine import record_exists
    # find record
    if record_exists(record_id) != 1:
        raise tags_errors.RecordNotFoundError(
            "Tag error: Record with id={0} does not exist".
            format(record_id))
    attached_tags = []
    associations = WtgTAGRecord.query.filter(
        WtgTAGRecord.id_bibrec == record_id
    ).all()
    if associations:
        for association in associations:
            tag = WtgTAG.query.filter(WtgTAG.id == association.id_tag).first()
            attached_tags.append(tag)
    return sorted(attached_tags, key=lambda t: t.name, reverse=False)
