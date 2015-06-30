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

"""Comment utility functions."""

from flask import request

from invenio.modules.comments.models import CmtRECORDCOMMENT


def comments_nb_counts():
    """Get number of comments for the record `recid`."""
    recid = request.view_args.get('recid')

    if recid is None:
        return
    elif recid == 0:
        return 0
    else:
        return CmtRECORDCOMMENT.count(*[
            CmtRECORDCOMMENT.id_bibrec == recid,
            CmtRECORDCOMMENT.star_score == 0,
            CmtRECORDCOMMENT.status.notin_('dm', 'da')
        ])


def reviews_nb_counts():
    """Get number of reviews for the record `recid`."""
    recid = request.view_args.get('recid')

    if recid is None:
        return
    elif recid == 0:
        return 0
    else:
        return CmtRECORDCOMMENT.count(*[
            CmtRECORDCOMMENT.id_bibrec == recid,
            CmtRECORDCOMMENT.star_score > 0,
            CmtRECORDCOMMENT.status.notin_(['dm', 'da'])
        ])
