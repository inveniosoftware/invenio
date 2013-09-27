# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2012, 2013 CERN.
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

from flask import Blueprint, render_template, request, jsonify
from flask.ext.login import current_user, login_required
from invenio.base.decorators import wash_arguments
from invenio.base.i18n import _
from invenio.ext.breadcrumb import default_breadcrumb_root, register_breadcrumb
from invenio.ext.sqlalchemy import db
from invenio.modules.accounts.models import User, Usergroup, UserUsergroup

blueprint = Blueprint('webgroup', __name__, url_prefix="/yourgroups",
                      template_folder='templates', static_folder='static')

default_breadcrumb_root(blueprint, '.webaccount.webgroup')

def filter_by_user_status(uid, user_status, login_method='INTERNAL'):
    return db.and_(UserUsergroup.id_user == uid,
                   UserUsergroup.user_status == user_status,
                   Usergroup.login_method == login_method)


@blueprint.route('/')
@blueprint.route('/index', methods=['GET', 'POST'])
@register_breadcrumb(blueprint, '.', _('Your Groups'))
@login_required
def index():
    uid = current_user.get_id()
    mg = Usergroup.query.join(Usergroup.users).\
        filter(UserUsergroup.id_user==uid).all()
        #filter_by_user_status(uid,
        #CFG_WEBSESSION_USERGROUP_STATUS["MEMBER"])).\
        #all()

    return render_template('groups/index.html', member_groups=map(dict, mg))


@blueprint.route("/search", methods=['GET', 'POST'])
@wash_arguments({"query": (unicode, ""), "term": (unicode, "")})
def search(query, term):
    if query == 'users' and len(term) >= 3:
        res = db.session.query(User.nickname).filter(
            User.nickname.like("%s%%" % term)).limit(10).all()
        return jsonify(nicknames=[elem for elem, in res])
    elif query == 'groups' and len(term) >= 3:
        res = db.session.query(db.func.distinct(Usergroup.name)).\
            join(UserUsergroup).filter(
                Usergroup.name.like("%s%%" % term)).limit(10).all()
        return jsonify(groups=[elem for elem, in res])
    return jsonify()


@blueprint.route("/tokenize", methods=['GET', 'POST'])
@wash_arguments({"q": (unicode, "")})
def tokenize(q):
    res = Usergroup.query.filter(
        Usergroup.name.like("%s%%" % q)).limit(10).all()
    return jsonify(data=map(dict, res))


@blueprint.route("/join", methods=['GET', 'POST'])
@blueprint.route("/leave", methods=['GET', 'POST'])
@wash_arguments({"id": (int, 0)})
def _manipulate_group(id):
    uid = current_user.get_id()
    try:
        user = User.query.filter(User.id == uid).one()
        group = Usergroup.query.filter(Usergroup.id == id).one()
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
#@login_required
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
