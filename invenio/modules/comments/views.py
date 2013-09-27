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

"""WebSearch Flask Blueprint"""

from datetime import datetime
import socket

from flask import g, render_template, request, flash, redirect, url_for, \
    current_app, abort, Blueprint
from invenio.ext.sqlalchemy import db
from invenio.webmessage_mailutils import email_quote_txt
from invenio.modules.comments.models import CmtRECORDCOMMENT, CmtSUBSCRIPTION, \
                                     CmtACTIONHISTORY
from .forms import AddCmtRECORDCOMMENTForm, AddCmtRECORDCOMMENTFormReview
from invenio.base.i18n import _
from invenio.base.decorators import templated
from flask.ext.login import current_user, login_required
from invenio.ext.menu import register_menu
from invenio.ext.breadcrumb import register_breadcrumb
from invenio.ext.principal import permission_required
#from invenio.config import CFG_SITE_RECORD
CFG_SITE_RECORD = 'record'
from invenio.webcomment_config import CFG_WEBCOMMENT_ACTION_CODE

blueprint = Blueprint('comments', __name__, url_prefix="/" + CFG_SITE_RECORD,
                      template_folder='templates')

from invenio.modules.records.views import request_record


def log_comment_action(action_code, id, recid, uid=None):
    action = CmtACTIONHISTORY(
        id_cmtRECORDCOMMENT=id,
        id_bibrec=recid,
        id_user=uid or current_user.get_id(),
        client_host=socket.inet_aton(request.remote_addr),
        action_time=datetime.now(),
        action_code=action_code)
    db.session.add(action)
    db.session.commit()


class CommentRights(object):

    def __init__(self, comment, uid=None):
        self.id = comment
        self.uid = uid or current_user.get_id()
        self.id_collection = 0  # FIXME

    def authorize_action(self, *args, **kwargs):
        from invenio.access_control_engine import acc_authorize_action
        return acc_authorize_action(*args, **kwargs)

    def can_perform_action(self, action=None):
        cond = CmtACTIONHISTORY.id_user == self.uid \
            if self.uid > 0 else \
            CmtACTIONHISTORY.client_host == socket.inet_aton(request.remote_addr)

        if action in CFG_WEBCOMMENT_ACTION_CODE:
            cond = db.and_(cond, CmtACTIONHISTORY.action_code ==
                           CFG_WEBCOMMENT_ACTION_CODE[action])

        return CmtACTIONHISTORY.query.filter(
            CmtACTIONHISTORY.id_cmtRECORDCOMMENT == self.id, cond).\
            count() == 0

    def can_view_restricted_comment(self, restriction):
        #restriction =  self.comment.restriction
        if restriction == "":
            return (0, '')
        return self.authorize_action(
            self.uid,
            'viewrestrcomment',
            status=restriction)

    def can_send_comment(self):
        return self.authorize_action(
            self.uid,
            'sendcomment',
            authorized_if_no_roles=True,
            collection=self.id_collection)

    def can_attach_comment_file(self):
        return self.authorize_action(
            self.uid,
            'attachcommentfile',
            authorized_if_no_roles=False,
            collection=self.id__collection)


@blueprint.route('/<int:recid>/comments/add', methods=['GET', 'POST'])
@request_record
@login_required
@permission_required('sendcomment', authorized_if_no_roles=True,
                     collection=lambda: g.collection.id)
def add_comment(recid):
    uid = current_user.get_id()
    in_reply = request.args.get('in_reply', type=int)
    if in_reply is not None:
        comment = CmtRECORDCOMMENT.query.get(in_reply)

        if comment.id_bibrec != recid or comment.is_deleted:
            abort(401)

        if comment is not None:
            c = CmtRECORDCOMMENT()
            c.title = _('Re: ') + comment.title
            c.body = email_quote_txt(comment.body or '')
            c.in_reply_to_id_cmtRECORDCOMMENT = in_reply
            form = AddCmtRECORDCOMMENTForm(request.form, obj=c)
            return render_template('comments/add.html', form=form)

    form = AddCmtRECORDCOMMENTForm(request.values)
    if form.validate_on_submit():
        c = CmtRECORDCOMMENT()
        form.populate_obj(c)
        c.id_bibrec = recid
        c.id_user = uid
        c.date_creation = datetime.now()
        c.star_score = 0
        try:
            db.session.add(c)
            db.session.commit()
            flash(_('Comment was sent'), "info")
            return redirect(url_for('comments.comments', recid=recid))
        except:
            db.session.rollback()

    return render_template('comments/add.html', form=form)


@blueprint.route('/<int:recid>/reviews/add', methods=['GET', 'POST'])
@request_record
@login_required
@permission_required('sendcomment', authorized_if_no_roles=True,
                     collection=lambda: g.collection.id)
def add_review(recid):
    uid = current_user.get_id()
    form = AddCmtRECORDCOMMENTFormReview(request.values)
    if form.validate_on_submit():
        c = CmtRECORDCOMMENT()
        form.populate_obj(c)
        c.id_bibrec = recid
        c.id_user = uid
        c.date_creation = datetime.now()
        try:
            db.session.add(c)
            db.session.commit()
            flash(_('Review was sent'), "info")
            return redirect(url_for('comments.reviews', recid=recid))
        except:
            db.session.rollback()

    return render_template('comments/add_review.html', form=form)


@blueprint.route('/<int:recid>/comments', methods=['GET', 'POST'])
@request_record
def comments(recid):
    from invenio.access_control_config import VIEWRESTRCOLL
    from invenio.access_control_mailcookie import \
        mail_cookie_create_authorize_action
    from invenio.webcomment import check_user_can_view_comments
    auth_code, auth_msg = check_user_can_view_comments(current_user, recid)
    if auth_code and current_user.is_guest:
        cookie = mail_cookie_create_authorize_action(VIEWRESTRCOLL, {
            'collection': g.collection})
        url_args = {'action': cookie, 'ln': g.ln, 'referer': request.referrer}
        flash(_("Authorization failure"), 'error')
        return redirect(url_for('webaccount.login', **url_args))
    elif auth_code:
        flash(auth_msg, 'error')
        abort(401)

    # FIXME check restricted discussion
    comments = CmtRECORDCOMMENT.query.filter(db.and_(
        CmtRECORDCOMMENT.id_bibrec == recid,
        CmtRECORDCOMMENT.in_reply_to_id_cmtRECORDCOMMENT == 0,
        CmtRECORDCOMMENT.star_score == 0
    )).all()
    return render_template('comments/comments.html', comments=comments)


@blueprint.route('/<int:recid>/reviews', methods=['GET', 'POST'])
@request_record
def reviews(recid):
    from invenio.access_control_config import VIEWRESTRCOLL
    from invenio.access_control_mailcookie import \
        mail_cookie_create_authorize_action
    from invenio.webcomment import check_user_can_view_comments
    auth_code, auth_msg = check_user_can_view_comments(current_user, recid)
    if auth_code and current_user.is_guest:
        cookie = mail_cookie_create_authorize_action(VIEWRESTRCOLL, {
            'collection': g.collection})
        url_args = {'action': cookie, 'ln': g.ln, 'referer': request.referrer}
        flash(_("Authorization failure"), 'error')
        return redirect(url_for('webaccount.login', **url_args))
    elif auth_code:
        flash(auth_msg, 'error')
        abort(401)

    comments = CmtRECORDCOMMENT.query.filter(db.and_(
        CmtRECORDCOMMENT.id_bibrec == recid,
        CmtRECORDCOMMENT.in_reply_to_id_cmtRECORDCOMMENT == 0,
        CmtRECORDCOMMENT.star_score > 0
    )).all()
    return render_template('comments/reviews.html', comments=comments)


@blueprint.route('/<int:recid>/report/<int:id>', methods=['GET', 'POST'])
@request_record
def report(recid, id):
    if CommentRights(id).can_perform_action():
        CmtRECORDCOMMENT.query.filter(CmtRECORDCOMMENT.id == id).update(dict(
            nb_abuse_reports=CmtRECORDCOMMENT.nb_abuse_reports + 1),
            synchronize_session='fetch')

        log_comment_action(CFG_WEBCOMMENT_ACTION_CODE['REPORT_ABUSE'], id, recid)
        flash(_('Comment has been reported.'), 'success')
    else:
        flash(_('Comment has been already reported.'), 'error')

    return redirect(url_for('comments.comments', recid=recid))


@blueprint.route('/<int:recid>/vote/<int:id>/<value>',
                 methods=['GET', 'POST'])
@request_record
def vote(recid, id, value):
    if CommentRights(id).can_perform_action():
        value = 1 if int(value) > 0 else 0
        CmtRECORDCOMMENT.query.filter(
            CmtRECORDCOMMENT.id == id).update(dict(
                nb_votes_total=CmtRECORDCOMMENT.nb_votes_total + 1,
                nb_votes_yes=CmtRECORDCOMMENT.nb_votes_yes + value),
                synchronize_session='fetch')

        log_comment_action(CFG_WEBCOMMENT_ACTION_CODE['VOTE'], id, recid)
        flash(_('Thank you for your vote.'), 'success')
    else:
        flash(_('You can not vote for this comment.'), 'error')

    return redirect(url_for('comments.comments', recid=recid))


@blueprint.route('/<int:recid>/toggle/<int:id>', methods=['GET', 'POST'])
@login_required
@request_record
def toggle(recid, id, show=None):
    uid = current_user.get_id()
    comment = CmtRECORDCOMMENT.query.get_or_404(id)
    assert(comment.id_bibrec == recid)

    if show is None:
        show = 1 if comment.is_collapsed(uid) else 0

    if show:
        comment.expand(uid)
    else:
        comment.collapse(uid)

    if not request.is_xhr:
        return redirect(url_for('comments.comments', recid=recid))
    else:
        return 'OK'


@blueprint.route('/<int:recid>/comments/subscribe', methods=['GET', 'POST'])
@login_required
@request_record
def subscribe(recid):
    uid = current_user.get_id()
    subscription = CmtSUBSCRIPTION(id_bibrec=recid, id_user=uid,
                                   creation_time=datetime.now())
    try:
        db.session.add(subscription)
        db.session.commit()
        flash(_('You have been successfully subscribed'), 'success')
    except:
        flash(_('You are already subscribed'), 'error')
    return redirect(url_for('.comments', recid=recid))


@blueprint.route('/<int:recid>/comments/unsubscribe', methods=['GET', 'POST'])
@blueprint.route('/comments/unsubscribe', methods=['GET', 'POST'])
@login_required
def unsubscribe(recid=None):
    uid = current_user.get_id()
    if recid is None:
        recid = request.values.getlist('recid', type=int)
    else:
        recid = [recid]
    current_app.logger.info(recid)
    try:
        db.session.query(CmtSUBSCRIPTION).filter(db.and_(
            CmtSUBSCRIPTION.id_bibrec.in_(recid),
            CmtSUBSCRIPTION.id_user == uid
        )).delete(synchronize_session=False)
        db.session.commit()
        flash(_('You have been successfully unsubscribed'), 'success')
    except:
        flash(_('You are already unsubscribed'), 'error')
    if len(recid) == 1:
        return redirect(url_for('.comments', recid=recid[0]))
    else:
        return redirect(url_for('.subscriptions'))


@blueprint.route('/comments/subscriptions', methods=['GET', 'POST'])
@login_required
@templated('comments/subscriptions.html')
@register_menu(blueprint, 'personalize.comment_subscriptions',
               _('Your comment subscriptions'), order=20)
@register_breadcrumb(blueprint, '.', _("Your comment subscriptions"))
def subscriptions():
    uid = current_user.get_id()
    subscriptions = CmtSUBSCRIPTION.query.filter(
        CmtSUBSCRIPTION.id_user == uid).all()
    return dict(subscriptions=subscriptions)
