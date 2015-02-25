# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014 CERN.
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


""" Test for workflow not fitting in other categories."""

from invenio.testsuite import make_test_suite, run_test_suite
from .test_workflows import WorkflowTasksTestCase


class WorkflowOthers(WorkflowTasksTestCase):

    """Class to test the other tasks and workflows."""

    def setUp(self):
        """Setup tests."""
        self.create_registries()

    def tearDown(self):
        """ Clean up created objects."""
        from invenio.modules.workflows.models import Workflow
        Workflow.get(Workflow.module_name == "unit_tests").delete()
        self.cleanup_registries()

    def test_result_abstraction(self):
        """Test abastraction layer for celery worker."""
        from invenio.ext.sqlalchemy import db
        from ..utils import BibWorkflowObjectIdContainer
        from ..models import BibWorkflowObject
        from ..worker_result import AsynchronousResultWrapper

        bwoic = BibWorkflowObjectIdContainer(None)
        self.assertEqual(None, bwoic.get_object())
        test_object = BibWorkflowObject()
        test_object.set_data(45)
        test_object.save()
        bwoic2 = BibWorkflowObjectIdContainer(test_object)
        self.assertEqual(bwoic2.get_object().id, test_object.id)
        result = bwoic2.to_dict()
        self.assertEqual(bwoic2.from_dict(result).id, test_object.id)
        db.session.delete(test_object)
        try:
            AsynchronousResultWrapper(None)
        except Exception as e:
            self.assertTrue(isinstance(e, TypeError))

    def test_acces_to_undefineworkflow(self):
        """Test of access to undefined workflow."""
        from invenio.modules.workflows.api import start
        try:
            start("@thisisnotatrueworkflow@", ["my_false_data"],
                  random_kay_args="value")
        except Exception as e:
            from invenio.modules.workflows.errors import WorkflowDefinitionError
            self.assertTrue(isinstance(e, WorkflowDefinitionError))

    def test_workflows_exceptions(self):
        """Test for workflows exception."""
        from invenio.modules.workflows.errors import WorkflowError
        from invenio.modules.workflows.api import start

        try:
            start("test_workflow_error", [2],
                  module_name="unit_tests")
        except Exception as e:
            self.assertTrue(isinstance(e, WorkflowError))
            self.assertTrue("ZeroDivisionError" in e.message)
            self.assertTrue("call_a()" in e.message)
            self.assertTrue("call_b()" in e.message)
            self.assertTrue("call_c()" in e.message)


TEST_SUITE = make_test_suite(WorkflowOthers)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
