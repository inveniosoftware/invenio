# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2013 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

from flask.ext.login import current_user
from invenio.webtag_queries import tags_for_html_brief

def tag_list(recid):
    """
    @param recid: Id of document
    @return List of tags atached to this document visible by current user
    """

    if recid:
        tags = tags_for_html_brief(recid, current_user.get_id()).all()
        response = []
        for tag in tags:
            response.append(tag.serializable_fields({'name'}))

        return response
