# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014, 2015 CERN.
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

"""Annotations module."""

from __future__ import unicode_literals

from flask import Blueprint, abort, current_app, flash, g, jsonify, redirect, \
    render_template, request, url_for

from flask_login import current_user, login_required

from invenio.base.globals import cfg
from invenio.base.i18n import _
from invenio.modules.comments.models import CmtRECORDCOMMENT
from invenio.modules.comments.views import blueprint as comments_blueprint
from invenio.modules.records.views import request_record

from sqlalchemy.event import listen

from urlparse import urlsplit

from .api import add_annotation, get_annotations, get_count
from .forms import WebPageAnnotationForm, WebPageAnnotationFormAttachments
from .noteutils import get_note_title, get_original_comment, \
    note_is_collapsed, prepare_notes
from .receivers import extract_notes

blueprint = Blueprint('annotations',
                      __name__,
                      url_prefix="/annotations",
                      template_folder='templates',
                      static_folder='static')

listen(CmtRECORDCOMMENT, 'after_insert', extract_notes)


def permission_builder(public, groups=None):
    """Permission builder."""
    d = {}
    if groups is None:
        groups = []
    d['public'] = public
    d['groups'] = groups
    return d


@blueprint.route('/ping/<string:message>', methods=['GET'])
@blueprint.route('/ping/', methods=['GET'])
def ping(message=""):
    """Pong message."""
    return "PONG: " + message


@blueprint.route('/menu', methods=['GET'])
def menu():
    """Menu page."""
    # we need the after-login referrer to be the main page, not the modal dialog
    original_referrer = request.referrer
    annos = get_count(current_user.get_id(), urlsplit(original_referrer)[2])
    if not annos["total"]:
        view = "add"
    elif not annos["public"] and annos["private"]:
        view = "private"
    else:
        view = "public"
    return render_template("annotations/menu.html",
                           view=view,
                           original_referrer=original_referrer)


@blueprint.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    """Add page."""
    if cfg["ANNOTATIONS_ATTACHMENTS"]:
        form = WebPageAnnotationFormAttachments(request.form)
    else:
        form = WebPageAnnotationForm(request.form)
    if form.validate_on_submit():
        # FIXME: use form.data instead of manual fields
        add_annotation(model='annotation',
                       who=current_user,
                       where=form.url.data,
                       what=form.body.data,
                       perm=permission_builder(form.public.data))
        from flask_babel import gettext  # "unlazy" translation hack
        flash(gettext("Annotation saved."), "info")
        if not request.is_xhr:
            return redirect(request.referrer)
    else:
        form.url.data = request.args.get("target")
    return render_template('annotations/add.html', form=form)


@blueprint.route('/get_count', methods=['GET'])
def get__anno_count():
    """Get count page."""
    return jsonify(get_count(current_user.get_id(),
                             urlsplit(request.referrer)[2]))


@blueprint.route('/view', methods=['GET', 'POST'])
def view():
    """View page."""
    return render_template('annotations/view.html',
                           public_annotations=get_annotations(
                               {"where": request.args.get("target"),
                                "perm": {"public": True, "groups": []}}),
                           private_annotations=get_annotations(
                               {"where": request.args.get("target"),
                                "who": current_user.get_id(),
                                "perm": {"public": False, "groups": []}}))


@blueprint.route('/attach', methods=['POST'])
@login_required
def attach():
    """Attach page."""
    # if not _id, create empty annotation, get id
    # send id back and autofill form
    # save Document
    # link Annotation and Document
    current_app.logger.info('Uploaded file: ' +
                            request.files.get('file').filename)
    return jsonify(_id=0)


@blueprint.route('/detach', methods=['POST'])
@login_required
def detach():
    """Detach page."""
    current_app.logger.info('Removal request: ' + request.values.get('file_id'))
    return jsonify()


@comments_blueprint.route('/<int:recid>/notes', methods=['GET'])
@request_record
def notes(recid):
    """Note page."""
    """View for the record notes extracted from comments"""

    if not cfg['ANNOTATIONS_NOTES_ENABLED']:
        return redirect(url_for('comments.comments', recid=recid))

    from invenio.modules.access.local_config import VIEWRESTRCOLL
    from invenio.modules.access.mailcookie import \
        mail_cookie_create_authorize_action
    from invenio.modules.comments.api import check_user_can_view_comments
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

    from invenio.modules.annotations.api import get_annotations

    page = request.args.get('page', type=int)
    if cfg["ANNOTATIONS_PREVIEW_ENABLED"] and not request.is_xhr:
        # the notes will be requested again via AJAX
        notes = []
    elif page is None or page == -1:
        notes = prepare_notes(get_annotations({"where.record": recid}))
    else:
        import re
        rgx = re.compile("^P\.([0-9]*?\,)*?" + str(page) + "(,|$|[_]\.*)")
        notes = prepare_notes(get_annotations({"where.marker": rgx,
                                               "where.record": recid}))

    if request.is_xhr:
        template = 'annotations/notes_fragment.html'
    else:
        template = 'annotations/notes.html'
        flash(_('This is a summary of all the comments that includes only the \
                 existing annotations. The full discussion is available \
                 <a href="' + url_for('comments.comments', recid=recid) +
                '">here</a>.'), "info")

    from invenio.utils.washers import wash_html_id

    return render_template(template,
                           notes=notes,
                           option='notes',
                           get_note_title=get_note_title,
                           note_is_collapsed=note_is_collapsed,
                           get_original_comment=get_original_comment,
                           wash_html_id=wash_html_id)


@comments_blueprint.route('/<int:recid>/notes_toggle/<string:path>',
                          methods=['GET', 'POST'])
@login_required
@request_record
def notes_toggle(recid, path):
    """Toggle notes collapsed/ expanded."""
    from .noteutils import note_collapse, note_expand, note_is_collapsed

    if note_is_collapsed(recid, path):
        note_expand(recid, path)
    else:
        note_collapse(recid, path)

    if not request.is_xhr:
        return redirect(url_for('annotations.notes', recid=recid))
    else:
        return 'OK'
