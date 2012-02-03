# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2011 CERN.
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

"""WebMessage Flask Blueprint"""

import pprint

from flask import Blueprint, session, make_response, g, render_template, request, flash, jsonify
from invenio import webmessage_dblayer as db
from invenio.webmessage import is_no_quota_user
from invenio.webmessage_config import CFG_WEBMESSAGE_ROLES_WITHOUT_QUOTA
from invenio.webinterface_handler_flask_utils import _, InvenioBlueprint
from invenio.webinterface_handler import wash_urlargd
from invenio.dbquery import run_sql

blueprint = InvenioBlueprint('yourmessages', __name__, url_prefix="/yourmessages", config='invenio.webmessage_config', breadcrumbs=[(_("Your Account"), 'youraccount.display'), ('Your Messages', 'yourmessages.display')])

@blueprint.route('/')
@blueprint.route('/display')
@blueprint.invenio_authenticated
def display():
    uid = g.user_info['uid']
    messages = db.get_all_messages_for_user(uid)
    nb_messages = db.count_nb_messages(uid)
    no_quota = is_no_quota_user(uid)
    return render_template('webmessage_display.html', messages=messages, nb_messages=nb_messages, no_quota=no_quota)

@blueprint.route("/test")
def test():
    resp = make_response("I am in the blueprint. Session -> %s" % pprint.pformat(dict(session)))
    resp.content_type = 'text/plain'
    return resp

@blueprint.route("/ajax")
@blueprint.invenio_wash_urlargd({"query": (unicode, ""), "term": (unicode, "")})
def ajax(query, term):
    if query == 'users' and len(term) >= 3:
        res = run_sql("SELECT nickname FROM user WHERE nickname LIKE %s ORDER BY nickname LIMIT 10", ("%s%%" % term, ))
        return jsonify(nicknames=[elem[0] for elem in res])
    elif query == 'groups' and len(term) >= 3:
        res = run_sql("SELECT name FROM usergroup WHERE name LIKE %s ORDER BY name LIMIT 10", ("%s%%" %term, ))
        return jsonify(groups=[elem[0] for elem in res])
    return jsonify()

@blueprint.route("/write", methods=['GET', 'POST'])
@blueprint.invenio_set_breadcrumb(_("Write a message"))
@blueprint.invenio_authenticated
@blueprint.invenio_wash_urlargd({'msg_reply_id': (int, 0),
                                   'msg_to': (unicode, u""),
                                   'msg_to_group': (unicode, u""),
                                   'msg_to_user': (unicode, u""),
                                   'msg_subject' : (unicode, u""),
                                   'msg_body' : (unicode, u"")})
def write(msg_reply_id, msg_to, msg_to_user, msg_to_group, msg_body, msg_subject):
    uid = g.user_info['uid']
    msg_id = 0
    if msg_reply_id:
        if (db.check_user_owns_message(uid, msg_reply_id) == 0):
            flash(_('Sorry, this message in not in your mailbox.'), "error")
            msg_reply_id = 0
        else:
            # dummy == variable name to make pylint and pychecker happy!
            (msg_id,
             msg_from_id, msg_from_nickname,
             dummy, dummy,
             msg_subject, msg_body,
             dummy, dummy, dummy) = db.get_message(uid, msg_reply_id)
            if not msg_id:
                # The message exists in table user_msgMESSAGE
                # but not in table msgMESSAGE => table inconsistency
                flash(_('This message does not exist.'), "error")
                msg_reply_id = 0
                msg_subject = ""
                msg_body = ""
            else:
                msg_to = msg_from_nickname or str(msg_from_id)
                msg_subject = _("Re:") + " " + msg_subject
                msg_body = email_quote_txt(msg_body)

    return render_template('webmessage_write.html', msg_to=msg_to,
                                           msg_to_group=msg_to_group,
                                           msg_id=msg_id,
                                           msg_subject=msg_subject,
                                           msg_body=msg_body)
