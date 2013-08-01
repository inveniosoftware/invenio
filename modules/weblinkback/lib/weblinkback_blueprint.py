# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2012 CERN.
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

"""WebSearch Flask Blueprint"""

import datetime
import pprint
from functools import wraps
from string import rfind, strip
from datetime import datetime

from flask import Blueprint, session, make_response, g, render_template, \
                  request, flash, jsonify, redirect, url_for, current_app
from invenio.cache import cache
from invenio.hashutils import md5
from invenio.intbitset import intbitset as HitSet
from invenio.sqlalchemyutils import db
from invenio.webinterface_handler_flask_utils import _, InvenioBlueprint
from invenio.webuser_flask import current_user
from invenio.weblinkback_model import LnkENTRY
from invenio.access_control_engine import acc_authorize_action
from invenio.config import CFG_SITE_URL, \
                           CFG_SITE_LANG, \
                           CFG_SITE_RECORD

from invenio.weblinkback_config import CFG_WEBLINKBACK_TYPE, \
                                       CFG_WEBLINKBACK_SUBSCRIPTION_DEFAULT_ARGUMENT_NAME, \
                                       CFG_WEBLINKBACK_STATUS, \
                                       CFG_WEBLINKBACK_ORDER_BY_INSERTION_TIME, \
                                       CFG_WEBLINKBACK_LIST_TYPE, \
                                       CFG_WEBLINKBACK_TRACKBACK_SUBSCRIPTION_ERROR_MESSAGE, \
                                       CFG_WEBLINKBACK_PAGE_TITLE_STATUS, \
                                       CFG_WEBLINKBACK_BROKEN_COUNT


blueprint = InvenioBlueprint('weblinkback', __name__,
                            url_prefix="/"+CFG_SITE_RECORD,
                            #breadcrumbs=[(_('Comments'),
                            #              'webcomment.subscribtions')],
                            #menubuilder=[('main.personalize.subscriptions',
                            #              _('Subscriptions'),
                            #              'webcomment.subscriptions', 20)]
                            )

from invenio.record_blueprint import request_record


@blueprint.route('/<int:recid>/linkbacks2', methods=['GET', 'POST'])
@request_record
def index(recid):
    uid = current_user.get_id()
    linkbacks = LnkENTRY.query.filter(db.and_(
        LnkENTRY.id_bibrec == recid,
        LnkENTRY.status == CFG_WEBLINKBACK_STATUS['APPROVED']
        )).all()
    return render_template('weblinkback_index.html',
                linkbacks=linkbacks)


@blueprint.route('/<int:recid>/sendtracebacks', methods=['GET', 'POST'])
@request_record
def sendtraceback(recid):
    pass
