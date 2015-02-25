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

""" Bibcheck plugin to move (rename) fields"""
from invenio.utils.viaf import get_wikipedia_link, \
                                get_wiki_link_from_record, \
                                CFG_VIAF_WIKIPEDIA_LINK_BFO_FIELD, \
                                CFG_VIAF_WIKIPEDIA_LINK_SUBFIELD, \
                                CFG_VIAF_LINK_NAME_LABEL_SUBFIELD, \
                                CFG_VIAF_WIKIPEDIA_NAME_VALUE_SUBFIELD

from invenio.bibrecord import record_add_field,record_replace_field

def check_record(record, overwrite=True):
    """ Calculates wikipedia link based on viaf id"""

    maxi = 0
    for k in record.iterkeys():
        if record[k][-1][-1] > maxi:
            maxi = record[k][-1][-1]


    if not overwrite and get_wiki_link_from_record(record):
        record.warn("Author already had a link to wikipedia")
    else:
        control_nos = []
        if record.get('035',None):
            control_nos = [t[1] for d in record.get('035',()) if d and d[0] for t in d[0] if t and t[1]]
        for control_no in control_nos:
            if (control_no.find("|(VIAF)") != -1):
                viaf_id = control_no.split("|(VIAF)")[1]
                link = get_wikipedia_link(viaf_id)
                if link:
                    linkfield = ([(CFG_VIAF_LINK_NAME_LABEL_SUBFIELD,CFG_VIAF_WIKIPEDIA_NAME_VALUE_SUBFIELD),(CFG_VIAF_WIKIPEDIA_LINK_SUBFIELD,link)] , '', '', ' ', maxi)
                    if get_wiki_link_from_record(record):
                        for field in record[CFG_VIAF_WIKIPEDIA_LINK_BFO_FIELD]:
                            for subfield in field:
                                if type(subfield) is list and subfield[0] == CFG_VIAF_LINK_NAME_LABEL_SUBFIELD and subfield[1] == CFG_VIAF_WIKIPEDIA_NAME_VALUE_SUBFIELD:
                                    for sub in field:
                                        if type(sub) is list and sub[0] == CFG_VIAF_WIKIPEDIA_LINK_SUBFIELD:
                                            sub[1] = link

                    else:
                        record_add_field(record,CFG_VIAF_WIKIPEDIA_LINK_BFO_FIELD, \
                                subfields=[(CFG_VIAF_LINK_NAME_LABEL_SUBFIELD,CFG_VIAF_WIKIPEDIA_NAME_VALUE_SUBFIELD),(CFG_VIAF_WIKIPEDIA_LINK_SUBFIELD,link)])
                    record.set_amended("Added wiki link to author")
