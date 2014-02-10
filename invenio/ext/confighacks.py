# -*- coding: utf-8 -*-
## This file is part of Invenio.
## Copyright (C) 2012, 2013 CERN.
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
"""
    invenio.ext.confighacks
    -----------------------

    This module fixes problems with missing ``invenio.config`` module.
"""
import os
import sys


def setup_app(app):
    """
    This extension wraps application configs and installs it as python module
    to ``invenio.config``. As a next step it sets an attribute ``config`` to
    ``invenio`` module to enable import statment `from invenio import config`.
    """
    # STEP 1: create simple :class:`.Wrapper`.
    class Wrapper(object):
        def __init__(self, wrapped):
            self.wrapped = wrapped

        def __getattr__(self, name):
            # Perform custom logic here
            if name == '__file__':
                return __file__
            elif name == '__path__':
                return os.path.dirname(__file__)
            try:
                return self.wrapped[name]
            except:
                pass
                #import traceback
                #traceback.print_stack()

    # STEP 2: wrap application config and sets it as `invenio.config` module.
    sys.modules['invenio.config'] = Wrapper(app.config)
    sys.modules['invenio.dbquery_config'] = Wrapper(dict(
        (k, v) for (k, v) in app.config.iteritems()
        if k.startswith('CFG_DATABASE')))

    # STEP 3: enable `from invenio import config` by setting an attribute.
    import invenio
    setattr(invenio, 'config', Wrapper(app.config))

    return app
