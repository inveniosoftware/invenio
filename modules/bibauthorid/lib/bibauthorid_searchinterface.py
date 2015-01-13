# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2011 CERN.
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
'''
    This file contains the functions, which are used by the search engine
    to extract information about the authors.
'''

from invenio.bibauthorid_dbinterface import get_confirmed_papers_of_author  # emitting #pylint: disable-msg=W0611
from invenio.bibauthorid_dbinterface import get_authors_of_claimed_paper  # emitting #pylint: disable-msg=W0611
