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


def websearch_before_browse_handler(collection, **kwargs):
    from flask import flash, g
    from invenio.search_engine import create_exact_author_browse_help_link
    keys = ['p', 'p1', 'p2', 'p3', 'f', 'f1', 'f2', 'f3', 'rm', 'cc', 'ln', 'jrec', 'rg', 'aas', 'action']
    kwargs = dict(filter(lambda (k, v): k in keys, kwargs.iteritems()))
    print kwargs
    msg = create_exact_author_browse_help_link(**kwargs)
    if msg and len(msg)>0:
        flash(msg, 'websearch-after-search-form')
