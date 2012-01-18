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
from string import rfind, strip

from flask import Blueprint, session, make_response, g, render_template, \
                  request, flash, jsonify, redirect, url_for
from invenio import webmessage_dblayer as dbplayer
from invenio.sqlalchemyutils import db
from invenio.webmessage import is_no_quota_user
from invenio.webmessage_config import CFG_WEBMESSAGE_ROLES_WITHOUT_QUOTA, \
    CFG_WEBMESSAGE_STATUS_CODE, CFG_WEBMESSAGE_SEPARATOR
from invenio.webmessage_mailutils import email_quote_txt
from invenio.websession_model import User, Usergroup
from invenio.webmessage_model import MsgMESSAGE, UserMsgMESSAGE
from invenio import webmessage_query as dbquery
from invenio.webinterface_handler_flask_utils import _, InvenioBlueprint
from invenio.webinterface_handler import wash_urlargd
from invenio.dbquery import run_sql

blueprint = InvenioBlueprint('yourmessages', __name__, url_prefix="/yourmessages", config='invenio.webmessage_config', breadcrumbs=[(_("Your Account"), 'youraccount.display'), ('Your Messages', 'yourmessages.display')])

@blueprint.route('/')
@blueprint.route('/display', methods=['GET', 'POST'])
@blueprint.invenio_authenticated
def display():
    uid = g.user_info['uid']
    return render_template('webmessage_display.html',
                messages=dbquery.get_all_messages_for_user(uid),
                nb_messages=dbquery.count_nb_messages(uid),
                no_quota=is_no_quota_user(uid))

@blueprint.route("/test")
def test():
    resp = make_response("I am in the blueprint. Session -> %s" % pprint.pformat(dict(session)))
    resp.content_type = 'text/plain'
    return resp

@blueprint.route("/ajax")
def ajax():
    argd = wash_urlargd(request.values, {"q": (str, ""), "p": (str, "")})
    q = argd['q']
    p = argd['p']
    if q == 'users' and len(p) >= 3:
        res = db.session.query(User.nickname).filter(
            User.nickname.like("%s%%" % p)).limit(10).all()
        return jsonify(nicknames=[elem for elem, in res])
    elif q == 'groups' and len(p) >= 3:
        res = db.session.query(Usergroup.name).filter(
            Usergroup.name.like("%s%%" % p)).limit(10).all()
        return jsonify(groups=[elem for elem, in res])
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
        if (dbplayer.check_user_owns_message(uid, msg_reply_id) == 0):
            flash(_('Sorry, this message in not in your mailbox.'), "error")
            msg_reply_id = 0
        else:
            msg_subject = ""
            msg_body = ""
            try:
                m = dbquery.get_message(uid, msg_reply_id)
                msg_to = m.message.user_from.nickname or str(m.message.id_user_from)
                msg_subject = _("Re:") + " " + m.message.subject
                msg_body = email_quote_txt(m.message.body)
            except db.sqlalchemy.orm.exc.NoResultFound:
                # The message exists in table user_msgMESSAGE
                # but not in table msgMESSAGE => table inconsistency
                flash(_('This message does not exist.'), "error")
                msg_reply_id = 0
            except:
                flash(_('This message does not exist.'), "error")
                msg_reply_id = 0

    return render_template('webmessage_write.html', msg_to=msg_to,
                                           msg_to_group=msg_to_group,
                                           msg_id=msg_id,
                                           msg_subject=msg_subject,
                                           msg_body=msg_body)


@blueprint.route("/display_msg")
@blueprint.invenio_set_breadcrumb(_("Read a message"))
@blueprint.invenio_authenticated
@blueprint.invenio_wash_urlargd({'msgid': (int, 0)})
def display_msg(msgid):
    data = ()
    uid = g.user_info['uid']
    if (dbquery.check_user_owns_message(uid, msgid) == 0):
        flash(_('Sorry, this message (#%d) is not in your mailbox.') % (msgid, ), "error")
    else:
        try:
            m = dbquery.get_message(uid, msgid)
            return render_template('webmessage_display_msg.html', m=m)
        except db.sqlalchemy.orm.exc.NoResultFound:
            flash(_('This message does not exist.'), "error")
        except:
            flash(_('Problem with loading message.'), "error")

    return redirect(url_for('.display'))

@blueprint.route("/delete")
@blueprint.invenio_set_breadcrumb(_("Delete a messages"))
@blueprint.invenio_authenticated
@blueprint.invenio_wash_urlargd({'msgid': (int, 0)})
def delete(msgid):
    """
    Delete every message for a logged user
    @param confirmed: 0 will produce a confirmation message.
    """
    uid = g.user_info['uid']
    if dbquery.check_user_owns_message(uid, msgid) == 0:
        flash(_('Sorry, this message (#%d) is not in your mailbox.') % (msgid, ), "error")
    else:
        if dbquery.delete_message_from_user_inbox(uid, msgid) == 0:
            flash(_("The message could not be deleted."), "error")
        else:
            flash(_("The message was successfully deleted."), "info")

    return redirect(url_for('.display'))

@blueprint.route("/delete_all", methods=['GET', 'POST'])
@blueprint.invenio_set_breadcrumb(_("Delete all messages"))
@blueprint.invenio_authenticated
@blueprint.invenio_wash_urlargd({'confirmed': (int, 0)})
def delete_all(confirmed=0):
    """
    Delete every message for a logged user
    @param confirmed: 0 will produce a confirmation message.
    """
    uid = g.user_info['uid']
    if confirmed != 1:
        return render_template('webmessage_confirm_delete.html')

    if dbquery.delete_all_messages(uid):
        flash(_("Your mailbox has been emptied."), "info")
    else:
        flash(_("Could not empty your mailbox."), "warning")
    return redirect(url_for('.display'))

