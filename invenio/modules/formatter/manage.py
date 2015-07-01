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

"""Perform template operations."""

from __future__ import print_function

import os
import re
import shutil

from six import iteritems

from invenio.ext.script import Manager

manager = Manager(usage=__doc__)


@manager.option('-o', '--output-format', dest='output_format',
                default="HB", help="Specify output format/s (default HB)")
def expunge(output_format="HB"):
    """Remove static output formats from cache."""
    from invenio.ext.sqlalchemy import db
    from invenio.modules.formatter.models import Bibfmt

    # Make it uppercased as it is stored in database.
    output_format = output_format.upper()
    print(">>> Cleaning %s cache..." % (output_format, ))
    # Prepare where expression.
    filter_format = (
        Bibfmt.format == output_format if ',' not in output_format else
        Bibfmt.format.in_(map(lambda x: x.strip(), output_format.split(',')))
    )
    Bibfmt.query.filter(filter_format).delete(synchronize_session=False)
    db.session.commit()


def main():
    """Run manager."""
    from invenio.base.factory import create_app
    app = create_app()
    manager.app = app
    manager.run()

if __name__ == '__main__':
    main()
