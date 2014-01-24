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


def get_persistent_identifiers_keys(keys):
    """
    Acording with @persistent_identifier it recollects all the fields that
    could be considered as persistent identifiers
    """
    from invenio.bibfield_config_engine import BibFieldParser

    def smart_set_element(the_list, index, value):
        try:
            the_list[index] = value
        except IndexError:
            for i in xrange(len(the_list), index+1):
                the_list.append(None)
            the_list[index] = value

    tmp = []
    for key in keys:
        try:
            if not BibFieldParser.field_definitions()[key]['persistent_identifier'] is None:
                smart_set_element(tmp, BibFieldParser.field_definitions()[key]['persistent_identifier'], key)
        except TypeError:
            # Work arround for [0] and [n]
            for kkey in BibFieldParser.field_definitions()[key]:
                if BibFieldParser.field_definitions()[kkey]['persistent_identifier']:
                    smart_set_element(tmp, BibFieldParser.field_definitions()[key]['persistent_identifier'], key)
        except:
            continue

    return filter(None, tmp)
