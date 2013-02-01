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

"""WebGroup Flask Blueprint"""

from flask import Blueprint, session, make_response, g, render_template, \
                  request, flash, jsonify, redirect, url_for
from invenio import webgroup_dblayer as dbplayer
from invenio.sqlalchemyutils import db
from invenio.webuser_flask import current_user
from invenio.config import CFG_SITE_LANG
from invenio.websession_model import User, Usergroup, UserUsergroup
from invenio.webinterface_handler_flask_utils import _, InvenioBlueprint
from invenio.webinterface_handler import wash_urlargd
from invenio.dbquery import run_sql

from invenio.websession_config import CFG_WEBSESSION_INFO_MESSAGES, \
      CFG_WEBSESSION_USERGROUP_STATUS, \
      CFG_WEBSESSION_GROUP_JOIN_POLICY, \
      InvenioWebSessionError, \
      InvenioWebSessionWarning

blueprint = InvenioBlueprint('webgroup', __name__, url_prefix="/yourgroups",
                             breadcrumbs=[(_("Your Groups"),
                                           'webgroup.index')])


def filter_by_user_status(uid, user_status, login_method='INTERNAL'):
    return db.and_(UserUsergroup.id_user==uid,
                   UserUsergroup.user_status==user_status,
                   Usergroup.login_method==login_method)


@blueprint.route('/')
@blueprint.route('/index', methods=['GET', 'POST'])
@blueprint.invenio_authenticated
def index():
    uid = current_user.get_id()
    mg = Usergroup.query.join(Usergroup.users).\
            filter(UserUsergroup.id_user==uid).all()
            #filter_by_user_status(uid,
            #CFG_WEBSESSION_USERGROUP_STATUS["MEMBER"])).\
            #all()

    return render_template('webgroup_index.html', member_groups=map(dict, mg))


@blueprint.route("/search", methods=['GET', 'POST'])
@blueprint.invenio_wash_urlargd({"query": (unicode, ""), "term": (unicode, "")})
def search(query, term):
    if query == 'users' and len(term) >= 3:
        res = db.session.query(User.nickname).filter(
            User.nickname.like("%s%%" % term)).limit(10).all()
        return jsonify(nicknames=[elem for elem, in res])
    elif query == 'groups' and len(term) >= 3:
        res = db.session.query(Usergroup.name).filter(
            Usergroup.name.like("%s%%" % term)).limit(10).all()
        return jsonify(groups=[elem for elem, in res])
    return jsonify()

@blueprint.route("/tokenize", methods=['GET', 'POST'])
@blueprint.invenio_wash_urlargd({"q": (unicode, "")})
def tokenize(q):
    res = Usergroup.query.filter(
        Usergroup.name.like("%s%%" % q)).limit(10).all()
    return jsonify(data=map(dict, res))

@blueprint.route("/join", methods=['GET', 'POST'])
@blueprint.route("/leave", methods=['GET', 'POST'])
@blueprint.invenio_wash_urlargd({"id": (int, 0)})
def _manipulate_group(id):
    uid = current_user.get_id()
    try:
        user = User.query.filter(User.id==uid).one()
        group = Usergroup.query.filter(Usergroup.id==id).one()
        if request.path.find("/join") > 0:
            user.usergroups.append(UserUsergroup(usergroup=group))
            db.session.add(user)
        else:
            [db.session.delete(ug) for ug in user.usergroups
                            if ug.id_usergroup == id]
            #UserUsergroup.query.filter(and_(
            #    UserUsergroup.id_user==uid,
            #    UserUsergroup.id_userusergroup==id_usergroup)).delete()
        db.session.commit()
        return jsonify(result=dict({'status':True}))
    except:
        db.session.rollback()
        return jsonify(result=dict({'status':False}))



#@blueprint.route("/add", methods=['GET', 'POST'])
#@blueprint.invenio_authenticated
#def add():
#    uid = current_user.get_id()
#    form = AddMsgMESSAGEForm(request.form)
#    if form.validate_on_submit():
#        m = MsgMESSAGE()
#        form.populate_obj(m)
#        try:
#            db.session.add(m)
#            db.session.commit()
#            flash(_('Message was sent'), "info")
#            return redirect(url_for('.display'))
#        except:
#            db.session.rollback()
#
#    return render_template('webgroup_add.html', form=form)
#
