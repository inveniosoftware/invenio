# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013, 2015 CERN.
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

"""WebTag Forms."""

from flask_login import current_user

from invenio.base.globals import cfg
from invenio.base.i18n import _
from invenio.ext.sqlalchemy import db
from invenio.modules.accounts.models import UserUsergroup, Usergroup
from invenio.modules.records.models import Record as Bibrec
from invenio.utils.forms import InvenioBaseForm

from wtforms import BooleanField, HiddenField, IntegerField, SelectField, \
    SelectMultipleField, StringField, validators

# Internal
from .models import WtgTAG, WtgTAGRecord, wash_tag_blocking, wash_tag_silent


def validate_tag_name(dummy_form, field):
    """Check validity of tag name."""
    max_len = cfg['CFG_TAGS_NAME_MAX_LENGTH']
    max_char = cfg['CFG_TAGS_MAX_CHARACTER']

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

        if len(suggested_silent) > max_len:
            raise validators.ValidationError(
                _('The name cannot exeed %(x_max_len)d characters.',
                  x_max_len=max_len))

        if max(ord(letter) for letter in suggested_silent) > max_char:
            raise validators.ValidationError(_('Forbidden character.'))


def validate_name_available(dummy_form, field):
    """Check if the user already has tag named this way."""
    if field.data:
        uid = current_user.get_id()
        copy_count = db.session.query(WtgTAG).\
            filter_by(id_user=uid, name=field.data).count()

        if copy_count > 0:
            raise validators.ValidationError(
                _('Tag with that name already exists.'))


def validate_tag_exists(dummy_form, field):
    """Check if id_tag matches a tag in database."""
    if field.data:
        try:
            field.data = int(field.data)
        except ValueError:
            raise validators.ValidationError(_('Tag ID must be an integer.'))

        if not db.session.query(WtgTAG).get(field.data):
            raise validators.ValidationError(_('Tag does not exist.'))


def validate_user_owns_tag(dummy_form, field):
    """Check if id_tag matches a tag in database."""
    if field.data:
        tag = db.session.query(WtgTAG).get(field.data)

        if tag and tag.id_user != current_user.get_id():
            raise validators.ValidationError(
                _('You are not the owner of this tag.'))


def validate_bibrec_exists(dummy_form, field):
    """Check if id_bibrec matches a bibrec in database."""
    if field.data:
        try:
            field.data = int(field.data)
        except ValueError:
            raise validators.ValidationError(
                _('Bibrec ID must be an integer.'))

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
    """Check if user has rights to view bibrec."""
    if field.data:
        from invenio.legacy.search_engine import check_user_can_view_record

        (auth_code, msg) = check_user_can_view_record(current_user, field.data)

        if auth_code > 0:
            raise validators.ValidationError(
                _('Unauthorized to view record: ') + msg)


def validate_not_already_attached(form, dummy_field):
    """Check if the pair (tag, bibrec) is already connected."""
    if form:
        if ('id_tag' in form.data) and ('id_bibrec' in form.data):
            tag_record = db.session.query(WtgTAGRecord)\
                .get((form.data['id_tag'], form.data['id_bibrec']))

            if tag_record is not None:
                raise validators.ValidationError(_('Tag already attached.'))


def validate_already_attached(form, dummy_field):
    """Check if the pair (tag, bibrec) is already connected."""
    if form:
        if ('id_tag' in form.data) and ('id_bibrec' in form.data):
            tag_record = db.session.query(WtgTAGRecord)\
                .get((form.data['id_tag'], form.data['id_bibrec']))

            if tag_record is None:
                raise validators.ValidationError(_('Tag not attached.'))


class CreateTagForm(InvenioBaseForm):

    """Defines form for creating a new tag."""

    name = StringField(_('Name'), [validators.DataRequired(),
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
                                 [validators.DataRequired(),
                                  validate_tag_exists,
                                  validate_user_owns_tag])


class AttachTagForm(InvenioBaseForm):

    """Defines a form validating attaching a tag to record."""

    # Ajax requests only:
    id_tag = IntegerField('Tag ID',
                          [validators.DataRequired(),
                           validate_tag_exists,
                           validate_not_already_attached,
                           validate_user_owns_tag])

    # validate user rights on tag

    id_bibrec = IntegerField('Record ID',
                             [validate_bibrec_exists,
                              validate_user_can_see_bibrec])


class DetachTagForm(InvenioBaseForm):

    """Defines a form validating detaching a tag from record."""

    # Ajax requests only:
    id_tag = IntegerField('Tag ID',
                          [validators.DataRequired(),
                           validate_tag_exists,
                           validate_already_attached,
                           validate_user_owns_tag])
    # validate user rights on tag

    id_bibrec = IntegerField('Record ID',
                             [validators.DataRequired(),
                              validate_bibrec_exists,
                              validate_user_can_see_bibrec])


class TagAnnotationForm(InvenioBaseForm):

    """Defines a form validating attaching a tag to record."""

    # Ajax requests only:
    id_tag = IntegerField('Tag ID',
                          [validators.DataRequired(),
                           validate_tag_exists,
                           validate_already_attached,
                           validate_user_owns_tag])

    # validate user rights on tag
    id_bibrec = IntegerField('Record ID',
                             [validate_bibrec_exists,
                              validate_user_can_see_bibrec])

    annotation_value = StringField('Annotation')


class GetGroupOptions(object):

    """Get group options."""

    def __iter__(self):
        """Iter function."""
        id_user = current_user.get_id()

        options = [('0', _('Private'))]

        options += db.session.query(Usergroup.id, Usergroup.name)\
            .join(UserUsergroup)\
            .filter(UserUsergroup.id_user == id_user)\
            .all()

        for (gid, name) in options:
            yield (str(gid), name)


class EditTagForm(InvenioBaseForm):

    """Defines form for editing an existing tag."""

    name = StringField(_('Name'), [validators.DataRequired(),
                                   validate_tag_name])

    id_usergroup = SelectField(
        _('Group sharing options'),
        choices=GetGroupOptions())

    group_access_rights = SelectField(
        _('Group access rights'),
        choices=[
            (str(WtgTAG.ACCESS_LEVELS['View']), 'View'),
            (str(WtgTAG.ACCESS_LEVELS['Add and remove']),
             'Attach to documents')
        ])


class WebTagUserSettingsForm(InvenioBaseForm):

    """User's personal settings influencing WebTag module."""

    display_tags = BooleanField(_('Display tags with records'))

    display_tags_group = BooleanField(_('Show group tags'))

    display_tags_public = BooleanField(_('Show public tags'))
