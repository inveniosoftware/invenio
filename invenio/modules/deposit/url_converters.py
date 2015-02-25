# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013, 2014 CERN.
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
from werkzeug.routing import BaseConverter


def converter_factory(items):
    class DepositionConverter(BaseConverter):
        """Matches one of the items provided.  Items can either be Python
        identifiers or strings::

            Rule('/<depositions:page_name>')

        :param map: the :class:`Map`.
        :param items: this function accepts the possible items as positional
                      arguments.
        """

        def __init__(self, url_map):
            BaseConverter.__init__(self, url_map)
            self.regex = '(?:%s)' % '|'.join([re.escape(x) for x in items])

    return DepositionConverter


def update_converter(app):
    """ Update URL map  converter based on registered deposition types """
    from .registry import deposit_types
    app.url_map.converters['depositions'] = converter_factory(
        deposit_types.mapping().keys()
    )


def refresh_url_map(app):
    """
    Refresh the applications URL map

    Call this if you manually registered a deposition type outside of the
    configuration variable DEPOSIT_TYPES.
    """
    update_converter(app)
    for rule in app.url_map.iter_rules():
        if rule.endpoint.startswith('webdeposit.'):
            rule.refresh()


def setup_app(app):
    """Installs 'depositions' url_map converter."""
    from .config import DEPOSIT_TYPES, DEPOSIT_DEFAULT_TYPE
    app.config.setdefault('DEPOSIT_TYPES', DEPOSIT_TYPES)
    app.config.setdefault('DEPOSIT_DEFAULT_TYPE', DEPOSIT_DEFAULT_TYPE)

    with app.app_context():
        update_converter(app)
    return app
