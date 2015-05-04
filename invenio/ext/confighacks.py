# -*- coding: utf-8 -*-
# This file is part of Invenio.
# Copyright (C) 2012, 2013, 2014, 2015 CERN.
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

"""This module fixes problems with missing ``invenio.config`` module."""

import os

import sys

import warnings

from invenio.utils.deprecation import RemovedInInvenio23Warning

from six import iteritems


def get_relative_url(url):
    """Return the relative URL from a URL.

     For example:::

        'http://web.net' -> ''
        'http://web.net/' -> ''
        'http://web.net/1222' -> '/1222'
        'http://web.net/wsadas/asd' -> '/wsadas/asd'

    It will never return a trailing "/".

    :param url: A url to transform
    :type url: str

    :return: relative URL
    """
    # remove any protocol info before
    stripped_site_url = url.replace("://", "")
    baseurl = "/" + "/".join(stripped_site_url.split("/")[1:])

    # remove any trailing slash ("/")
    if baseurl[-1] == "/":
        return baseurl[:-1]
    else:
        return baseurl


def setup_app(app):
    """The extension wraps application configs.

    This extension wraps application configs and installs it as python module
    to ``invenio.config``.
    As a next step it sets an attribute ``config`` to ``invenio`` module
    to enable import statment `from invenio import config`.
    """
    # STEP 0: Special treatment of base URL, adding CFG_BASE_URL.
    CFG_BASE_URL = get_relative_url(app.config.get("CFG_SITE_URL"))
    app.config['CFG_BASE_URL'] = CFG_BASE_URL

    # STEP 1: create simple :class:`.Wrapper`.
    class Wrapper(object):

        """Wrapper."""

        def __init__(self, wrapped):
            """Init."""
            self.wrapped = wrapped

        def __getattr__(self, name):
            """Get attr."""
            # Perform custom logic here
            if name == '__file__':
                return __file__
            elif name == '__path__':
                return os.path.dirname(__file__)
            try:
                from invenio.base.helpers import utf8ifier
                warnings.warn(
                    "Usage of invenio.config.{0} is deprecated".format(name),
                    RemovedInInvenio23Warning
                )
                return utf8ifier(self.wrapped[name])
            except Exception:
                pass
                # import traceback
                # traceback.print_stack()

    # STEP 2: wrap application config and sets it as `invenio.config` module.
    sys.modules['invenio.config'] = Wrapper(app.config)
    sys.modules['invenio.dbquery_config'] = Wrapper(dict(
        (k, v) for (k, v) in iteritems(app.config)
        if k.startswith('CFG_DATABASE')))

    # STEP 3: enable `from invenio import config` by setting an attribute.
    import invenio
    setattr(invenio, 'config', Wrapper(app.config))

    return app
