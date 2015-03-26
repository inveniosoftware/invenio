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

"""Implement hit counters."""

import string

from intbitset import intbitset
from sqlalchemy.sql.expression import cast

from invenio.ext.sqlalchemy import db
from invenio.modules.records import models
from invenio.modules.records.models import Record
from invenio.legacy.search_engine import get_field_tags

from .models import IdxINDEX


def get_nbhits_in_bibrec(term, f):
    """Return number of hits in bibrec table. Term is usually a date string."""
    column = (Record.modification_date if f == 'datemodified' else
              Record.creation_date)
    return Record.query.filter(
        cast(column, db.String).like(term + '%')
    ).value(db.func.count(Record.id))


def get_nbhits_in_bibwords(word, f):
    """Return number of hits for 'word' inside words index for field 'f'."""
    model = IdxINDEX.idxWORDF(f or "anyfield")
    if model is None:
        return 0
    hitlist = intbitset()
    for item in model.query.filter_by(term=word).values('hitlist'):
        hitlist |= intbitset(item[0])
    return len(hitlist)


def get_nbhits_in_idxphrases(word, f):
    """Return number of hits for 'word' inside phrase index for field 'f'."""
    model = IdxINDEX.idxPHRASEF(f or "anyfield")
    if model is None:
        return 0
    hitlist = intbitset()
    for item in model.query.filter_by(term=word).values('hitlist'):
        hitlist |= intbitset(item[0])
    return len(hitlist)


def get_nbhits_in_bibxxx(p, f, in_hitset=None):
    """Return number of hits for 'word' inside words index for field 'f'."""
    # determine browse field:
    if not f and string.find(p, ":") > 0:
        # does 'p' contain ':'?
        f, p = string.split(p, ":", 1)

    # FIXME: quick hack for the journal index
    if f == 'journal':
        return get_nbhits_in_bibwords(p, f)

    # construct 'tl' which defines the tag list (MARC tags) to search in:
    tl = []
    if f[0].isdigit() and f[1].isdigit():
        tl.append(f)  # 'f' seems to be okay as it starts by two digits
    else:
        # deduce desired MARC tags on the basis of chosen 'f'
        tl = get_field_tags(f)
    # start searching:
    hitlist = intbitset()
    for t in tl:
        # deduce into which bibxxx table we will search:
        digit1, digit2 = int(t[0]), int(t[1])
        model = getattr(models, 'Bib{0}{1}x'.format(digit1, digit2))

        if len(t) != 6 or t[-1:] == '%':
            # only the beginning of field 't' is defined, so add wildcard
            # character:
            condition = model.tag.like(t + '%')
        else:
            condition = model.tag == t

        res = model.query.join(model.bibrecs).filter(condition).values(
            'id_bibrec')

        hitlist |= intbitset([row[0] for row in res])

    if in_hitset is None:
        nbhits = len(hitlist)
    else:
        nbhits = len(hitlist & in_hitset)
    return nbhits
