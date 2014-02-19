# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2014 CERN.
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

from flask import Blueprint, render_template, request, redirect, flash
from flask.ext.login import login_required
from flask.ext.login import current_user

from invenio.modules.accounts.models import User

from .api import add_annotation, get_annotations
from .forms import WebPageAnnotationForm

blueprint = Blueprint('annotations',
                      __name__,
                      url_prefix="/annotations",
                      template_folder='templates',
                      static_folder='static')


def get_username_by_id(id):
    return User.query.filter(User.id == id).one().nickname


def permission_builder(public, groups=None):
    d = {}
    if groups is None:
        groups = []
    d['public'] = public
    d['groups'] = groups
    return d


@blueprint.route('/ping/<string:message>', methods=['GET'])
@blueprint.route('/ping/', methods=['GET'])
def ping(message=""):
    return "PONG: " + message


@blueprint.route('/menu', methods=['GET'])
def menu():
    # we need the after-login referrer to be the main page, not the modal dialog
    original_referrer = request.referrer
    return render_template("annotations/menu.html",
                           original_referrer=original_referrer)


@blueprint.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    form = WebPageAnnotationForm(request.form)
    if form.validate_on_submit():
        # FIXME: use form.data instead of manual fields
        add_annotation(model='annotation',
                       who=current_user.get_id(),
                       where=form.url.data,
                       what=form.body.data,
                       perm=permission_builder(form.public.data))
        from flask.ext.babel import gettext  # "unlazy" translation hack
        flash(gettext("Annotation saved."), "info")
        if not request.is_xhr:
            return redirect(request.referrer)
    else:
        form.url.data = request.args.get("target")
    return render_template('annotations/add.html', form=form)


@blueprint.route('/view', methods=['GET', 'POST'])
def view():
    return render_template('annotations/view.html',
                           public_annotations=get_annotations(
                               {"where": request.args.get("target"),
                                "perm": {"public": True, "groups": []}}),
                           private_annotations=get_annotations(
                               {"where": request.args.get("target"),
                                "who": current_user.get_id(),
                                "perm": {"public": False, "groups": []}}),
                           get_username_by_id=get_username_by_id)
