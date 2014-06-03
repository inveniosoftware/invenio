# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2013 CERN.
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

"""WebTag Forms"""

from invenio.webtag_config import \
    CFG_WEBTAG_LAST_MYSQL_CHARACTER

from invenio.webtag_config import \
    CFG_WEBTAG_NAME_MAX_LENGTH

from invenio.webinterface_handler_flask_utils import _

from invenio.wtforms_utils import InvenioBaseForm
from invenio.webuser_flask import current_user

from wtforms import \
    IntegerField, \
    HiddenField, \
    TextField, \
    SelectMultipleField, \
    validators

# Models
from invenio.sqlalchemyutils import db
from invenio.webtag_model import \
    WtgTAG, \
    WtgTAGRecord, \
    wash_tag_silent, \
    wash_tag_blocking
from invenio.bibedit_model import Bibrec

from invenio.search_engine import check_user_can_view_record


def validate_tag_name(dummy_form, field):
    """ Check validity of tag name """
    if field.data:
        suggested_silent = wash_tag_silent(field.data)
        suggested = wash_tag_blocking(suggested_silent)

        field.data = suggested_silent

        if suggested != suggested_silent:
            raise validators.ValidationError(
                _('Forbidden characters. Try ') + suggested + '.')

        if len(suggested) <= 0:
            raise validators.ValidationError(
                _('The name must contain valid characters.'))

        if len(suggested_silent) > CFG_WEBTAG_NAME_MAX_LENGTH:
            raise validators.ValidationError( _('The name cannot exeed ') \
                  + str(CFG_WEBTAG_NAME_MAX_LENGTH) + _(' characters.'))

        if max(ord(letter) for letter in suggested_silent) \
           > CFG_WEBTAG_LAST_MYSQL_CHARACTER:
            raise validators.ValidationError( _('Forbidden character.'))

def validate_name_available(dummy_form, field):
    """ Check if the user already has tag named this way """
    if field.data:
        uid = current_user.get_id()
        copy_count = db.session.query(WtgTAG).\
            filter_by(id_user=uid, name=field.data).count()

        if copy_count > 0:
            raise validators.ValidationError(
                _('Tag with that name already exists.'))

def validate_tag_exists(dummy_form, field):
    """ Check if id_tag matches a tag in database """
    if field.data:
        try:
            field.data = int(field.data)
        except ValueError:
            raise validators.ValidationError(_('Tag ID must be an integer.'))

        if not db.session.query(WtgTAG).get(field.data):
            raise validators.ValidationError(_('Tag does not exist.'))

def validate_user_owns_tag(dummy_form, field):
    """ Check if id_tag matches a tag in database """
    if field.data:
        tag = db.session.query(WtgTAG).get(field.data)

        if tag and tag.id_user != current_user.get_id():
            raise validators.ValidationError(
                  _('You are not the owner of this tag.'))

def validate_bibrec_exists(dummy_form, field):
    """ Check if id_bibrec matches a bibrec in database """
    if field.data:
        try:
            field.data = int(field.data)
        except ValueError:
            raise validators.ValidationError(_('Bibrec ID must be an integer.'))

        record = db.session.query(Bibrec).get(field.data)

        if (not record):
            raise validators.ValidationError(_('Bibrec does not exist.'))

        # Switch to merged record if present
        merged_id = record.merged_recid_final
        if merged_id != record.id:
            record = db.session.query(Bibrec).get(merged_id)
            field.data = merged_id

        if record.deleted:
            raise validators.ValidationError(_('Bibrec has been deleted.'))

def validate_user_can_see_bibrec(dummy_form, field):
    """ Check if user has rights to view bibrec """
    if field.data:
        (auth_code, msg) = check_user_can_view_record(current_user, field.data)

        if auth_code > 0:
            raise validators.ValidationError(
                  _('Unauthorized to view record: ')+msg)

def validate_not_already_attached(form, dummy_field):
    """ Check if the pair (tag, bibrec) is already connected """
    if form:
        if ('id_tag' in form.data) and ('id_bibrec' in form.data):
            tag_record = db.session.query(WtgTAGRecord)\
                .get((form.data['id_tag'], form.data['id_bibrec']))

            if tag_record is not None:
                raise validators.ValidationError(_('Tag already attached.'))

def validate_already_attached(form, dummy_field):
    """ Check if the pair (tag, bibrec) is already connected """
    if form:
        if ('id_tag' in form.data) and ('id_bibrec' in form.data):
            tag_record = db.session.query(WtgTAGRecord)\
                .get((form.data['id_tag'], form.data['id_bibrec']))

            if tag_record is None:
                raise validators.ValidationError(_('Tag not attached.'))

class CreateTagForm(InvenioBaseForm):
    """Defines form for creating a new tag."""
    name = TextField(_('Name'), [validators.Required(),
                                 validate_tag_name,
                                 validate_name_available])

    # Ajax requests only:
    # Send a record ID if the tag should be attached to the record
    # right after creation
    id_bibrec = HiddenField('Tagged record',
                            [validate_bibrec_exists,
                             validate_user_can_see_bibrec])

class DeleteTagForm(InvenioBaseForm):
    """Defines form for deleting a tag."""
    id_tag = SelectMultipleField('Tag ID',
                              [validators.Required(),
                               validate_tag_exists,
                               validate_user_owns_tag])

class AttachTagForm(InvenioBaseForm):
    """Defines a form validating attaching a tag to record"""
    # Ajax requests only:
    id_tag = IntegerField('Tag ID',
             [validators.Required(),
              validate_tag_exists,
              validate_not_already_attached,
              validate_user_owns_tag])

    # validate user rights on tag

    id_bibrec = IntegerField('Record ID',
                [validate_bibrec_exists,
                 validate_user_can_see_bibrec])

class DetachTagForm(InvenioBaseForm):
    """Defines a form validating detaching a tag from record"""
    # Ajax requests only:
    id_tag = IntegerField('Tag ID',
             [validators.Required(),
              validate_tag_exists,
              validate_already_attached,
              validate_user_owns_tag])
    # validate user rights on tag

    id_bibrec = IntegerField('Record ID',
                [validators.Required(),
                 validate_bibrec_exists,
                 validate_user_can_see_bibrec])
