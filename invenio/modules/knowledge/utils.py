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

"""Knowledge utilities."""

from flask import current_app

from .api import add_kb_mapping


def load_kb_mappings_file(kbname, kbfile, separator):
    """Add KB values from file to given KB returning rows added."""
    num_added = 0
    with open(kbfile) as kb_fd:
        for line in kb_fd:
            if not line.strip():
                continue
            try:
                key, value = line.split(separator)
            except ValueError:
                # bad split, pass
                current_app.logger.error("Error splitting: {0}".format(line))
                continue
            add_kb_mapping(kbname, key, value)
            num_added += 1
    return num_added
