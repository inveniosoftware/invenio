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

"""WebAccess Admin Flask Blueprint"""

from flask import redirect, url_for
from invenio.webaccess_model import AccACTION, AccROLE
from invenio.websession_model import User
from invenio.webinterface_handler_flask_utils import _, InvenioBlueprint

from invenio.access_control_config import \
    WEBACCESSACTION

blueprint = InvenioBlueprint('webaccess_admin', __name__,
                             url_prefix="/admin/webaccess",
                             config='invenio.access_control_config',
                             breadcrumbs=[(_('Administration'), 'help.admin'),
                                          (_('WebAccess'), 'webaccesss_admin.index')],
                             menubuilder=[('main.admin.webaccess',
                                          _('Configure WebAccess'),
                                          'webaccess_admin.index', 90)])


@blueprint.route('/', methods=['GET', 'POST'])
@blueprint.invenio_authenticated
@blueprint.invenio_authorized(WEBACCESSACTION)
@blueprint.invenio_templated('webaccess_admin_index.html')
def index():
    actions = [
        dict(url=url_for('.rolearea'),
             title=_('Role Area'),
             description=_('Main area to configure administration rights and authorization rules.')),
        dict(url=url_for('.actionarea'),
             title=_('Action Area'),
             description=_('Configure administration rights with the actions as starting point.')),
        dict(url=url_for('.userarea'),
             title=_('User Area'),
             description=_('Configure administration rights with the users as starting point.')),
        dict(url=url_for('.resetarea'),
             title=_('Reset Area'),
             description=_('Reset roles, actions and authorizations.')),
        dict(url=url_for('.manageaccounts'),
             title=_('Manage Accounts Area'),
             description=_('Manage user accounts.')),
        dict(url=url_for('.delegate_startarea'),
             title=_('Delegate Rights - With Restrictions'),
             description=_('Delegate your rights for some roles.')),
        dict(url=url_for('.managerobotlogin'),
             title=_('Manage Robot Login'),
             description=_('Manage robot login keys and test URLs.')),
    ]
    return dict(actions=actions)


@blueprint.route('/actionarea', methods=['GET', 'POST'])
@blueprint.invenio_authenticated
@blueprint.invenio_authorized(WEBACCESSACTION)
@blueprint.invenio_sorted(AccACTION)
@blueprint.invenio_templated('webaccess_admin_actionarea.html')
def actionarea(sort=False, filter=None):
    if sort is False:
        sort = AccACTION.name
    actions = AccACTION.query.order_by(sort).filter(filter).all()
    return dict(actions=actions)


@blueprint.route('/rolearea', methods=['GET', 'POST'])
@blueprint.invenio_authenticated
@blueprint.invenio_authorized(WEBACCESSACTION)
@blueprint.invenio_sorted(AccROLE)
@blueprint.invenio_templated('webaccess_admin_rolearea.html')
def rolearea(sort=False, filter=None):
    if sort is False:
        sort = AccROLE.name
    roles = AccROLE.query.order_by(sort).filter(filter).all()
    return dict(roles=roles)


@blueprint.route('/showroledetails/<int:id_role>', methods=['GET', 'POST'])
@blueprint.invenio_authenticated
@blueprint.invenio_authorized(WEBACCESSACTION)
@blueprint.invenio_templated('webaccess_admin_showroledetails.html')
def showroledetails(id_role):
    return dict(role=AccROLE.query.get_or_404(id_role))


@blueprint.route('/userarea', methods=['GET', 'POST'])
@blueprint.invenio_authenticated
@blueprint.invenio_authorized(WEBACCESSACTION)
@blueprint.invenio_sorted(User)
@blueprint.invenio_templated('webaccess_admin_userarea.html')
def userarea(sort=False, filter=None):
    if sort is False:
        sort = User.nickname
    users = User.query.order_by(sort).filter(filter).all()
    return dict(users=users)


@blueprint.route('/resetarea', methods=['GET', 'POST'])
def resetarea():
    #FIXME reimplement this function
    return redirect('/admin/webaccess/webaccessadmin.py/resetarea')


@blueprint.route('/manageaccounts', methods=['GET', 'POST'])
def manageaccounts():
    #FIXME reimplement this function
    return redirect('/admin/webaccess/webaccessadmin.py/manageaccounts')


@blueprint.route('/delegate_startarea', methods=['GET', 'POST'])
def delegate_startarea():
    #FIXME reimplement this function
    return redirect('/admin/webaccess/webaccessadmin.py/delegate_startarea')


@blueprint.route('/managerobotlogin', methods=['GET', 'POST'])
def managerobotlogin():
    #FIXME reimplement this function
    return redirect('/admin/webaccess/webaccessadmin.py/managerobotlogin')
