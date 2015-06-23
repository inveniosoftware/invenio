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


from invenio.base.utils import toposort_depends
from invenio.modules.pidstore.recordext.functions import reserve_recid
from invenio_records.signals import before_record_insert


def get_creation_date(recid):
    """Return creation date for given record."""
    from invenio_records.models import Record as Bibrec
    try:
        return Bibrec.query.get(recid).creation_date
    except AttributeError:
        return None


@before_record_insert.connect
@toposort_depends(reserve_recid.reserve_recid)
def creation_date(record, *args, **kwargs):
    if record.get('creation_date', None) is not None:
        record['creation_date'] = get_creation_date(record['recid'])
