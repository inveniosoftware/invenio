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

"""Test for delayed workflows."""

from invenio.testsuite import make_test_suite, run_test_suite
from ...workflows.testsuite.test_workflows import WorkflowTasksTestCase
from invenio.celery import celery


class WorkflowDelayedTest(WorkflowTasksTestCase):

    """Class to test the delayed workflows."""

    def setUp(self):
        """ Setup tests."""
        self.create_registries()
        celery.conf['CELERY_ALWAYS_EAGER'] = True

    def tearDown(self):
        """ Clean up created objects."""
        from invenio.modules.workflows.models import Workflow
        Workflow.get(Workflow.module_name == "unit_tests").delete()
        self.cleanup_registries()

    def test_workflow_delay(self):
        """Test simple delayed workflow."""
        from invenio.modules.workflows.models import BibWorkflowObject
        from invenio.modules.workflows.api import (start_delayed,
                                                   continue_oid_delayed,
                                                   start_by_wid_delayed)
        from invenio.modules.workflows.engine import WorkflowStatus

        test_objectb = BibWorkflowObject()
        test_objectb.set_data(20)
        test_objectb.save()
        from invenio.modules.workflows.worker_result import uuid_to_workflow

        asyncr = start_delayed('test_workflow', [test_objectb],
                               module_name="unit_tests")
        engineb = asyncr.get(uuid_to_workflow)

        self.assertEqual(38, test_objectb.get_data())

        asyncr = start_by_wid_delayed(engineb.uuid)
        asyncr.get(uuid_to_workflow)
        self.assertEqual(38, test_objectb.get_data())
        test_objecte = BibWorkflowObject()
        test_objecte.set_data(2)
        test_objecte.save()
        asyncr = start_delayed('test_workflow', [test_objecte],
                               module_name="unit_tests")
        engineb = asyncr.get(uuid_to_workflow)
        asyncr = continue_oid_delayed(test_objecte.id)

        engineb = asyncr.get(uuid_to_workflow)
        self.assertEqual(WorkflowStatus.COMPLETED, engineb.status)
        self.assertEqual(20, test_objecte.get_data())

    def test_workflows_tasks_chained(self):
        """Test delayed workflows in delayed workflow."""
        from invenio.modules.workflows.models import BibWorkflowObject
        from invenio.modules.workflows.api import start_delayed
        from invenio.modules.workflows.worker_result import uuid_to_workflow

        test_object = BibWorkflowObject()
        test_object.set_data(22)
        test_object.save()
        async = start_delayed("test_workflow_workflows", [test_object],
                              module_name="unit_tests")
        engine = async.get(uuid_to_workflow)
        from invenio.modules.workflows.engine import WorkflowStatus

        self.assertEqual(21, engine.get_extra_data()["_nb_workflow_finish"])
        self.assertEqual(0, engine.get_extra_data()["_nb_workflow_failed"])
        self.assertEqual(WorkflowStatus.COMPLETED, engine.status)

    def test_dirty_worker(self):
        """Deep test of celery worker."""
        from ..workers.worker_celery import (celery_run, celery_restart,
                                             celery_continue)
        from invenio.modules.workflows.utils import BibWorkflowObjectIdContainer
        from invenio.modules.workflows.models import (BibWorkflowObject,
                                                      get_default_extra_data)

        test_objectb = BibWorkflowObject()
        test_objectb.set_data(22)
        test_objectb.save()
        data = BibWorkflowObjectIdContainer(test_objectb).to_dict()
        celery_run('test_workflow', [data], module_name="unit_tests")
        self.assertEqual(40, test_objectb.get_data())
        test_object = BibWorkflowObject()
        test_object.set_data(22)
        test_object.save()
        test_objectc = BibWorkflowObject()
        test_objectc.set_data(22)
        test_objectc.save()
        data = [test_object, test_objectc]
        for i in range(0, len(data)):
            if isinstance(data[i], BibWorkflowObject):
                data[i] = BibWorkflowObjectIdContainer(data[i]).to_dict()
        celery_run('test_workflow', data, module_name="unit_tests")
        self.assertEqual(40, test_object.get_data())
        self.assertEqual(40, test_objectc.get_data())

        test_object = BibWorkflowObject()
        test_object.save()
        test_object.set_data(0)
        from invenio.modules.workflows.worker_result import uuid_to_workflow

        engine = uuid_to_workflow(
            celery_run('test_workflow_logic', [test_object],
                       module_name="unit_tests"))
        self.assertEqual(5, test_object.get_data())
        self.assertEqual("lt9", test_object.get_extra_data()["test"])

        engine._extra_data = get_default_extra_data()  # reset iterators
        celery_restart(engine.uuid)
        self.assertEqual(5, test_object.get_data())
        self.assertEqual("lt9", test_object.get_extra_data()["test"])

        celery_continue(test_object.id, "continue_next")
        self.assertEqual(6, test_object.get_data())
        self.assertEqual("lt9", test_object.get_extra_data()["test"])

        celery_continue(test_object.id, "continue_next")
        self.assertEqual(9, test_object.get_data())
        self.assertEqual("gte9", test_object.get_extra_data()["test"])

        celery_continue(test_object.id, "continue_next")
        self.assertEqual(15, test_object.get_data())
        self.assertEqual("gte9", test_object.get_extra_data()["test"])
        engine = uuid_to_workflow(
            celery_continue(test_object.id, "continue_next",
                            module_name="unit_tests"))
        from invenio.modules.workflows.engine import WorkflowStatus

        self.assertEqual(WorkflowStatus.COMPLETED, engine.status)

    def test_workflows_tasks(self):
        """Test delayed workflows in non delayed one."""
        from invenio.modules.workflows.models import BibWorkflowObject
        from invenio.modules.workflows.api import start

        test_object = BibWorkflowObject()
        test_object.save()
        test_object.set_data(22)
        engine = start("test_workflow_workflows", [test_object],
                       module_name="unit_tests")
        from invenio.modules.workflows.engine import WorkflowStatus

        self.assertEqual(0, engine.get_extra_data()["_nb_workflow_failed"])
        self.assertEqual(WorkflowStatus.COMPLETED, engine.status)
        self.assertEqual(0, test_object.get_tasks_results()[
                         "review_workflow"][0]["result"]["failed"])
        self.assertEqual(4, test_object.get_extra_data()["nbworkflowrunning"])
        self.assertEqual(21, engine.get_extra_data()["_nb_workflow_finish"])


TEST_SUITE = make_test_suite(WorkflowDelayedTest)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
