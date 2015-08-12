# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014, 2015 CERN.
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

"""Contain signals emitted from workflows module."""

from flask.signals import Namespace
_signals = Namespace()

workflow_halted = _signals.signal('workflow_halted')
"""
This signal is sent when a workflow engine's halt function is called.
Sender is the BibWorkflowObject that was running before the workflow
was halted.
"""

workflow_started = _signals.signal('workflow_started')
"""
This signal is sent when a workflow is started.
Sender is the workflow engine object running the workflow.
"""

workflow_finished = _signals.signal('workflow_finished')
"""
This signal is sent when a workflow is finished.
Sender is the workflow engine object running the workflow.
"""

workflow_error = _signals.signal('workflow_error')
"""
This signal is sent when a workflow object gets an error.
Sender is the BibWorkflowObject that was running before the workflow
got the error.
"""
