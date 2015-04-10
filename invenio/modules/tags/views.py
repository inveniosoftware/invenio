# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013, 2015 CERN.
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

"""Invenio.modules.tags.blueprint: Tagging interface."""

from __future__ import unicode_literals

from flask import Blueprint, flash, jsonify, redirect, render_template, \
    request, url_for

from flask_breadcrumbs import default_breadcrumb_root, register_breadcrumb

from flask_login import current_user, login_required

from flask_menu import register_menu

from invenio.base.decorators import templated, wash_arguments
from invenio.base.globals import cfg
from invenio.base.i18n import _
from invenio.ext.sqlalchemy import db
from invenio.modules.accounts.models import User
from invenio.modules.collections.models import Collection
from invenio.modules.records.models import Record as Bibrec
from invenio.modules.search.views.search import response_formated_records

from werkzeug import LocalProxy

from .forms import AttachTagForm, CreateTagForm, DetachTagForm, EditTagForm, \
    TagAnnotationForm, validate_tag_exists, validate_user_owns_tag, validators
from .models import WtgTAG, WtgTAGRecord, wash_tag

# Uset settings
user_settings = LocalProxy(
    lambda:
    current_user['settings'].get('webtag',
                                 cfg['CFG_WEBTAG_DEFAULT_USER_SETTINGS']))

blueprint = Blueprint('webtag', __name__, url_prefix='/yourtags',
                      template_folder='templates', static_folder='static')

default_breadcrumb_root(blueprint, '.webaccount.tags')


@blueprint.route('/', methods=['GET', 'POST'])
@blueprint.route('/display', methods=['GET', 'POST'])
@blueprint.route('/display/cloud', methods=['GET', 'POST'])
@login_required
@templated('tags/display_cloud.html')
@register_menu(blueprint, 'personalize.tags', _('Your Tags'))
@register_breadcrumb(blueprint, '.', _('Your Tags'))
def display_cloud():
    """List of user's private/group/public tags."""
    user = User.query.get(current_user.get_id())
    tags = user.tags_query.order_by(WtgTAG.name).all()

    # Calculate document count for each tag
    min_count = 0
    max_count = 0
    for tag in tags:
        if tag.record_count > max_count:
            max_count = tag.record_count
        if tag.record_count < min_count:
            min_count = tag.record_count

    difference = float(max_count - min_count)
    if not difference:
        difference = 1.0

    # Assign sizes
    min_size = 1.0
    max_size = 2.0

    for tag in tags:
        size = min_size + \
            float(max_size - min_size) * \
            float(tag.record_count - min_count) / difference

        tag.css_size = str(size*100)

    return dict(user_tags=tags,
                display_mode='cloud')


@blueprint.route('/display/list', methods=['GET', 'POST'])
@login_required
@templated('tags/display_list.html')
@wash_arguments({'sort_by': (unicode, 'name'),
                 'order': (unicode, '')})
@register_breadcrumb(blueprint, '.list', _('Display as List'))
def display_list(sort_by, order):
    """List of user's private/group/public tags."""
    tags = User.query.get(current_user.get_id()).tags_query

    sort_by = str(sort_by)
    order = str(order)

    if sort_by == 'record_count':
        tags = tags.order_by(WtgTAG.record_count)
    else:
        tags = tags.order_by(WtgTAG.name)

    tags = tags.all()

    if order == 'desc':
        tags.reverse()

    return dict(user_tags=tags,
                display_mode='list')


@blueprint.route('/tag/<int:id_tag>/records', methods=['GET', 'POST'])
@login_required
@register_breadcrumb(blueprint, '.tags_details', _('Associated Records'))
def tag_details(id_tag):
    """List of documents attached to this tag."""
    if not id_tag:
        flash(_('Invalid tag id'), "error")
        return redirect(url_for('.display_cloud'))

    tag = WtgTAG.query.get(id_tag)

    if not tag:
        flash(_('Invalid tag id'), "error")
        return redirect(url_for('.display_cloud'))

    if tag.id_user != current_user.get_id():
        flash(_('You are not authorized to view this tag'), "error")
        return redirect(url_for('.display_cloud'))

    if not tag.records:
        flash(_('There are no documents tagged with ') + tag.name)
        return redirect(url_for('.display_cloud'))

    return response_formated_records([bibrec.id for bibrec in tag.records],
                                     Collection.query.get(1),
                                     'hb')


@blueprint.route('/tag/<int:id_tag>/edit', methods=['GET', 'POST'])
@login_required
@templated('tags/record_tags_test.html')  # FIXME: tag editor template missing?
@register_breadcrumb(blueprint, '.tag_edit', _('Edit tag'))
def tag_edit(id_tag):
    """List of documents attached to this tag."""
    id_user = current_user.get_id()
    tag = WtgTAG.query.get(id_tag)

    if not tag:
        flash(_('Invalid tag id'), "error")
        return redirect(url_for('.display_cloud'))

    if tag.id_user != id_user:
        flash(_('You are not authorized to view this tag'), "error")
        return redirect(url_for('.display_cloud'))

    form = EditTagForm(request.values, csrf_enabled=False, obj=tag)

    if form.validate_on_submit():
        form.populate_obj(tag)

        name_count = db.session.query(WtgTAG).\
            filter_by(id_user=id_user, name=tag.name).count()

        if name_count == 1:
            db.session.add(tag)
            db.session.commit()
            flash(_('Tag Successfully edited.'), 'success')

        else:
            flash(_('Tag name') + ' <strong>' + tag.name + '</strong> ' +
                  _('is already in use.'), 'error')

    return dict(tag=tag, form=form)


@blueprint.route('/tag/<int:id_tag>/annotations/<int:id_bibrec>',
                 methods=['GET', 'POST'])
@login_required
def update_annotation(id_tag, id_bibrec):
    """Change the annotation on relationship between record and tag."""
    from werkzeug.datastructures import MultiDict

    values = MultiDict(request.values)
    values['id_tag'] = id_tag
    values['id_bibrec'] = id_bibrec

    form = TagAnnotationForm(values, csrf_enabled=False)

    if form.validate():

        relation = db.session.query(WtgTAGRecord)\
            .filter(WtgTAGRecord.id_tag == id_tag)\
            .filter(WtgTAGRecord.id_bibrec == id_bibrec)\
            .one()

        relation.annotation = form.data.get('annotation_value', '')
        db.session.add(relation)
        db.session.commit()

        return relation.annotation

    else:
        return str(form.errors)


@blueprint.route('/record/<int:id_bibrec>/tags', methods=['GET', 'POST'])
@login_required
@templated('tags/record_tags_test.html')
@register_breadcrumb(blueprint, '.tags_details', _('Tag list'))
def record_tags(id_bibrec):
    """List of documents attached to this tag."""
    from .template_context_functions.tfn_webtag_record_tags \
        import template_context_function

    return dict(
        tag_list=template_context_function(
            id_bibrec, current_user.get_id()))


@blueprint.route('/tokenize/<int:id_bibrec>', methods=['GET', 'POST'])
@login_required
@wash_arguments({'q': (unicode, '')})
def tokenize(id_bibrec, q):
    """Data for tokeninput."""
    id_user = current_user.get_id()

    # Output only tags unattached to this record
    record = Bibrec.query.get(id_bibrec)

    tags = WtgTAG.query\
        .filter_by(id_user=id_user)\
        .filter(WtgTAG.name.like('%' + q + '%'))\
        .filter(db.not_(WtgTAG.records.contains(record)))\
        .order_by(WtgTAG.name)

    # If a tag with searched name does not exist, lets suggest creating it
    # Clean the name
    new_name = wash_tag(q)
    add_new_name = True

    response_tags = []
    for tag in tags.all():
        tag_json = tag.serializable_fields(set(['id', 'name']))
        response_tags.append(tag_json)

        # Check if it matches the search name
        if tag_json['name'] == new_name:
            add_new_name = False

    # If the name was not found
    if add_new_name:
        # Check if a tag with this name is already attached
        already_attached = WtgTAG.query\
            .join(WtgTAGRecord)\
            .filter(WtgTAG.name == new_name)\
            .filter(WtgTAGRecord.id_bibrec == id_bibrec)\
            .count()

        if not already_attached:
            tag_json = {'id': 0, 'name': new_name}
            response_tags.append(tag_json)

    return jsonify(dict(results=response_tags, query=q))


@blueprint.route('/record/<int:id_bibrec>/edit', methods=['GET', 'POST'])
@login_required
def editor(id_bibrec):
    """Edit your tags for `id_bibrec`.

    :param id_bibrec: record identifier
    """
    user = db.session.query(User).get(current_user.get_id())
    record = db.session.query(Bibrec).get(id_bibrec)

    tags = db.session.query(WtgTAG)\
        .filter_by(user=user)\
        .filter(WtgTAG.records.contains(record))

    tags_json = []
    for tag in tags.all():
        fields = tag.serializable_fields(set(['id', 'name']))
        fields['can_remove'] = True
        tags_json.append(fields)

    # invenio_templated cannot be used,
    # because this view is requested using AJAX
    return render_template('tags/record_editor.html', id_bibrec=id_bibrec,
                           record_tags=tags_json)


# Temporary solution to call validators, we need a better one
class Field(object):

    """Field class."""

    def __init__(self, attr, value):
        """Init."""
        setattr(self, attr, value)


@blueprint.route('/delete', methods=['GET', 'POST'])
@login_required
def delete():
    """Delete a tag."""
    response = {}
    response['action'] = 'delete'

    id_tags = request.values.getlist('id_tag', type=int)

    # Validate
    for id_tag in id_tags:
        try:
            field = Field('data', id_tag)
            validate_tag_exists(None, field)
            validate_user_owns_tag(None, field)
        except validators.ValidationError as ex:
            flash(ex.message, 'error')

    for id_tag in id_tags:
        tag = WtgTAG.query.get(id_tag)
        db.session.delete(tag)

    db.session.commit()

    # WtgTAG.query\
    #    .filter(WtgTAG.id.in_(id_tags))\
    #    .delete(synchronize_session=False)

    flash(_('Successfully deleted tags.'), 'success')

    return redirect(url_for('.display_list'))

# AJAX
# reposnse template:
#   action = name of action 'create' 'attach' 'detach'
#   success = True / False
#
#   if success:
#       id_tag = id of tag participating in process
#       id_bibrec = id of bibrec (if present in action)
#       items = created or deleted model objects
#
#   else:
#       errors = dict of errors from form


@blueprint.route('/create', methods=['GET', 'POST'])
@login_required
@register_breadcrumb(blueprint, '.create', _('New tag'))
@templated('tags/create.html')
def create():
    """Create a new tag."""
    response = {}
    response['action'] = 'create'

    user = User.query.get(current_user.get_id())

    form = CreateTagForm(request.values, csrf_enabled=False)

    if form.validate_on_submit() or\
       (request.is_xhr and form.validate()):
        new_tag = WtgTAG()
        form.populate_obj(new_tag)
        new_tag.user = user
        db.session.add(new_tag)
        db.session.flush()
        db.session.refresh(new_tag)

        if 'id_bibrec' in form.data and form.data['id_bibrec']:
            record = db.session.query(Bibrec).get(form.data['id_bibrec'])
            new_tag.records.append(record)
            db.session.add(new_tag)
            response['id_bibrec'] = form.data['id_bibrec']

        db.session.commit()
        db.session.refresh(new_tag)

        response['success'] = True
        response['id_tag'] = new_tag.id
        response['items'] = [new_tag.serializable_fields()]

        if request.is_xhr:
            return jsonify(response)
        else:
            return redirect(url_for('.display_list'))
    else:
        if request.is_xhr:
            response['success'] = False
            response['errors'] = form.errors

            return jsonify(response)
        else:
            return dict(form=form)


@blueprint.route('/attach', methods=['GET', 'POST'])
@login_required
def attach():
    """Attach a tag to a record."""
    response = {}
    response['action'] = 'attach'

    # Ajax - disable csrf
    form = AttachTagForm(request.values, csrf_enabled=False)

    if form.validate():
        association = WtgTAGRecord()
        form.populate_obj(association)

        db.session.add(association)
        db.session.commit()

        response['success'] = True
        response['id_tag'] = association.id_tag
        response['id_bibrec'] = association.id_bibrec
        response['items'] = [association.serializable_fields()]

    else:
        response['success'] = False
        response['errors'] = form.errors

    return jsonify(response)


@blueprint.route('/detach', methods=['GET', 'POST'])
@login_required
def detach():
    """Detach a tag from a record."""
    response = {}
    response['action'] = 'detach'

    # Ajax - disable csrf
    form = DetachTagForm(request.values, csrf_enabled=False)

    if form.validate():
        association = db.session.query(WtgTAGRecord) \
            .filter_by(id_tag=form.data['id_tag'],
                       id_bibrec=form.data['id_bibrec']).first()
        if association:
            db.session.delete(association)
            db.session.commit()

        response['success'] = True
        response['id_tag'] = association.id_tag
        response['id_bibrec'] = association.id_bibrec
        response['items'] = [association.serializable_fields()]

    else:
        response['success'] = False
        response['errors'] = form.errors

    return jsonify(response)
