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

"""Utility functions."""

from invenio.ext.cache import cache
from invenio.ext.sqlalchemy import db
from invenio.utils.datastructures import LazyDict

from .models import IdxINDEX, IdxINDEXField
from .registry import tokenizers

field_tokenizer_cache = LazyDict(
    lambda: dict(IdxINDEXField.get_field_tokenizers())
)


@cache.memoize()
def get_idx_indexer(name):
    """Return indexer field value."""
    return db.session.query(IdxINDEX.indexer).filter_by(name=name).scalar()


def load_tokenizers():
    """Load all the bibindex tokenizers and returns it."""
    return dict((module.__name__.split('.')[-1],
                 getattr(module, module.__name__.split('.')[-1], ''))
                for module in tokenizers)
