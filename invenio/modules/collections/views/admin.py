# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2012, 2014, 2015 CERN.
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

"""Admin interface for collections."""

from __future__ import unicode_literals

from flask import Blueprint, abort, flash, g, redirect, render_template, \
    request, url_for

from flask_breadcrumbs import register_breadcrumb

from flask_login import current_user, login_required

from invenio.base.decorators import templated
from invenio.base.i18n import _, language_list_long
from invenio.ext.principal import permission_required
from invenio.ext.sqlalchemy import db

from ..forms import CollectionForm, TranslationsForm
from ..models import (
    Collection, CollectionCollection, CollectionPortalbox, Collectionname,
    Portalbox
)


def not_guest():
    """Not guest."""
    return not current_user.is_guest

blueprint = Blueprint('collections_admin', __name__,
                      url_prefix="/admin/collections",
                      template_folder='../templates'
                      )


@blueprint.route('/', methods=['GET', 'POST'])
@blueprint.route('/index', methods=['GET', 'POST'])
@login_required
@permission_required('cfgwebsearch')
@templated('search/admin_index.html')
@register_breadcrumb(blueprint, 'admin.collections_admin', _('WebSearch'))
def index():
    """WebSearch admin interface with editable collection tree."""
    collection = Collection.query.get_or_404(1)
    orphans = Collection.query.filter(
        db.not_(db.or_(
            Collection.id.in_(db.session.query(
                              CollectionCollection.id_son).subquery()),
            Collection.id.in_(db.session.query(
                              CollectionCollection.id_dad).subquery())
        ))).all()

    return dict(collection=collection, orphans=orphans)


@blueprint.route('/modifycollectiontree', methods=['POST'])
@login_required
@permission_required('cfgwebsearch')
def modifycollectiontree():
    """Handler for the tree changing operations triggered by the drag&drop."""
    # Get the requests parameters
    id_son = request.form.get('id_son', 0, type=int)
    id_dad = request.form.get('id_dad', 0, type=int)
    id_new_dad = request.form.get('id_new_dad', 0, type=int)
    score = request.form.get('score', 0, type=int)
    type_ = request.form.get('type', 'r')

    # Check if collection exits.
    Collection.query.get_or_404(id_son)

    if id_dad > 0:
        # Get only one record
        cc = CollectionCollection.query.filter(
            db.and_(
                CollectionCollection.id_son == id_son,
                CollectionCollection.id_dad == id_dad
            )).one()
        dad = Collection.query.get_or_404(id_dad)
        dad._collection_children.remove(cc)
        dad._collection_children.reorder()
    else:
        cc = CollectionCollection(
            id_dad=id_new_dad,
            id_son=id_son,
            type=type_)
        db.session.add(cc)

    if id_new_dad == 0:
        db.session.delete(cc)
    else:
        new_dad = Collection.query.get_or_404(id_new_dad)
        cc.id_dad = id_new_dad
        try:
            descendants = Collection.query.get(id_son).descendants_ids
            ancestors = new_dad.ancestors_ids
            if descendants & ancestors:
                raise
        except Exception:
            # Cycle has been detected.
            db.session.rollback()
            abort(406)
        new_dad._collection_children.reorder()
        new_dad._collection_children.insert(score, cc)

    # FIXME add dbrecs rebuild for modified trees.
    db.session.commit()
    return 'done'


@blueprint.route('/collectiontree', methods=['GET', 'POST'])
@login_required
@permission_required('cfgwebsearch')
def managecollectiontree():
    """Here is where managing the tree is possible."""
    collection = Collection.query.get_or_404(1)
    orphans = Collection.query.filter(
        Collection.id != CollectionCollection.id_dad,
        id != CollectionCollection.id_son).get_or_404(1)

    return dict(collection=collection, orphans=orphans)


@blueprint.route('/collection/<name>', methods=['GET', 'POST'])
@blueprint.route('/collection/view/<name>', methods=['GET', 'POST'])
@login_required
@permission_required('cfgwebsearch')
def manage_collection(name):
    """Manage collection."""
    collection = Collection.query.filter(
        Collection.name == name).first_or_404()
    form = CollectionForm(request.form, obj=collection)

    # gets the collections translations
    translations = dict((x.ln, x.value) for x in collection.collection_names)

    # Creating the translations form
    TranslationsFormFilled = TranslationsForm(language_list_long(),
                                              translations)
    translation_form = TranslationsFormFilled(request.form)

    return render_template('search/admin_collection.html',
                           collection=collection, form=form,
                           translation_form=translation_form)


@blueprint.route('/collection/update/<id_collection>', methods=['POST'])
@login_required
@permission_required('cfgwebsearch')
def update(id_collection):
    """Update page."""
    form = CollectionForm(request.form)
    if request.method == 'POST':  # and form.validate():
        collection = Collection.query.get_or_404(id_collection)
        form.populate_obj(collection)
        db.session.commit()
        flash(_('Collection was updated'), "info")
        return redirect(url_for('.index'))


@blueprint.route('/collection/new', methods=['GET', 'POST'])
@blueprint.route('/collection/add', methods=['GET', 'POST'])
@login_required
@permission_required('cfgwebsearch')
@templated('search/admin_collection.html')
def create_collection():
    """Create collection page."""
    form = CollectionForm()
    return dict(form=form)


@blueprint.route('/collection/update_translations<id>', methods=['POST'])
@login_required
@permission_required('cfgwebsearch')
def update_translations(id):
    """Update translations if the value is altered or not void."""
    collection = Collection.query.filter(Collection.id == id).first_or_404()

    for (lang, lang_long) in language_list_long():
        collection_name = Collectionname.query.filter(db.and_(
            Collectionname.id_collection == id,
            Collectionname.ln == lang,
            Collectionname.type == 'ln'
        )).first()

        if collection_name:
            if collection_name.value != request.form.get(lang):
                collection_name.value = request.form.get(lang)
                db.session.commit()
        else:
            if request.form.get(lang) != '':
                collection_name = Collectionname(collection, lang,
                                                 'ln', request.form.get(lang))
                db.session.add(collection_name)
                db.session.commit()

    flash(_('Collection was updated on n languages:'), "info")
    return redirect(url_for('.manage_collection', name=collection.name))


@blueprint.route('/collection/manage_portalboxes_order',
                 methods=['GET', 'POST'])
@login_required
@permission_required('cfgwebsearch')
def manage_portalboxes_order():
    """Manage order of portalboxes."""
    id_p = request.args.get('id', 0, type=int)
    id_collection = request.args.get('id_collection', 0, type=int)
    order = request.args.get('score', 0, type=int)

    collection = Collection.query.filter(
        Collection.id == id_collection).first_or_404()

    portalbox = \
        CollectionPortalbox.query.filter(db.and_(
            CollectionPortalbox.id_portalbox == id_p,
            CollectionPortalbox.id_collection == id_collection)).first_or_404()

    position = portalbox.position
    p_order = portalbox.score

    db.session.delete(portalbox)
    collection.portal_boxes_ln.set(
        CollectionPortalbox(id_collection, id_p, g.ln, position, p_order),
        order
    )
    db.session.commit()

    return ''


@blueprint.route('/collection/edit_portalbox', methods=['GET', 'POST'])
@login_required
@permission_required('cfgwebsearch')
def edit_portalbox():
    """Edit portal box."""
    portalbox = Portalbox.query.get(request.args.get_or_404('id', 0, type=int))
    return dict(portalbox=portalbox)
