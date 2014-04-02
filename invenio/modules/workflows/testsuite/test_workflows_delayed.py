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



from invenio.testsuite import (InvenioTestCase,
                               make_test_suite,
                               run_test_suite,)


class WorkflowDelayedTest(InvenioTestCase):
    def tearDown(self):
        """ Clean up created objects """
        from invenio.modules.workflows.utils import tearDown as mtearDown
        mtearDown(self)

    def test_workflow_delay(self):
        from invenio.modules.workflows.models import BibWorkflowObject
        from invenio.modules.workflows.api import start_delayed, continue_oid_delayed, start_by_wid_delayed
        from invenio.modules.workflows.engine import WorkflowStatus

        test_objectb = BibWorkflowObject()
        test_objectb.set_data(20)
        test_objectb.save()
        from invenio.modules.workflows.worker_result import uui_to_workflow

        asyncr = start_delayed('test_workflow', [test_objectb], module_name="unit_tests")
        engineb = asyncr.get(uui_to_workflow)

        self.assertEqual(test_objectb.get_data(), 38)

        asyncr = start_by_wid_delayed(engineb.uuid)
        asyncr.get()
        self.assertEqual(test_objectb.get_data(), 38)
        test_objecte = BibWorkflowObject()
        test_objecte.set_data(2)
        test_objecte.save()
        asyncr = start_delayed('test_workflow', [test_objecte], module_name="unit_tests")
        engineb = asyncr.get(uui_to_workflow)
        while engineb.status != WorkflowStatus.COMPLETED:
            asyncr = continue_oid_delayed(test_objecte.id)
            engineb = asyncr.get()
        self.assertEqual(engineb.status, WorkflowStatus.COMPLETED)
        self.assertEqual(test_objecte.get_data(), 20)

    def test_workflows_tasks_chained(self):
        from invenio.modules.workflows.models import BibWorkflowObject
        from invenio.modules.workflows.api import start_delayed

        test_object = BibWorkflowObject()
        test_object.set_data(10)
        test_object.save()
        async = start_delayed("test_workflow_workflows", [test_object], module_name="unit_tests")
        engine = async.get()
        from invenio.modules.workflows.engine import WorkflowStatus

        self.assertEqual(engine.get_extra_data()["_nb_workflow_finish"], 21)
        self.assertEqual(engine.get_extra_data()["_nb_workflow_failed"], 0)
        self.assertEqual(engine.status, WorkflowStatus.COMPLETED)

    def test_dirty_worker(self):
        from invenio.modules.workflows.workers.worker_celery import celery_run, celery_restart, celery_continue
        from invenio.modules.workflows.utils import BibWorkflowObjectIdContainer
        from invenio.modules.workflows.models import BibWorkflowObject

        test_objectb = BibWorkflowObject()
        test_objectb.set_data(22)
        test_objectb.save()
        data = BibWorkflowObjectIdContainer(test_objectb).to_dict()
        celery_run('test_workflow', [data], module_name="unit_tests")
        self.assertEqual(test_objectb.get_data(), 40)
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
        self.assertEqual(test_object.get_data(), 40)
        self.assertEqual(test_objectc.get_data(), 40)

        test_object = BibWorkflowObject()
        test_object.save()
        test_object.set_data(0)
        from invenio.modules.workflows.worker_result import uui_to_workflow

        engine = uui_to_workflow(celery_run('test_workflow_logic', [test_object], module_name="unit_tests"))
        self.assertEqual(test_object.get_data(), 5)
        self.assertEqual(test_object.get_extra_data()["test"], "lt9")
        celery_restart(engine.uuid)
        self.assertEqual(test_object.get_data(), 5)
        self.assertEqual(test_object.get_extra_data()["test"], "lt9")
        celery_continue(test_object.id, "continue_next")
        self.assertEqual(test_object.get_data(), 6)
        self.assertEqual(test_object.get_extra_data()["test"], "lt9")
        celery_continue(test_object.id, "continue_next")
        self.assertEqual(test_object.get_data(), 9)
        self.assertEqual(test_object.get_extra_data()["test"], "gte9")
        celery_continue(test_object.id, "continue_next")
        self.assertEqual(test_object.get_data(), 15)
        self.assertEqual(test_object.get_extra_data()["test"], "gte9")
        engine = uui_to_workflow(celery_continue(test_object.id, "continue_next", module_name="unit_tests"))
        from invenio.modules.workflows.engine import WorkflowStatus

        while engine.status != WorkflowStatus.COMPLETED:
            engine = uui_to_workflow(celery_continue(test_object.id, "continue_next"))
        self.assertEqual(engine.status, WorkflowStatus.COMPLETED)

    def test_workflows_tasks(self):
        from invenio.modules.workflows.models import BibWorkflowObject
        from invenio.modules.workflows.api import start

        test_object = BibWorkflowObject()
        test_object.save()
        test_object.set_data(10)
        engine = start("test_workflow_workflows", [test_object], module_name="unit_tests")
        from invenio.modules.workflows.engine import WorkflowStatus

        self.assertEqual(engine.get_extra_data()["_nb_workflow_failed"], 0)
        self.assertEqual(engine.status, WorkflowStatus.COMPLETED)
        self.assertEqual(test_object.get_extra_data()["_tasks_results"]["_workflows_reviews"][0].result["failed"], 0)
        self.assertEqual(test_object.get_extra_data()["nbworkflowrunning"], 4)
        self.assertEqual(engine.get_extra_data()["_nb_workflow_finish"], 21)


TEST_SUITE = make_test_suite(WorkflowDelayedTest,
                             )

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)

