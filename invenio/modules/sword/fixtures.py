# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013 CERN.
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

from fixture import DataSet


class SwrREMOTESERVERData(DataSet):

    class SwrREMOTESERVER_1:
        id = 1L
        username = u'CDS_Invenio'
        url_base_record = u'http://arxiv.org/abs'
        password = u'sword_invenio'
        xml_servicedocument = ''
        realm = u'SWORD at arXiv'
        name = u'arXiv'
        last_update = 0L
        email = u'admin'
        host = u'arxiv.org'
        url_servicedocument = u'https://arxiv.org/sword-app/servicedocument'
