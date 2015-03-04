# -*- coding: utf-8; -*-
#
# This file is part of Invenio.
# Copyright (C) 2013, 2015 CERN.
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
   "bibcheck" is used to check a set of records against a
   configurable set of rules. A rule consists of a query, a
   checker and an amender. The set of records that
   match the query are checked with the checker and the records
   that don't pass the test will be passed to the amender. An
   amender can try to fix the record automatically or request a
   human to fix the record.

   The checkers and amenders are loaded via a plug-in system, so
   it's easy to add new checkers or amenders.
"""

from invenio.base.factory import with_app_context


@with_app_context()
def main():
    from invenio.legacy.bibcheck.task import main as cli_main
    return cli_main()
