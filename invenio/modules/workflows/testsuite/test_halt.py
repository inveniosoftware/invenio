# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2013 CERN.
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

"""Unit tests for workflows views."""

from __future__ import absolute_import

from invenio.testsuite import InvenioTestCase, make_test_suite, \
    run_test_suite
import logging


class WorkflowTestBranch(InvenioTestCase):
    def test_halt(self):
        from invenio.modules.workflows.loader import workflows
        from invenio.modules.workflows.api import start
        from invenio.modules.workflows.engine import WorkflowStatus
        from invenio.modules.workflows.models import (BibWorkflowObjectLog,
                                                      ObjectVersion)

        halt_engine = lambda obj, eng: eng.halt("Test")

        class HaltTest(object):
            workflow = [halt_engine]

        workflows['halttest'] = HaltTest

        data = [{'somekey', 'somevalue'}]
        eng = start('halttest', data)
        idx, obj = list(eng.getObjects())[0]

        assert obj.version == ObjectVersion.HALTED
        assert eng.status == WorkflowStatus.FINISHED
        assert BibWorkflowObjectLog.get(
            id_object=obj.id, log_type=logging.ERROR).count() == 0

    def test_halt_in_branch(self):
        from workflow.patterns import IF_ELSE
        from invenio.modules.workflows.loader import workflows
        from invenio.modules.workflows.api import start
        from invenio.modules.workflows.engine import WorkflowStatus
        from invenio.modules.workflows.models import (BibWorkflowObjectLog,
                                                      ObjectVersion)
        always_true = lambda obj, eng: True
        halt_engine = lambda obj, eng: eng.halt("Test")

        class BranchTest(object):
            workflow = [
                IF_ELSE(always_true, [halt_engine], [halt_engine])
            ]

        workflows['branchtest'] = BranchTest

        data = [{'somekey', 'somevalue'}, ]
        eng = start('branchtest', data)
        idx, obj = list(eng.getObjects())[0]

        assert obj.version == ObjectVersion.HALTED
        assert eng.status == WorkflowStatus.FINISHED
        assert BibWorkflowObjectLog.get(
            id_object=obj.id, log_type=logging.ERROR).count() == 0


TEST_SUITE = make_test_suite(WorkflowTestBranch)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
