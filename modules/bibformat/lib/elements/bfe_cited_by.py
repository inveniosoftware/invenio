# -*- coding: utf-8 -*-
## $Id$

## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005 CERN.
##
## The CDSware is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## The CDSware is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDSware; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

def format(bfo, separator='; '):
    """
    Prints a list of records citing this record
    
    @param separator a separator between citations
    """
    from urllib import quote
    from invenio.config import weburl

    primary_report_numbers = bfo.fields('037__a')
    additional_report_numbers = bfo.fields('088__a')

    primary_citations = map(lambda x: '<a href="'+weburl+'/search?f=reference&p='+quote(x)+'">'+x+'</a>', primary_report_numbers)
    additional_citations = map(lambda x: '<a href="'+weburl+'/search?f=reference&p='+quote(x)+'">'+x+'</a>', additional_report_numbers)

    citations = primary_citations
    citations.extend(additional_citations)

    return separator.join(citations)
