# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2013, 2014 CERN.
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
    invenio.modules.workflows
    -------------------------

    This module provides an interface for other modules (clients) to run
    fully customized workflows from anywhere in Invenio.

    These workflows can run synchronously or asynchronously using external
    task queues like Celery or Redis Queue (see all functions with "_delayed"
    suffix). A workflow can also be run without using task queues, directly
    in the Python process.

    Take a look at the sample workflows and tasks for inspiration on how
    to create new workflows.

    See the API on how to start workflows.

    (Documentation work-in-progress).
"""
