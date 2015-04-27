# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2012, 2014, 2015 CERN.
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

"""WebSearch Flask Blueprint."""

from __future__ import unicode_literals

from flask import Blueprint, Response, render_template, request

from flask_login import current_user

from flask_menu import register_menu

from invenio.base.decorators import wash_arguments
from invenio.base.i18n import _
from invenio.config import (CFG_SITE_RECORD,
                            CFG_WEBLINKBACK_TRACKBACK_ENABLED)
from invenio.ext.sqlalchemy import db
from invenio.legacy.weblinkback.config import CFG_WEBLINKBACK_STATUS, \
    CFG_WEBLINKBACK_SUBSCRIPTION_DEFAULT_ARGUMENT_NAME
from invenio.modules.records.utils import visible_collection_tabs
from invenio.modules.records.views import request_record

from .models import LnkENTRY

blueprint = Blueprint('weblinkback', __name__, url_prefix="/"+CFG_SITE_RECORD,
                      template_folder='templates', static_folder='static')


@blueprint.route('/<int:recid>/linkbacks2', methods=['GET', 'POST'])
@request_record
@register_menu(blueprint, 'record.linkbacks', _('Linkbacks'), order=11,
               endpoint_arguments_constructor=lambda:
               dict(recid=request.view_args.get('recid')),
               visible_when=visible_collection_tabs('linkbacks'))
def index(recid):
    """Index."""
    linkbacks = LnkENTRY.query.filter(db.and_(
        LnkENTRY.id_bibrec == recid,
        LnkENTRY.status == CFG_WEBLINKBACK_STATUS['APPROVED']
        )).all()
    return render_template('linkbacks/index.html', linkbacks=linkbacks)


@blueprint.route('/<int:recid>/sendtrackback', methods=['GET', 'POST'])
@request_record
@wash_arguments({
                'url': (unicode,
                        CFG_WEBLINKBACK_SUBSCRIPTION_DEFAULT_ARGUMENT_NAME),
                'title': (unicode,
                          CFG_WEBLINKBACK_SUBSCRIPTION_DEFAULT_ARGUMENT_NAME),
                'excerpt': (unicode,
                            CFG_WEBLINKBACK_SUBSCRIPTION_DEFAULT_ARGUMENT_NAME
                            ),
                'blog_name':
                (unicode, CFG_WEBLINKBACK_SUBSCRIPTION_DEFAULT_ARGUMENT_NAME),
                'id':
                (unicode, CFG_WEBLINKBACK_SUBSCRIPTION_DEFAULT_ARGUMENT_NAME),
                'source': (unicode,
                           CFG_WEBLINKBACK_SUBSCRIPTION_DEFAULT_ARGUMENT_NAME)}
                )
def sendtrackback(recid, url, title, excerpt, blog_name, id, source):
    """Send trackback."""
    from invenio.legacy.weblinkback.api import (perform_sendtrackback,
                                                perform_sendtrackback_disabled)
    mime_type = 'text/xml; charset=utf-8'
    if CFG_WEBLINKBACK_TRACKBACK_ENABLED:
        xml_response, status = perform_sendtrackback(recid, url, title,
                                                     excerpt, blog_name, id,
                                                     source, current_user)
    else:
        xml_response, status = perform_sendtrackback_disabled()
    return Response(response=xml_response, status=status, mimetype=mime_type)
