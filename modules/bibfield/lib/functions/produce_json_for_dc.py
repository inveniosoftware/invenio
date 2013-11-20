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

def produce_json_for_dc(self, fields=None):
    """
    Export the record in dublin core format.

    @param tags: list of tags to include in the output, if None or
                empty list all available tags will be included.
    """
    from invenio.bibfield_utils import get_producer_rules

    if not fields:
        fields = self.keys()

    out = []

    for field in fields:
        if field.startswith('__'):
            continue
        try:
            dc_rules = get_producer_rules(field, 'json_for_dc')
            for rule in dc_rules:
                field = self.get(rule[0], None)
                if field is None:
                    continue
                if not isinstance(field, list):
                    field = [field, ]
                for f in field:
                    for r in rule[1]:
                        tmp_dict = {}
                        for key, subfield in r.iteritems():
                            if not subfield:
                                tmp_dict[key] = f
                            else:
                                try:
                                    tmp_dict[key] = f[subfield]
                                except:
                                    try:
                                        tmp_dict[key] = self._try_to_eval(subfield, value=f)
                                    except Exception,e:
                                        self['__error_messages.cerror[n]'] = 'Producer CError - Unable to produce %s - %s' % (field, str(e))
                        if tmp_dict:
                            out.append(tmp_dict)
        except KeyError:
            self['__error_messages.cerror[n]'] = 'Producer CError - No producer rule for field %s' % field
    return out
