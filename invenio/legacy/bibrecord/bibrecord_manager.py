# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013, 2014, 2015 CERN.
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

"""Perform BibRecord operations."""

from invenio.ext.script import Manager

manager = Manager(usage=__doc__)

# Define sub-manager
bibrecord_cache = Manager(usage="Manipulates BibRecord cache.")

# Add sub-manager
manager.add_command("cache", bibrecord_cache)


@bibrecord_cache.command
def reset(split_by=1000):
    """Reset bibrecord structure cache."""
    from invenio.modules.formatter.models import Bibfmt
    from invenio.base.scripts.cache import reset_rec_cache
    from invenio.legacy.search_engine import get_record
    from invenio.ext.sqlalchemy import db
    from invenio.utils.serializers import serialize_via_marshal

    def get_recstruct_record(recid):
        value = serialize_via_marshal(get_record(recid))
        b = Bibfmt(id_bibrec=recid, format='recstruct',
                   last_updated=db.func.now(), value=value)
        db.session.add(b)
        db.session.commit()

    reset_rec_cache('recstruct', get_recstruct_record, split_by=split_by)


def main():
    """Run manager command."""
    from invenio.base.factory import create_app
    app = create_app()
    manager.app = app
    manager.run()

if __name__ == '__main__':
    main()
