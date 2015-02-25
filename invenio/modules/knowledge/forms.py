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

"""Knowledge Forms."""

from invenio.base.i18n import _
from invenio.modules.collections.models import Collection
from invenio.utils.forms import InvenioBaseForm

from werkzeug.local import LocalProxy

from wtforms import FileField, Form, HiddenField, \
    SelectField, StringField, TextAreaField

from .api import query_get_kb_by_type


class KnwKBRVALForm(Form):

    """KnwKBRVAL Form."""

    m_key = StringField(label="Map From")
    m_value = StringField(label="To")
    id_knwKB = SelectField(
        label=_('Knowledge'),
        choices=LocalProxy(lambda: [
            (k.id, k.name) for k in
            query_get_kb_by_type('written_as').all()]
        ),
        coerce=int,
    )


class KnowledgeForm(InvenioBaseForm):

    """Knowledge form."""

    name = StringField()
    description = TextAreaField()
    kbtype = HiddenField()


class WrittenAsKnowledgeForm(KnowledgeForm):

    """Written As Knowledge form."""


class DynamicKnowledgeForm(KnowledgeForm):

    """Dynamic Knowledge form."""

    output_tag = StringField(label="Field")
    search_expression = StringField(label="Expression")
    id_collection = SelectField(
        'Collection',
        coerce=int,
        choices=LocalProxy(lambda:
                           [(0, _('-None-'))] +
                           [(c.id, c.name) for c in Collection.query.all()])
    )


class TaxonomyKnowledgeForm(KnowledgeForm):

    """Taxonomy Knowledge form."""

    tfile = FileField(label="File")
