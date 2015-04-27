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

"""Indexer Flask Blueprint."""

from __future__ import unicode_literals

import itertools

from invenio.base.i18n import _
from invenio.ext.admin.views import ModelView
from invenio.ext.sqlalchemy import db
from invenio.legacy.bibindex.engine_stemmer import get_stemming_language_map
from invenio.modules.knowledge import api as kapi
from invenio.modules.search.models import Field
from invenio.utils.datastructures import LazyDict

from werkzeug.local import LocalProxy

from wtforms import HiddenField
from wtforms.fields import BooleanField
from wtforms.fields import SelectField

from wtforms_sqlalchemy.fields import QuerySelectMultipleField

from .models import IdxINDEX
from .utils import load_tokenizers


_TOKENIZERS = LazyDict(load_tokenizers)

tokenizer_implemented = LocalProxy(
    lambda: [tokenizer for tokenizer
             in _TOKENIZERS if _TOKENIZERS[tokenizer]().implemented])


class IdxINDEXAdmin(ModelView):

    """Flask-Admin module to manage index list."""

    _can_create = True
    _can_edit = True
    _can_delete = True

    acc_view_action = 'cfgbibindex'
    acc_edit_action = 'cfgbibindex'
    acc_delete_action = 'cfgbibindex'

    # FIXME fix field "indexer" like a SelectField
    # @see perform_modifyindexer() function
    # FIXME fix field "names"
    form_overrides = dict(
        remove_stopwords=BooleanField,
        remove_html_markup=BooleanField,
        remove_latex_markup=BooleanField,
        synonym_kbrs=SelectField,
        stemming_language=SelectField,
        tokenizer=SelectField,
        fields=QuerySelectMultipleField,
        last_updated=HiddenField,
    )

    form_args = dict(
        synonym_kbrs=dict(
            label=_("Knowledge base name"),
            choices=LocalProxy(
                lambda:
                [('', _('-None-'))] +
                [(k, k) for k in [(x[0]+','+x[1]) for x in itertools.product(
                    kapi.get_all_kb_names(),
                    ['exact', 'leading_to_comma', 'leading_to_number']
                )]]
            )
        ),
        stemming_language=dict(
            label=_("Stemming language"),
            choices=LocalProxy(
                lambda:
                [('', _('-None-'))] +
                [(k, k) for k in get_stemming_language_map()]
            )
        ),
        tokenizer=dict(
            label=_("Tokenizer"),
            choices=LocalProxy(
                lambda: [(x, x) for x in tokenizer_implemented]
            )
        ),
        fields=dict(
            label=_("Index fields"),
            allow_blank=True,
            query_factory=lambda: Field.query.all(),
            get_pk=lambda i: i.id, get_label=lambda i: i.name
        )
    )

    def __init__(self, app, *args, **kwargs):
        """Constructor.

        :param app: flask application
        """
        super(IdxINDEXAdmin, self).__init__(*args, **kwargs)


def register_admin(app, admin):
    """Called on app initialization to register administration interface."""
    category = 'Indexes'
    admin.add_view(
        IdxINDEXAdmin(app, IdxINDEX, db.session,
                      name='Index', category=category,
                      endpoint="IdxINDEX")
    )
