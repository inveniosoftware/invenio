# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011 CERN.
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

""" Utlis for the WebNews module """

__revision__ = "$Id$"

# GENERAL IMPORTS
import re

# CONSTANT VARIABLES
# Regex for the nth element
PAT_NTH = r'(\w+)\[(\d+)\]'
def REP_NTH(matchobj):
    return "%s:eq(%s)" % (str(matchobj.group(1)), str(int(matchobj.group(2))-1))
FLG_NTH = 0
# Regex for the id attribute
PAT_IDA = r'\*\[@id=[\'"]([\w\-]+)[\'"]\]'
REP_IDA = r'#\1'
FLG_IDA = 0

def convert_xpath_expression_to_jquery_selector(xpath_expression):
    """
    Given an XPath expression this function
    returns the equivalent jQuery selector.
    """

    tmp_result = xpath_expression.strip('/')
    tmp_result = tmp_result.split('/')
    tmp_result = [_x2j(e) for e in zip(tmp_result, range(len(tmp_result)))]
    jquery_selector = '.'.join(tmp_result)

    return jquery_selector

def _x2j((s, i)):
    """
    Private helper function that converts each element of an XPath expression
    to the equivalent jQuery selector using regular expressions.
    """

    s = re.sub(PAT_IDA, REP_IDA, s, FLG_IDA)
    s = re.sub(PAT_NTH, REP_NTH, s, FLG_NTH)
    s = '%s("%s")' % (i and 'children' or '$', s)

    return s

