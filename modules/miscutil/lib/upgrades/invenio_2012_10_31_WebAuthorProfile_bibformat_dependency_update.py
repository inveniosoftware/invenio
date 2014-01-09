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

import warnings
from invenio.dbquery import run_sql
from invenio.textutils import wait_for_user

depends_on = ['invenio_release_1_1_0']

def info():
    return "New hidden format added to serve as helper in generating WebAuthorProfile pages"

def do_upgrade():
    """ Implement your upgrades here  """
    present = run_sql("select * from format where code='wapdat'")
    if not present:
        run_sql("INSERT INTO format (name,code,description,content_type,visibility) VALUES ('WebAuthorProfile data helper','wapdat', 'cPickled dicts', 'text', 0)")


def estimate():
    """  Estimate running time of upgrade in seconds (optional). """
    return 1

def pre_upgrade():
    """  Run pre-upgrade checks (optional). """
    # Example of raising errors:
    # raise RuntimeError("Description of error 1", "Description of error 2")

def post_upgrade():
    """  Run post-upgrade checks (optional). """
    # Example of issuing warnings:
    # warnings.warn("A continuable error occurred")
