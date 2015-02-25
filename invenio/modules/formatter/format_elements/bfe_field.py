# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011 CERN.
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
"""BibFormat element - Prints a custom field
"""
__revision__ = "$Id$"

from six import iteritems
from invenio.modules.formatter.utils import parse_tag

def format_element(bfo, tag, limit, instances_separator=" ",
           subfields_separator=" ", extension="", output_pattern=""):
    """
    Prints the given field of a record.
    If tag is in range [001, 010], this element assumes
    that it accesses a control field. Else it considers it
    accesses a data field.

    <p>For eg. consider the following metdata:
    <pre>
 100__ $$aCalatroni, S$$uCERN
 245__ $$aStatus of the EP Simulations and Facilities for the SPL
 700__ $$aFerreira, L$$uCERN
 700__ $$aMacatrao, M$$uCERN
 700__ $$aSkala, A$$uCERN
 700__ $$aSosin, M$$uCERN
 700__ $$ade Waele, R$$uCERN
 700__ $$aWithofs, Y$$uKHLim, Diepenbeek
    </pre>
    The following calls to bfe_field would print:
    <pre>
    &lt;BFE_FIELD tag="700" instances_separator="&lt;br/>" subfields_separator=" - ">

    Ferreira, L - CERN
    Macatrao, M - CERN
    Skala, A - CERN
    Sosin, M - CERN
    de Waele, R - CERN
    Withofs, Y - KHLim, Diepenbeek
    </pre>
    </p>

    <p>For more advanced formatting, the <code>output_pattern</code>
    parameter can be used to output the subfields of each instance in
    the specified way. For eg. consider the following metadata:
    <pre>
 775__ $$b15. Aufl.$$c1995-1996$$nv.1$$pGrundlagen und Werkstoffe$$w317999
 775__ $$b12. Aufl.$$c1963$$w278898
 775__ $$b14. Aufl.$$c1983$$w107899
 775__ $$b13. Aufl.$$c1974$$w99635
    </pre>
    with the following <code>output_pattern</code>:

    <pre>
    &lt;a href="/record/%(w)s">%(b)s (%(c)s) %(n)s %(p)s&lt;/a>
    </pre>
    would print:<br/>

    <a href="/record/317999">15. Aufl. (1995-1996) v.1 Grundlagen und Werkstoffe</a><br/>
    <a href="/record/278898">12. Aufl. (1963) </a><br/>
    <a href="/record/107899">14. Aufl. (1983) </a><br/>
    <a href="/record/99635">13. Aufl. (1974) </a>

    <br/>(<code>instances_separator="&lt;br/>"</code> set for
    readability)<br/> The output pattern must follow <a
    href="http://docs.python.org/library/stdtypes.html#string-formatting-operations">Python
    string formatting</a> syntax. The format must use parenthesized
    notation to map to the subfield code. This currently restricts the
    support of <code>output_pattern</code> to non-repeatable
    subfields</p>

    @param tag: the tag code of the field that is to be printed
    @param instances_separator: a separator between instances of field
    @param subfields_separator: a separator between subfields of an instance
    @param limit: the maximum number of values to display.
    @param extension: a text printed at the end if 'limit' has been exceeded
    @param output_pattern: when specified, prints the subfields of each instance according to pattern specified as parameter (following Python string formatting convention)
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
        filtered_values = [value for (subcode, value) in iteritems(instance)
                          if p_tag[3] == '' or p_tag[3] == '%' \
                           or p_tag[3] == subcode]
        if len(filtered_values) > 0:
            # We have found some corresponding subcode(s)
            if limit.isdigit() and x + len(filtered_values) >= int(limit):
                # We are going to exceed the limit
                filtered_values = filtered_values[:int(limit)-x] # Takes only needed one
                if len(filtered_values) > 0: # do not append empty list!
                    if output_pattern:
                        try:
                            instances_out.append(output_pattern % DictNoKeyError(instance))
                        except:
                            pass
                    else:
                        instances_out.append(subfields_separator.join(filtered_values))
                    x += len(filtered_values) # record that so we know limit has been exceeded
                break # No need to go further
            else:
                if output_pattern:
                    try:
                        instances_out.append(output_pattern % DictNoKeyError(instance))
                    except:
                        pass
                else:
                    instances_out.append(subfields_separator.join(filtered_values))
                x += len(filtered_values)

    ext_out = ''
    if limit.isdigit() and x > int(limit):
        ext_out = extension

    return instances_separator.join(instances_out) + ext_out


class DictNoKeyError(dict):
    def __getitem__(self, key):
        if dict.__contains__(self, key):
            val = dict.__getitem__(self, key)
        else:
            val = ''
        return val
