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

"""WebSearch Admin Flask Blueprint"""

from flask import Blueprint, session, make_response, g, render_template, \
        request, flash, jsonify, redirect, url_for, current_app
from invenio.cache import cache
from invenio.intbitset import intbitset as HitSet
from invenio.sqlalchemyutils import db
from invenio.websearch_model import Collection, CollectionCollection, \
        Collectionname
from invenio.websession_model import User
from invenio.webinterface_handler_flask_utils import _, InvenioBlueprint
from invenio.webuser_flask import current_user

from invenio.bibformat import format_record
from invenio.search_engine import search_pattern_parenthesised,\
        get_creation_date,\
        perform_request_search,\
        search_pattern

from invenio.messages import language_list_long

# imports the necessary forms
from websearch_admin_forms import CollectionForm

from wtforms.ext.sqlalchemy.orm import model_form

from sqlalchemy.sql import operators
not_guest = lambda: not current_user.is_guest()

blueprint = InvenioBlueprint(
        'websearch_admin',
        __name__,
        url_prefix="/admin/websearch",
        config=[],
        breadcrumbs=[],
        menubuilder=[('main.admin.websearch', _('Configure WebSearch'),
            'websearch_admin.index', 50)])


""" Previous inputs calculations not processed """


@cache.memoize(3600)



@blueprint.route('/', methods=['GET', 'POST'])
@blueprint.route('/index', methods=['GET', 'POST'])
@blueprint.invenio_authenticated
#@blueprint.invenio_authorized('usemessages')
@blueprint.invenio_templated('websearch_admin_index.html')
def index():

    collection = Collection.query.get_or_404(1)
    orphans = Collection.query.filter(db.and_(
            Collection.id != CollectionCollection.id_dad, \
            id != CollectionCollection.id_son)).get_or_404(1)

    return dict(collection=collection)


@blueprint.route('/modifycollectiontree', methods=['GET', 'POST'])
@blueprint.invenio_authenticated
@blueprint.invenio_templated('websearch_admin_index.html')
def modifycollectiontree():
    id = request.args.get('id', 0, type=int)
    id_dad = request.args.get('id_dad', 0, type=int)
    score = request.args.get('score', 0, type=int)
    flash(_("id = %d id_dad = %d score = %d") % (id, id_dad, score), "info")

    collection = Collection.query.get_or_404(id)

    # check to see if it is only one dad
    if len(collection.dads) > 1:
        return "multiple dads"
    # get the dad
    olddad = collection.dads.pop()
    db.session.delete(olddad)
    newdad = Collection.query.get_or_404(id_dad)
    newdad._collection_children.set(CollectionCollection(id_son=collection.id,
        type=collection.type), score)

    db.session.commit()
    return dict()#redirect(url_for('.index'))


"""
Here is where managing the tree is possible
"""


@blueprint.route('/collectiontree', methods=['GET', 'POST'])
@blueprint.invenio_authenticated
def managecollectiontree():

    collection = Collection.query.get_or_404(1)
    orphans = Collection.query.filter(
            Collection.id != CollectionCollection.id_dad,
            id != CollectionCollection.id_son).get_or_404(1)

    return dict()


@blueprint.route('/collection/<name>', methods=['GET', 'POST'])
@blueprint.route('/collection/view/<name>', methods=['GET', 'POST'])
@blueprint.invenio_authenticated
#@blueprint.invenio_templated('websearch_admin_collection.html')
def manage_collection(name):
    collection = Collection.query.filter(Collection.name==name).first_or_404()
    form = CollectionForm(request.form, obj = collection)

    return render_template('websearch_admin_collection.html', \
            collection = collection, form=form)


@blueprint.route('/collection/update<id>', methods=['POST'])
@blueprint.invenio_authenticated
def update(id):
    form = CollectionForm(request.form)

    if  request.method == 'POST':# and form.validate():
        #collection_id = request.form.id
        collection = Collection.query.filter(Collection.id==id).first_or_404()

        form.populate_obj(collection)

        db.session.commit()

        flash(_('Collection was updated'), "info")
        return redirect(url_for('.index'))


@blueprint.route('/collection/new', methods=['GET', 'POST'])
@blueprint.route('/collection/add', methods=['GET', 'POST'])
@blueprint.invenio_authenticated
@blueprint.invenio_templated('websearch_admin_collection.html')
def create_collection():
    form = CollectionForm()
    return dict(form=form)


"""
updates translations if the value is altered or not void
"""


@blueprint.route('/collection/update_translations<id>', methods=['POST'])
@blueprint.invenio_authenticated
def update_translations(id):
    collection = Collection.query.filter(Collection.id==id).first_or_404()

    for (lang, lang_long) in language_list_long():

        collection_name = Collectionname.query.filter(
                db.and_(Collectionname.id_collection==id,
            Collectionname.ln == lang, Collectionname.type=='ln')).first()

        if collection_name:
            if collection_name.value != request.form.get(lang):
                collection_name.value = request.form.get(lang)
                db.session.commit()
        else:
            if request.form.get(lang) != '':
                collection_name = Collectionname(collection, lang, \
                       'ln', request.form.get(lang))
                db.session.add(collection_name)
                db.session.commit()

    flash(_('Collection was updated on n languages:'), "info")
    return redirect(url_for('.manage_collection', name = collection.name))
