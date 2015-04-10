# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2006, 2007, 2008, 2010, 2011 CERN.
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

"""
BibUpload Engine configuration.
"""

from __future__ import unicode_literals

__revision__ = "$Id$"

CFG_BIBUPLOAD_CONTROLFIELD_TAGS = ['001', '002', '003', '004',
                                   '005', '006', '007', '008']

CFG_BIBUPLOAD_SPECIAL_TAGS = ['FFT', 'BDR', 'BDM']

CFG_BIBUPLOAD_DELETE_CODE = '0'

CFG_BIBUPLOAD_DELETE_VALUE = "__DELETE_FIELDS__"

CFG_BIBUPLOAD_OPT_MODES = ['insert', 'replace', 'replace_or_insert', 'reference',
        'correct', 'append', 'holdingpen', 'delete']
