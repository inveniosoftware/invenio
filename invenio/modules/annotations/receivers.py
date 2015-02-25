# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014 CERN.
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

from invenio.base.globals import cfg


def extract_notes(mapper, connection, target):
    if cfg['ANNOTATIONS_NOTES_ENABLED'] and target.star_score == 0:
        from .noteutils import extract_notes_from_comment
        revs = extract_notes_from_comment(target)
        if len(revs) > 0:
            from invenio.modules.annotations.api import add_annotation
            for rev in revs:
                add_annotation(model='annotation_note', **rev)
