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

import pprint
from string import rfind, strip
from datetime import datetime
from hashlib import md5

from flask import Blueprint, session, make_response, g, render_template, \
		request, flash, jsonify, redirect, url_for, current_app
from invenio.cache import cache
from invenio.intbitset import intbitset as HitSet
from invenio.sqlalchemyutils import db
from invenio.websearch_model import Collection, CollectionCollection
from invenio.websession_model import User
from invenio.webinterface_handler_flask_utils import _, InvenioBlueprint
from invenio.webuser_flask import current_user

from invenio.bibformat import format_record
from invenio.search_engine import search_pattern_parenthesised,\
		get_creation_date,\
		perform_request_search,\
		search_pattern

from sqlalchemy.sql import operators
not_guest = lambda: not current_user.is_guest()

blueprint = InvenioBlueprint('websearch_admin', __name__, url_prefix="/admin/websearch",
		config=[],
		breadcrumbs=[],
		menubuilder=[('main.admin.websearch', _('Search Admin'),
			'websearch_admin.index', 50)])
""" Previous inputs calculations not processed """
@cache.memoize(3600)



@blueprint.route('/', methods=['GET', 'POST'])
@blueprint.invenio_authenticated
#@blueprint.invenio_authorized('usemessages')
@blueprint.invenio_templated('websearch_admin_index.html')
def index():

	collection = Collection.query.get_or_404(1)
	return dict(collection=collection) 



@blueprint.route('/modifycollectiontree', methods=['GET', 'POST'])
#@blueprint.invenio_wash_urlargd({'id': (int, 0), 'id_dad': (int, 0), 'score': (int, 0)})
@blueprint.invenio_authenticated
@blueprint.invenio_templated('websearch_admin_index.html')
def modifycollectiontree():
    id = request.args.get('id', 0, type=int)
    id_dad = request.args.get('id_dad', 0, type=int)
    score = request.args.get('score', 0, type=int)
    flash(_("Bam, ajax style! id = %d id_dad = %d score = %d") % (id, id_dad, score), "info")

    collection = Collection.query.get_or_404(id)

    # check to see if it is only one dad
    if len(collection.dads) > 1:
        return "multiple dads"
    # get the dad
    olddad = collection.dads.pop()
    db.session.delete(olddad)
    newdad = Collection.query.get_or_404(id_dad) 
    newdad._collection_children.set(CollectionCollection(id_son=collection.id), score)

    db.session.commit()
    return dict()#redirect(url_for('.index'))

