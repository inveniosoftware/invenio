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

"""
    invenio.modules.deposit.url_converters
    --------------------------------------

    This module defines custom `url_map` `converters`.
"""

import re
from werkzeug.routing import BaseConverter, ValidationError
from werkzeug.utils import cached_property


class DepositionConverter(BaseConverter):
    """Matches one of the items provided.  Items can either be Python
    identifiers or strings::

        Rule('/<depositions:page_name>')

    :param map: the :class:`Map`.
    :param items: this function accepts the possible items as positional
                  arguments.
    """

    def __init__(self, map):
        BaseConverter.__init__(self, map)

    @cached_property
    def regex(self):
        return '[^/]{1,}'
        #items = [lambda x: '"%s"' % x, DepositionType.keys()]
        #return '(?:%s)' % '|'.join([re.escape(x) for x in items])

    def to_python(self, value):
        try:
            #FIXME there is a problem with the first request when
            # `match_request` is call ouside application context.
            from .models import DepositionType
            keys = DepositionType.keys()
        except:
            keys = []
        if not value in keys:
            raise ValidationError()
        return value

    def to_url(self, value):
        return value


def setup_app(app):
    """Installs 'depositions' url_map converter."""

    app.url_map.converters['depositions'] = DepositionConverter
    return app
