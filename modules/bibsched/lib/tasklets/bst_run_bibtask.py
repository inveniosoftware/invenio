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

"""Invenio Bibliographic Tasklet.

Allows a task to immediately run another task after it.
"""

from invenio.bibtask import task_low_level_submission

def bst_run_bibtask(taskname, user, **args):
    """
    Initiate a bibsched task.

    @param taskname: name of the task to run
    @type taskname: string

    @param user: the user to run the task under.
    @type user: string
    """
    arglist = []
    # Transform dict to list: {'a': 0, 'b': 1} -> ['a', 0, 'b', 1]
    for name, value in args.items():
        if len(name) == 1:
            name = '-' + name
        else:
            name = '--' + name
        arglist.append(name)
        if value:
            arglist.append(value)
    task_low_level_submission(taskname, user, *tuple(arglist))
