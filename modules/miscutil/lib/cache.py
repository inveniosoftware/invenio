# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2012 CERN.
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

from flaskext.cache import Cache

class SafeCache(Cache):
    #FIXME Let's fork the Flask-Cache extension later on and add connection
    #      checking for cache engine.

    with_jinja2_ext = True

    def set(self, *args, **kwargs):
        try:
            return Cache.set(self, *args, **kwargs)
        except:
            pass

    def get(self, *args, **kwargs):
        try:
            return Cache.get(self, *args, **kwargs)
        except:
            return None

cache = SafeCache()
