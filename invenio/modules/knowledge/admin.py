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

"""Knowledge Flask Blueprint."""

import os

from flask import request

from invenio.base.i18n import _
from invenio.ext.admin.views import ModelView
from invenio.ext.sqlalchemy import db
from invenio.modules.collections.models import Collection

from .forms import DynamicKnowledgeForm, KnowledgeForm, KnwKBRVALForm, \
    TaxonomyKnowledgeForm, WrittenAsKnowledgeForm
from .models import KnwKB, KnwKBRVAL


def KnwKBRVAL_id_knwKB_formatter(view, context, model, name):
    """Formatter for the id_knwKB: return the Knowledge name instead."""
    return model.kb.name


def Knowledge_kbtype_formatter(view, context, model, name):
    """Formatter for the kbtype: return the Knowledge name instead."""
    value = model.kbtype
    return next((key for key, val in KnwKB.KNWKB_TYPES.items() if val == value),
                None)


class KnwKBRVALAdmin(ModelView):

    """Flask-Admin module to manage Knowledge Base Mappings."""

    form = KnwKBRVALForm

    column_list = ['id_knwKB', 'm_key', 'm_value']
    column_labels = dict(
        id_knwKB='Knowledge',
        m_key='Map From',
        m_value='To',)
    column_formatters = dict(
        id_knwKB=KnwKBRVAL_id_knwKB_formatter
    )
    column_sortable_list = ('m_key', 'm_value', 'id_knwKB')
    column_searchable_list = ('m_key', 'm_value')
    column_default_sort = 'id_knwKB'
    # TODO add filter for id_knwKB!
    column_filters = ['m_key']

    def __init__(self, app, *args, **kwargs):
        """Constructor.

        :param app: flask application
        """
        super(KnwKBRVALAdmin, self).__init__(*args, **kwargs)


class KnowledgeAdmin(ModelView):

    """Flask-Admin module to manage knowledge."""

    _can_create = True
    _can_edit = True
    # TODO check if multiple deletes of taxonomy type, also delete the
    # associated files.
    _can_delete = True

    acc_view_action = 'cfgbibknowledge'
    acc_edit_action = 'cfgbibknowledge'
    acc_delete_action = 'cfgbibknowledge'

    form = KnowledgeForm

    column_list = ('name', 'kbtype', 'description')
    column_formatters = dict(
        kbtype=Knowledge_kbtype_formatter
    )
    column_filters = ('kbtype',)
    # FIXME wait that Issue #2690 is fixed to finish the works
    # column_choices = {
    #    'kbtype': [(v, k) for (k, v) in KnwKB.KNWKB_TYPES.iteritems()]
    # }
    column_sortable_list = ('name', 'kbtype')

    list_template = 'knowledge/list.html'

    def after_model_change(self, form, model, is_created):
        """Save model."""
        super(KnowledgeAdmin, self).after_model_change(form, model, is_created)

        if form.kbtype.data == KnwKB.KNWKB_TYPES['dynamic']:
            id_collection = form.id_collection.data or None
            collection = Collection.query.filter_by(
                id=id_collection).one() if id_collection else None

            model.set_dyn_config(
                field=form.output_tag.data,
                expression=form.search_expression.data,
                collection=collection)

        if form.kbtype.data == KnwKB.KNWKB_TYPES['taxonomy']:
            if form.tfile.data:
                file_name = model.get_filename()
                file_data = request.files[form.tfile.name].read()

                with open(file_name, 'w') as f:
                    f.write(file_data)

    def edit_form(self, obj=None):
        """Edit form."""
        kbtype = request.args['kbtype'] if 'kbtype' in request.args else 'w'

        if kbtype == KnwKB.KNWKB_TYPES['written_as']:
            self.form = WrittenAsKnowledgeForm
        elif kbtype == KnwKB.KNWKB_TYPES['dynamic']:
            self.form = DynamicKnowledgeForm
        else:
            self.form = TaxonomyKnowledgeForm

        form = self.form(obj=obj)

        if not form.is_submitted():
            # load extra data: obj => form
            if kbtype == KnwKB.KNWKB_TYPES['dynamic']:
                if obj.kbdefs:
                    form.id_collection.data = obj.kbdefs.id_collection
                    form.output_tag.data = obj.kbdefs.output_tag
                    form.search_expression.data = obj.kbdefs.search_expression

            if kbtype == KnwKB.KNWKB_TYPES['taxonomy']:
                file_name = obj.get_filename()
                if os.path.isfile(file_name):
                    form.tfile.label.text = form.tfile.label.text + " *"
                    # TODO add the possibility to download the file
                    form.tfile.description = _("Already uploaded %(name)s",
                                               name=obj.get_filename())

        form.kbtype.data = kbtype

        return form

    def create_form(self, obj=None):
        """Create form."""
        kbtype = request.args['kbtype'] if 'kbtype' in request.args else 'w'

        if kbtype == KnwKB.KNWKB_TYPES['written_as']:
            self.form = WrittenAsKnowledgeForm
        elif kbtype == KnwKB.KNWKB_TYPES['dynamic']:
            self.form = DynamicKnowledgeForm
        else:
            self.form = TaxonomyKnowledgeForm

        form = self.form()
        form.kbtype.data = kbtype

        return form

    def get_query(self):
        """Get query."""
        return KnwKB.query

    def __init__(self, app, *args, **kwargs):
        """Constructor.

        :param app: flask application
        """
        super(KnowledgeAdmin, self).__init__(*args, **kwargs)


def register_admin(app, admin):
    """Called on app initialization to register administration interface."""
    category = 'Knowledge'
    admin.add_view(
        KnowledgeAdmin(app, KnwKB, db.session,
                       name='Knowledge Base', category=category,
                       endpoint="kb")
    )
    admin.add_view(
        KnwKBRVALAdmin(app, KnwKBRVAL, db.session,
                       name="Knowledge Mappings", category=category,
                       endpoint="kbrval")
    )
