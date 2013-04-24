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

from datetime import datetime
from flask import render_template, request, flash, redirect, url_for
from invenio import webmessage_dblayer as dbplayer
from invenio.config import CFG_WEBMESSAGE_MAX_NB_OF_MESSAGES
from invenio.sqlalchemyutils import db
from invenio.webmessage import is_no_quota_user
from invenio.webmessage_config import CFG_WEBMESSAGE_STATUS_CODE
from invenio.webmessage_mailutils import email_quote_txt
from invenio.webmessage_model import MsgMESSAGE, UserMsgMESSAGE
from invenio.webmessage_forms import AddMsgMESSAGEForm, FilterMsgMESSAGEForm
from invenio import webmessage_query as dbquery
from invenio.webinterface_handler_flask_utils import _, InvenioBlueprint
from invenio.webuser_flask import current_user

from sqlalchemy.sql import operators


class MessagesMenu(object):
    def __str__(self):
        uid = current_user.get_id()
        dbquery.update_user_inbox_for_reminders(uid)
        unread = db.session.query(db.func.count(UserMsgMESSAGE.id_msgMESSAGE)).\
            filter(db.and_(
                UserMsgMESSAGE.id_user_to == uid,
                UserMsgMESSAGE.status == CFG_WEBMESSAGE_STATUS_CODE['NEW']
            )).scalar()

        out = '<div data-menu="click" data-menu-source="' + url_for('webmessage.menu') + '">'
        out += '<i class="icon-envelope icon-white"></i>'
        if unread:
            out += ' <span class="badge badge-important">%d</span>' % unread
        out += "</div>"
        return out

not_guest = lambda: not current_user.is_guest

blueprint = InvenioBlueprint('webmessage', __name__, url_prefix="/yourmessages",
                             config='invenio.webmessage_config',
                             menubuilder=[('personalize.messages',
                                           _('Your messages'),
                                           'webmessage.index', 10),
                                          ('main.messages', MessagesMenu(),
                                           'webmessage.index', -3, [],
                                           not_guest)],
                             breadcrumbs=[(_("Your Account"), 'webaccount.index'),
                                          ('Your Messages', 'webmessage.index')])


@blueprint.route('/menu', methods=['GET'])
#FIXME if request is_xhr then do not return 401
#@blueprint.invenio_authenticated
#@blueprint.invenio_authorized('usemessages')
#@blueprint.invenio_templated('webmessage_menu.html')
def menu():
    uid = current_user.get_id()

    dbquery.update_user_inbox_for_reminders(uid)
    # join: msgMESSAGE -> user_msgMESSAGE, msgMESSAGE -> users
    # filter: all messages from user AND filter form
    # order: sorted by one of the table column
    messages = db.session.query(MsgMESSAGE, UserMsgMESSAGE).\
        join(MsgMESSAGE.user_from, MsgMESSAGE.sent_to_users).\
        filter(db.and_(dbquery.filter_all_messages_from_user(uid))).\
        order_by(db.desc(MsgMESSAGE.received_date)).limit(5)

    #return dict(messages=messages.all())
    return render_template('webmessage_menu.html', messages=messages.all())


@blueprint.route('/', methods=['GET', 'POST'])
@blueprint.route('/index', methods=['GET', 'POST'])
@blueprint.route('/display', methods=['GET', 'POST'])
@blueprint.invenio_authenticated
@blueprint.invenio_authorized('usemessages')
@blueprint.invenio_sorted(MsgMESSAGE)
@blueprint.invenio_filtered(MsgMESSAGE, columns={
    'subject': operators.startswith_op,
    'user_from.nickname': operators.contains_op},
    form=FilterMsgMESSAGEForm)
@blueprint.invenio_templated('webmessage_index.html')
def index(sort=False, filter=None):
    uid = current_user.get_id()

    dbquery.update_user_inbox_for_reminders(uid)
    # join: msgMESSAGE -> user_msgMESSAGE, msgMESSAGE -> users
    # filter: all messages from user AND filter form
    # order: sorted by one of the table column
    messages = db.session.query(MsgMESSAGE, UserMsgMESSAGE).\
        join(MsgMESSAGE.user_from, MsgMESSAGE.sent_to_users).\
        filter(db.and_(dbquery.filter_all_messages_from_user(uid), (filter))).\
        order_by(sort)

    return dict(messages=messages.all(),
                nb_messages=dbquery.count_nb_messages(uid),
                no_quota=is_no_quota_user(uid))


@blueprint.route("/add", methods=['GET', 'POST'])
@blueprint.route("/write", methods=['GET', 'POST'])
@blueprint.invenio_set_breadcrumb(_("Write a message"))
@blueprint.invenio_authenticated
@blueprint.invenio_authorized('usemessages')
@blueprint.invenio_wash_urlargd({'msg_reply_id': (int, 0)})
def add(msg_reply_id):
    uid = current_user.get_id()
    if msg_reply_id:
        if (dbplayer.check_user_owns_message(uid, msg_reply_id) == 0):
            flash(_('Sorry, this message in not in your mailbox.'), "error")
            return redirect(url_for('.index'))
        else:
            try:
                m = dbquery.get_message(uid, msg_reply_id)
                message = MsgMESSAGE()
                message.sent_to_user_nicks = m.message.user_from.nickname \
                    or str(m.message.id_user_from)
                message.subject = _("Re:") + " " + m.message.subject
                message.body = email_quote_txt(m.message.body)
                form = AddMsgMESSAGEForm(request.form, obj=message)
                return dict(form=form)
            except db.sqlalchemy.orm.exc.NoResultFound:
                # The message exists in table user_msgMESSAGE
                # but not in table msgMESSAGE => table inconsistency
                flash(_('This message does not exist.'), "error")
            except:
                flash(_('Problem with loading message.'), "error")

            return redirect(url_for('.index'))

    form = AddMsgMESSAGEForm(request.values)
    if form.validate_on_submit():
        m = MsgMESSAGE()
        form.populate_obj(m)
        m.id_user_from = uid
        m.sent_date = datetime.now()
        quotas = dbplayer.check_quota(CFG_WEBMESSAGE_MAX_NB_OF_MESSAGES - 1)
        users = filter(lambda x: quotas.has_key(x.id), m.recipients)
        #m.recipients = m.recipients.difference(users))
        for u in users:
            m.recipients.remove(u)
        if len(users) > 0:
            flash(_('Following users reached their quota %d messages: %s') % \
                  (CFG_WEBMESSAGE_MAX_NB_OF_MESSAGES, ', '.join(
                  [u.nickname for u in users]),), "error")
        flash(_('Message has %d valid recipients.') %
              (len(m.recipients),), "info")
        if len(m.recipients) == 0:
            flash(_('Message was not sent'), "info")
        else:
            if m.received_date is not None \
                and m.received_date > datetime.now():

                for um in m.sent_to_users:
                    um.status = CFG_WEBMESSAGE_STATUS_CODE['REMINDER']
            else:
                m.received_date = datetime.now()
            try:
                db.session.add(m)
                db.session.commit()
                flash(_('Message was sent'), "info")
                return redirect(url_for('.index'))
            except:
                db.session.rollback()

    return render_template('webmessage_add.html', form=form)


@blueprint.route("/view")
@blueprint.route("/display_msg")
@blueprint.invenio_set_breadcrumb(_("Read a message"))
@blueprint.invenio_authenticated
@blueprint.invenio_authorized('usemessages')
@blueprint.invenio_wash_urlargd({'msgid': (int, 0)})
@blueprint.invenio_templated('webmessage_view.html')
def view(msgid):
    uid = current_user.get_id()
    if (dbquery.check_user_owns_message(uid, msgid) == 0):
        flash(_('Sorry, this message (#%d) is not in your mailbox.') % (msgid, ), "error")
    else:
        try:
            m = dbquery.get_message(uid, msgid)
            m.status = CFG_WEBMESSAGE_STATUS_CODE['READ']
            ## It's not necessary since "m" is SQLAlchemy object bind with same
            ## session.
            ##db.session.add(m)
            ## I wonder if the autocommit works ...
            # Commit changes before rendering for correct menu update.
            db.session.commit()
            return dict(m=m)
        except db.sqlalchemy.orm.exc.NoResultFound:
            flash(_('This message does not exist.'), "error")
        except:
            flash(_('Problem with loading message.'), "error")

    return redirect(url_for('.index'))


@blueprint.route("/delete", methods=['GET', 'POST'])
@blueprint.invenio_authenticated
@blueprint.invenio_authorized('usemessages')
def delete():
    """
    Delete message specified by 'msgid' that belongs to logged user.
    """
    uid = current_user.get_id()
    msgids = request.values.getlist('msgid', type=int)
    if len(msgids) <= 0:
        flash(_('Sorry, no valid message specified.'), "error")
    elif dbquery.check_user_owns_message(uid, msgids) < len(msgids):
        flash(_('Sorry, this message (#%s) is not in your mailbox.') % (str(msgids), ), "error")
    else:
        if dbquery.delete_message_from_user_inbox(uid, msgids) == 0:
            flash(_("The message could not be deleted."), "error")
        else:
            flash(_("The message was successfully deleted."), "info")

    return redirect(url_for('.index'))


@blueprint.route("/delete_all", methods=['GET', 'POST'])
@blueprint.invenio_set_breadcrumb(_("Delete all messages"))
@blueprint.invenio_authenticated
@blueprint.invenio_authorized('usemessages')
@blueprint.invenio_wash_urlargd({'confirmed': (int, 0)})
def delete_all(confirmed=0):
    """
    Delete every message belonging a logged user.
    @param confirmed: 0 will produce a confirmation message.
    """
    uid = current_user.get_id()
    if confirmed != 1:
        return render_template('webmessage_confirm_delete.html')

    if dbquery.delete_all_messages(uid):
        flash(_("Your mailbox has been emptied."), "info")
    else:
        flash(_("Could not empty your mailbox."), "warning")
    return redirect(url_for('.index'))
