# -*- coding: utf-8 -*-
#
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

from fixture import DataSet
from invenio.modules.search.fixtures import CollectionData


class RnkMETHODData(DataSet):

    class RnkMETHOD_1:
        last_updated = None
        id = 1
        name = u'wrd'


class RnkCITATIONDATAData(DataSet):

    class RnkCITATIONDATA_1:
        object_name = u'citationdict'
        last_updated = None
        id = 1
        object_value = None

    class RnkCITATIONDATA_2:
        object_name = u'reversedict'
        last_updated = None
        id = 2
        object_value = None

    class RnkCITATIONDATA_3:
        object_name = u'selfcitdict'
        last_updated = None
        id = 3
        object_value = None

    class RnkCITATIONDATA_4:
        object_name = u'selfcitedbydict'
        last_updated = None
        id = 4
        object_value = None


class CollectionRnkMETHODData(DataSet):

    class CollectionRnkMETHOD_1_1:
        score = 100
        id_rnkMETHOD = RnkMETHODData.RnkMETHOD_1.ref('id')
        id_collection = 1 #CollectionData.siteCollection.ref('id')
