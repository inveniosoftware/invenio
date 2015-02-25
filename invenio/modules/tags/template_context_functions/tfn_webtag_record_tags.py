# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013, 2014 CERN.
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

"""WebTag List of tags in document view."""

# Flask
from invenio.ext.template import render_template_to_string
from invenio.base.globals import cfg
from invenio.ext.sqlalchemy import db

# Models
from invenio.modules.tags.models import \
    WtgTAG, \
    WtgTAGRecord

# Related models
from invenio.modules.accounts.models import User, Usergroup, UserUsergroup


def template_context_function(id_bibrec, id_user):
    """Add tag editor.

    :param id_bibrec: ID of record
    :param id_user: user viewing the record (and owning the displayed tags)
    :return: HTML containing tag list
    """
    if id_user and id_bibrec:
        # Get user settings:
        user = User.query.get(id_user)
        user_settings = user.settings.get(
            'webtag', cfg['CFG_WEBTAG_DEFAULT_USER_SETTINGS'])

        if not user_settings['display_tags']:
            # Do not display if user turned off tags in settings
            return ''

        # Private
        query_results = db.session.query(WtgTAG, WtgTAGRecord.annotation)\
            .filter(WtgTAG.id == WtgTAGRecord.id_tag)\
            .filter(WtgTAGRecord.id_bibrec == id_bibrec)\
            .filter(WtgTAG.id_user == id_user)\
            .all()

        # Group tags
        if user_settings.get('display_tags_group', True):
            group_results = db.session.query(WtgTAG, WtgTAGRecord.annotation, Usergroup.name)\
                .join(UserUsergroup, UserUsergroup.id_user == id_user)\
                .filter(WtgTAG.id == WtgTAGRecord.id_tag)\
                .filter(WtgTAGRecord.id_bibrec == id_bibrec)\
                .filter(WtgTAG.group_access_rights >= WtgTAG.ACCESS_LEVELS['View'])\
                .filter(WtgTAG.id_usergroup == Usergroup.id)\
                .filter(WtgTAG.id_user != id_user)\
                .filter(Usergroup.id == UserUsergroup.id_usergroup)\
                .all()

            for (tag, annotation, group_name) in group_results:
                tag.group_name = group_name
                query_results.append((tag, annotation))

        # Public tags
        #if user_settings.get('display_tags_public', True):

        tag_infos = []

        for (tag, annotation_text) in query_results:
            tag_info = dict(
                id=tag.id,
                name=tag.name,
                record_count=tag.record_count,
                annotation=annotation_text,
                label_classes='')

            tag_info['owned'] = (tag.id_user == id_user)
            tag_info['is_group'] = (tag.id_usergroup != 0)
            tag_info['is_private'] = not tag_info['is_group']

            if tag_info['is_private']:
                tag_info['label_classes'] += ' label-info'

            if tag_info['is_group']:
                tag_info['group_name'] = getattr(tag, 'group_name', '')

                tag_info['label_classes'] += ' label-success'
                if tag_info['owned']:
                    tag_info['label_classes'] += ' label-tag-owned'

            tag_info['popover_title'] = render_template_to_string(
                'tags/tag_popover_title.html',
                tag=tag_info,
                id_bibrec=id_bibrec)

            tag_info['popover_content'] = render_template_to_string(
                'tags/tag_popover_content.html',
                tag=tag_info,
                id_bibrec=id_bibrec)

            tag_infos.append(tag_info)
        return render_template_to_string(
            'tags/record_tags.html',
            tag_infos=tag_infos,
            id_bibrec=id_bibrec)
    else:
        return ''
