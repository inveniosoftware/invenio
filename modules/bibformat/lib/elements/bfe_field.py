# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010 CERN.
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
"""BibFormat element - Prints a custom field
"""
__revision__ = "$Id$"

from invenio.bibformat_utils import parse_tag

def format(bfo, tag, limit, instances_separator=" ",
           subfields_separator=" ", extension=""):
    """
    Prints the given field of a record.
    If tag is in range [001, 010], this element assumes
    that it accesses a control field. Else it considers it
    accesses a data field.

    @param tag: the tag code of the field that is to be printed
    @param instances_separator: a separator between instances of field
    @param subfields_separator: a separator between subfields of an instance
    @param limit: the maximum number of values to display.
    @param extension: a text printed at the end if 'limit' has been exceeded
    """
    # Check if data or control field
    p_tag = parse_tag(tag)
    if p_tag[0].isdigit() and int(p_tag[0]) in range(0, 11):
        return  bfo.control_field(tag)
    elif p_tag[0].isdigit():
        # Get values without subcode.
        # We will filter unneeded subcode later
        if p_tag[1] == '':
            p_tag[1] = '_'
        if p_tag[2] == '':
            p_tag[2] = '_'
        values = bfo.fields(p_tag[0]+p_tag[1]+p_tag[2]) # Values will
                                                        # always be a
                                                        # list of
                                                        # dicts
    else:
        return ''

    x = 0
    instances_out = [] # Retain each instance output
    for instance in values:
        filtered_values = [value for (subcode, value) in instance.iteritems()
                          if p_tag[3] == '' or p_tag[3] == '%' \
                           or p_tag[3] == subcode]
        if len(filtered_values) > 0:
            # We have found some corresponding subcode(s)
            if limit.isdigit() and x + len(filtered_values) >= int(limit):
                # We are going to exceed the limit
                filtered_values = filtered_values[:int(limit)-x] # Takes only needed one
                if len(filtered_values) > 0: # do not append empty list!
                    instances_out.append(subfields_separator.join(filtered_values))
                    x += len(filtered_values) # record that so we know limit has been exceeded
                break # No need to go further
            else:
                instances_out.append(subfields_separator.join(filtered_values))
                x += len(filtered_values)

    ext_out = ''
    if limit.isdigit() and x > int(limit):
        ext_out = extension

    return instances_separator.join(instances_out) + ext_out
