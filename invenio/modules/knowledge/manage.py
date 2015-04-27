# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015 CERN.
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

"""Perform knowledge operations."""

import os
import sys

from flask import current_app

from invenio.ext.script import Manager

from sqlalchemy.orm.exc import NoResultFound

from .api import get_kb_by_name
from .utils import load_kb_mappings_file

manager = Manager(usage=__doc__)


@manager.command
@manager.option('--name', '-n', dest='name')
@manager.option('--file', '-f', dest='filepath',
                help='Load knowledge base from this file.')
@manager.option('--sep', '-s', dest='separator',
                help='Separator between values. Defaults to "---".',
                default="---")
def load(name, filepath, separator="---"):
    """Load given file into knowledge base.

    Simply load data into an existing knowledge base:

    .. code-block:: console

        $ inveniomanage knowledge load mykb /path/to/file.kb

    The file is expected to have a mapping with values: ``foo<seperator>bar`` (per line)

    ``<separator>`` is by default set to **---**, but can be overridden with
    ``-s someseperator`` or ``--sep someseperator``.
    """
    current_app.logger.info(">>> Going to load knowledge base {0} into '{1}'...".format(
        filepath, name
    ))
    if not os.path.isfile(filepath):
        current_app.logger.error(
            "Path to non-existing file\n",
            file=sys.stderr
        )
        sys.exit(1)
    try:
        get_kb_by_name(name)
    except NoResultFound:
        current_app.logger.error(
            "KB does not exist\n",
            file=sys.stderr
        )
        sys.exit(1)
    num_added = load_kb_mappings_file(name, filepath, separator)
    current_app.logger.info(
        ">>> Knowledge '{0}' updated successfully with {1} entries.".format(
            name, num_added
        )
    )


def main():
    """Run manager."""
    from invenio.base.factory import create_app
    app = create_app()
    manager.app = app
    manager.run()
