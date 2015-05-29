# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013, 2014, 2015 CERN.
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

"""Unit tests for workflows."""

from __future__ import absolute_import

import logging

import random

import time

from flask_registry import ImportPathRegistry
from functools import partial

from workflow.engine_db import WorkflowStatus
from workflow.errors import WorkflowError, WorkflowObjectStatusError

from invenio.testsuite import InvenioTestCase, make_test_suite, run_test_suite
from invenio.base.wrappers import lazy_import

ObjectStatus = lazy_import("invenio.modules.workflows.models.ObjectStatus")
DbWorkflowObject = lazy_import("invenio.modules.workflows.models.DbWorkflowObject")
Workflow = lazy_import("invenio.modules.workflows.models.Workflow")
DbWorkflowObjectLog = lazy_import("invenio.modules.workflows.models.DbWorkflowObjectLog")

from ..registry import WorkflowsRegistry

TEST_PACKAGES = [
    'invenio.modules.*',
    'invenio.modules.workflows.testsuite',
]

start = lazy_import("invenio.modules.workflows.api.start")
start = partial(start, module_name='unit_tests')


class WorkflowTasksTestCase(InvenioTestCase):

    """ Workflow class for testing."""

    def create_registries(self):
        """Create registries for testing."""
        self.app.extensions['registry']['workflows.tests'] = \
            ImportPathRegistry(initial=TEST_PACKAGES)
        self.app.extensions['registry']['workflows'] = \
            WorkflowsRegistry(
                'workflows', app=self.app, registry_namespace='workflows.tests'
            )
        self.app.extensions['registry']['workflows.actions'] = \
            WorkflowsRegistry(
                'actions', app=self.app, registry_namespace='workflows.tests'
            )

    def cleanup_registries(self):
        """Clean registries for testing."""
        del self.app.extensions['registry']['workflows.tests']
        del self.app.extensions['registry']['workflows']
        del self.app.extensions['registry']['workflows.actions']


class WorkflowTasksTestAPI(WorkflowTasksTestCase):

    """ Test basic workflow API."""

    def setUp(self):
        """Setup tests."""
        self.create_registries()
        self.id_workflows = []
        self.recxml = """<?xml version="1.0" encoding="UTF-8"?>
<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd">
<responseDate>2013-04-03T13:56:49Z</responseDate>
<request verb="ListRecords" from="2013-03-25" metadataPrefix="arXiv" set="physics:astro-ph">http://export.arxiv.org/oai2</request>
<ListRecords>
<record>
<header>
<identifier>oai:arXiv.org:0801.3931</identifier>
<datestamp>2013-03-26</datestamp>
<setSpec>physics:astro-ph</setSpec>
</header>
<metadata>
<arXiv xmlns="http://arxiv.org/OAI/arXiv/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://arxiv.org/OAI/arXiv/ http://arxiv.org/OAI/arXiv.xsd">
<id>0801.3931</id><created>2008-01-25</created><authors><author><keyname>Manos</keyname><forenames>T.</forenames></author><author><keyname>Athanassoula</keyname><forenames>E.</forenames></author></authors><title>Dynamical study of 2D and 3D barred galaxy models</title><categories>astro-ph</categories><comments>8 pages, 3 figures, to appear in the proceedings of the international
conference &quot;Chaos in Astronomy&quot;, Athens, Greece (talk contribution)</comments><journal-ref>Chaos in Astronomy Astrophysics and Space Science Proceedings
2009, pp 115-122</journal-ref><doi>10.1007/978-3-540-75826-6_11</doi><abstract> We study the dynamics of 2D and 3D barred galaxy analytical models, focusing
on the distinction between regular and chaotic orbits with the help of the
Smaller ALigment Index (SALI), a very powerful tool for this kind of problems.
We present briefly the method and we calculate the fraction of chaotic and
regular orbits in several cases. In the 2D model, taking initial conditions on
a Poincar\'{e} $(y,p_y)$ surface of section, we determine the fraction of
regular and chaotic orbits. In the 3D model, choosing initial conditions on a
cartesian grid in a region of the $(x, z, p_y)$ space, which in coordinate
space covers the inner disc, we find how the fraction of regular orbits changes
as a function of the Jacobi constant. Finally, we outline that regions near the
$(x,y)$ plane are populated mainly by regular orbits. The same is true for
regions that lie either near to the galactic center, or at larger relatively
distances from it.
</abstract></arXiv>
</metadata>
</record>
</ListRecords>
</OAI-PMH>
"""

    def tearDown(self):
        """ Clean up created objects."""
        self.delete_objects(
            Workflow.get(Workflow.module_name == "unit_tests").all())
        self.cleanup_registries()

    def test_halt(self):
        """Test halt task."""
        from invenio.modules.workflows.registry import workflows

        def halt_engine(obj, eng):
            return eng.halt("Test")

        class HaltTest(object):
            workflow = [halt_engine]

        workflows['halttest'] = HaltTest

        data = [set(('somekey', 'somevalue'))]
        eng = start('halttest', data)
        obj = list(eng.objects)[0]

        self.assertEqual(obj.known_statuses.WAITING, obj.status)
        self.assertEqual(WorkflowStatus.HALTED, eng.status)
        self.assertEqual(0, DbWorkflowObjectLog.get(
            id_object=obj.id, log_type=logging.ERROR).count())

    def test_halt_in_branch(self):
        """Test halt task when in conditionnal branch."""
        from workflow.patterns import IF_ELSE
        from invenio.modules.workflows.registry import workflows

        def always_true(obj, eng):
            return True

        def halt_engine(obj, eng):
            return eng.halt("Test")

        class BranchTest(object):
            workflow = [
                IF_ELSE(always_true, [halt_engine], [halt_engine])
            ]

        workflows['branchtest'] = BranchTest

        data = [set(('somekey', 'somevalue'))]
        eng = start('branchtest', data)
        obj = list(eng.objects)[0]

        self.assertEqual(obj.known_statuses.WAITING, obj.status)
        self.assertEqual(WorkflowStatus.HALTED, eng.status)
        self.assertEqual(0, DbWorkflowObjectLog.get(
            id_object=obj.id, log_type=logging.ERROR).count())

    def test_object_creation_complete(self):
        """
        Test status of object before/after workflow.

        When created before calling API, with "high" test-data that will
        make the workflow complete.
        """
        from workflow.engine_db import WorkflowStatus

        test_object = DbWorkflowObject()
        test_object.set_data(20)
        test_object.save()

        self.assertEqual(test_object.known_statuses.INITIAL, test_object.status)
        self.assertEqual(None, test_object.id_parent)
        self.assertEqual(20, test_object.get_data())

        engine = start('test_workflow', [test_object],
                       module_name="unit_tests")

        self.assertEqual(38, test_object.get_data())
        self.assertEqual(None, test_object.id_parent)
        self.assertEqual(WorkflowStatus.COMPLETED, engine.status)
        self.assertEqual(test_object.known_statuses.COMPLETED, test_object.status)

    def test_object_creation_halt(self):
        """Test status of object before/after workflow.

        When created before calling API, with "low" test-data that will
        make the workflow halt.
        """
        from workflow.engine_db import WorkflowStatus

        test_object = DbWorkflowObject()
        test_object.set_data(2)
        test_object.save()

        self.assertEqual(test_object.known_statuses.INITIAL, test_object.status)
        self.assertEqual(None, test_object.id_parent)
        self.assertEqual(2, test_object.get_data())

        engine = start('test_workflow', [test_object],
                       module_name="unit_tests")

        self.assertEqual(2, test_object.get_data())
        self.assertEqual(test_object.known_statuses.WAITING, test_object.status)
        self.assertEqual(WorkflowStatus.HALTED, engine.status)

    def test_workflow_engine_instantiation(self):
        """Check the proper init of the Workflow and BibWorkflowEngine."""
        from invenio.modules.workflows.engine import BibWorkflowEngine
        from uuid import uuid1 as new_uuid

        test_workflow = Workflow(name='test_workflow', uuid=new_uuid(),
                                 id_user=0, module_name="Unknown", )
        test_workflow_engine = BibWorkflowEngine(test_workflow)
        self.assertEqual(test_workflow.name, test_workflow_engine.name)

    # THIS ALSO TESTS engine.objects
    def test_workflow_restarts(self):
        """Check if all is well when restarting a workflow several times."""
        from invenio.modules.workflows.api import continue_oid

        test_object = DbWorkflowObject()

        random.seed(time.time())
        tries = 15

        test_object.set_data(tries)
        test_object.save()

        engine = start('test_workflow_hardcore', [test_object])
        for i in range(0, tries):
            self.assertEqual(engine.status, WorkflowStatus.HALTED)
            for my_object_b in engine.objects:
                engine = continue_oid(my_object_b.id, "restart_task")
        self.assertEqual(0, test_object.get_data())
        self.assertEqual(test_object.known_statuses.COMPLETED, test_object.status)
        self.assertEqual(WorkflowStatus.COMPLETED, engine.status)

    def test_workflow_object_creation(self):
        """Test to see if the right snapshots or object versions are created."""
        initial_data = 22
        final_data = 40

        test_object = DbWorkflowObject()
        test_object.set_data(initial_data)
        test_object.save()

        workflow = start(workflow_name="test_workflow",
                         data=[test_object])

        # Get parent object of the workflow we just ran
        initial_object = DbWorkflowObject.query.filter(DbWorkflowObject.id_parent == test_object.id).one()
        all_objects = DbWorkflowObject.query.filter(
            DbWorkflowObject.id_workflow == workflow.uuid
        ).order_by(DbWorkflowObject.id).all()

        # There should only be 2 objects (initial, final)
        self.assertEqual(2, len(all_objects))
        self.assertEqual(test_object.id, initial_object.id_parent)
        self.assertEqual(initial_object.known_statuses.INITIAL, initial_object.status)
        self.assertEqual(initial_data, initial_object.get_data())
        self.assertEqual(final_data, test_object.get_data())
        self.assertEqual(initial_object.known_statuses.COMPLETED, test_object.status)

    def test_workflow_object_creation_simple(self):
        """Test to see if the right snapshots or object versions are created."""
        initial_data = 22
        final_data = 40

        workflow = start(workflow_name="test_workflow",
                         data=[initial_data])

        # Get parent object of the workflow we just ran
        initial_object = DbWorkflowObject.query.filter(
            DbWorkflowObject.id_workflow == workflow.uuid,
            DbWorkflowObject.id_parent == None).first()  # noqa E711
        test_object = DbWorkflowObject.query.filter(
            DbWorkflowObject.id_workflow == workflow.uuid,
            DbWorkflowObject.id_parent == initial_object.id).first()
        all_objects = DbWorkflowObject.query.filter(
            DbWorkflowObject.id_workflow == workflow.uuid
        ).order_by(DbWorkflowObject.id).all()

        # There should only be 2 objects (initial, final)
        self.assertEqual(2, len(all_objects))
        self.assertEqual(test_object.id_parent, initial_object.id)
        self.assertEqual(initial_object.known_statuses.COMPLETED, initial_object.status)
        self.assertEqual(final_data, initial_object.get_data())
        self.assertEqual(initial_data, test_object.get_data())
        self.assertEqual(initial_object.known_statuses.INITIAL, test_object.status)

    def test_workflow_complex_run(self):
        """Test running workflow with several data objects."""
        test_data = [1, 20]
        final_data = [1, 38]

        workflow = start(workflow_name="test_workflow",
                         data=test_data)

        # Get parent objects of the workflow we just ran
        objects = DbWorkflowObject.query.filter(
            DbWorkflowObject.id_workflow == workflow.uuid,
            DbWorkflowObject.id_parent == None  # noqa E711
        ).order_by(DbWorkflowObject.id).all()

        # Let's check that we found anything.
        # There should only be two objects
        self.assertEqual(2, len(objects))

        all_objects = DbWorkflowObject.query.filter(
            DbWorkflowObject.id_workflow == workflow.uuid
        ).order_by(DbWorkflowObject.id).all()

        self.assertEqual(4, len(all_objects))

        for obj in objects:
            # The child object should have the final or halted status
            # FIXME: Exactly what is not deterministic about this workflow?
            obj0 = obj.child_objects[0]
            self.assertTrue(obj0.status in (obj0.known_statuses.INITIAL,
                                            obj0.known_statuses.HALTED))
            # Making sure the final data is correct
            self.assertTrue(obj.get_data() in final_data)
            self.assertTrue(obj0.get_data() in test_data)

    def test_workflow_marcxml(self):
        """Test runnning a record ingestion workflow with a action step."""
        initial_data = self.recxml
        workflow = start(workflow_name="marcxml_workflow", data=[initial_data])

        # Get objects of the workflow we just ran
        objects = DbWorkflowObject.query.filter(
            DbWorkflowObject.id_workflow == workflow.uuid,
            DbWorkflowObject.id_parent == None  # noqa E711
        ).order_by(DbWorkflowObject.id).all()

        self._check_workflow_execution(objects, initial_data)

        all_objects = DbWorkflowObject.query.filter(
            DbWorkflowObject.id_workflow == workflow.uuid
        ).order_by(DbWorkflowObject.id).all()

        self.assertEqual(2, len(all_objects))

        self.assertEqual(WorkflowStatus.HALTED, workflow.status)

        current = DbWorkflowObject.query.filter(
            DbWorkflowObject.id_workflow == workflow.uuid,
            DbWorkflowObject.status == DbWorkflowObject.known_statuses.HALTED
        ).one()

        self.assertEqual(current.get_action(), "approval")

    def test_workflow_for_halted_object(self):
        """Test workflow with continuing a halted object."""
        from invenio.modules.workflows.api import continue_oid

        current = DbWorkflowObject()
        current.set_data(self.recxml)
        current.save()

        workflow = start(workflow_name="marcxml_workflow",
                         data=[current])

        self.assertEqual(WorkflowStatus.HALTED, workflow.status)
        self.assertEqual(current.known_statuses.HALTED, current.status)

        workflow = continue_oid(current.id)
        self.assertEqual(WorkflowStatus.COMPLETED, workflow.status)
        self.assertEqual(current.known_statuses.COMPLETED, current.status)

    def test_workflow_for_finished_object(self):
        """Test starting workflow with finished object given."""
        current = DbWorkflowObject()
        current.set_data(20)
        current.save()

        workflow = start(workflow_name="test_workflow", data=[current])

        self.assertEqual(WorkflowStatus.COMPLETED, workflow.status)
        self.assertEqual(current.known_statuses.COMPLETED, current.status)
        self.assertEqual(38, current.get_data())

        previous = DbWorkflowObject.query.get(current.id)

        workflow_2 = start(workflow_name="test_workflow", data=[previous])

        self.assertEqual(WorkflowStatus.COMPLETED, workflow_2.status)
        self.assertEqual(previous.known_statuses.COMPLETED, previous.status)
        self.assertEqual(56, previous.get_data())

    def test_logging_for_workflow_objects_without_workflow(self):
        """Test run a virtual object out of a workflow for test purpose."""
        initial_data = 20
        obj_init = DbWorkflowObject(
            id_workflow=None,
            version=ObjectStatus.INITIAL)
        obj_init.set_data(initial_data)
        obj_init.save()

        err_msg = "This is an error message"
        info_msg = "This is an info message"

        obj_init.log.info(info_msg)
        obj_init.log.error("This is an error message")
        # FIXME: loglevels are simply overwritten somewhere in Celery
        # even if Celery is not being "used".
        #
        # This means loglevel.DEBUG is NOT working at the moment!
        # debug_msg = "This is a debug message"
        # obj_init.log.debug(debug_msg)
        obj_init.save()

        obj_test = DbWorkflowObjectLog.query.filter(
            DbWorkflowObjectLog.id_object == obj_init.id).all()
        messages_found = 0
        for current_obj in obj_test:
            if current_obj.message == info_msg and messages_found == 0:
                messages_found += 1
            elif current_obj.message == err_msg and messages_found == 1:
                messages_found += 1
        self.assertEqual(2, messages_found)

    def test_workflow_for_running_object(self):
        """Test workflow with running object given and watch it fail."""
        from invenio.modules.workflows.api import start_by_oids

        obj_running = DbWorkflowObject()
        obj_running.set_data(1234)
        obj_running.save(status=obj_running.known_statuses.RUNNING)

        try:
            start_by_oids('test_workflow', [obj_running.id])
        except Exception as e:
            self.assertTrue(isinstance(e, WorkflowObjectStatusError))
            obj_running.delete(e.id_object)
        obj_running.delete(obj_running)
        obj_running = DbWorkflowObject()
        obj_running.set_data(1234)
        obj_running.save(status=obj_running.known_statuses.RUNNING)
        try:
            start_by_oids('test_workflow', [obj_running.id])
        except Exception as e:
            self.assertTrue(isinstance(e, WorkflowObjectStatusError))
            obj_running.delete(e.id_object)
        obj_running.delete(obj_running)

        obj_running = DbWorkflowObject()
        obj_running.set_data(1234)
        obj_running.save(status=obj_running.known_statuses.ERROR)
        try:
            start_by_oids('test_workflow', [obj_running.id])
        except Exception as e:
            self.assertTrue(isinstance(e, WorkflowObjectStatusError))
            obj_running.delete(e.id_object)
        obj_running.delete(obj_running)

    def test_continue_execution_for_object(self):
        """Test continuing execution of workflow for object given."""
        from invenio.modules.workflows.api import continue_oid

        initial_data = 1

        # testing restarting from previous task
        init_workflow = start("test_workflow", data=[initial_data])

        obj_halted = DbWorkflowObject.query.filter(
            DbWorkflowObject.id_workflow == init_workflow.uuid,
            DbWorkflowObject.status == DbWorkflowObject.known_statuses.WAITING
        ).first()

        self.assertTrue(obj_halted)
        self.assertEqual(1, obj_halted.get_data())

        # Try to restart, we should halt again actually.
        continue_oid(oid=obj_halted.id, start_point="restart_task")

        self.assertEqual(1, obj_halted.get_data())
        self.assertEqual(obj_halted.known_statuses.WAITING, obj_halted.status)

        # We skip to next part, this should work
        continue_oid(oid=obj_halted.id)

        self.assertEqual(19, obj_halted.get_data())
        self.assertEqual(obj_halted.known_statuses.COMPLETED, obj_halted.status)

        # Let's do that last task again, shall we?
        continue_oid(oid=obj_halted.id, start_point="restart_prev")

        self.assertEqual(37, obj_halted.get_data())
        self.assertEqual(obj_halted.known_statuses.COMPLETED, obj_halted.status)

    def test_restart_workflow(self):
        """Test restarting workflow for given workflow id."""
        from invenio.modules.workflows.api import start_by_wid

        initial_data = 1

        init_workflow = start(workflow_name="test_workflow",
                              data=[initial_data])

        init_objects = DbWorkflowObject.query.filter(
            DbWorkflowObject.id_workflow == init_workflow.uuid
        ).order_by(DbWorkflowObject.id).all()
        self.assertEqual(2, len(init_objects))
        restarted_workflow = start_by_wid(wid=init_workflow.uuid)

        # We expect the same workflow to be re-started
        self.assertTrue(init_workflow.uuid == restarted_workflow.uuid)

        restarted_objects = DbWorkflowObject.query.filter(
            DbWorkflowObject.id_workflow == restarted_workflow.uuid
        ).order_by(DbWorkflowObject.id).all()
        # This time we should only have one more initial object
        self.assertEqual(2, len(restarted_objects))

        # Last object will be INITIAL
        self.assertEqual(restarted_objects[1].known_statuses.INITIAL, restarted_objects[1].status)

        self.assertEqual(restarted_objects[1].id_parent,
                         restarted_objects[0].id)

    def test_restart_failed_workflow(self):
        """Test restarting workflow for given workflow id."""
        from invenio.modules.workflows.api import start_by_oids

        initial_data = DbWorkflowObject.create_object()
        initial_data.set_data(1)
        initial_data.save()

        with self.assertRaises(WorkflowError):
            start(workflow_name="test_workflow_error", data=[initial_data])
        self.assertEqual(initial_data.status, initial_data.known_statuses.ERROR)

        restarted_workflow = start_by_oids("test_workflow",
                                           oids=[initial_data.id])
        self.assertEqual(initial_data.status, initial_data.known_statuses.WAITING)
        self.assertEqual(restarted_workflow.status, WorkflowStatus.HALTED)

    def _check_workflow_execution(self, objects, initial_data):
        """Test correct workflow execution."""
        # Let's check that we found anything. There should only be one object
        self.assertEqual(len(objects), 1)
        parent_object = objects[0]

        # The object should be the inital status
        self.assertEqual(parent_object.known_statuses.HALTED, parent_object.status)

        # The object should have the inital data
        self.assertEqual(initial_data, objects[0].child_objects[0].get_data())

        # Fetch final object which should exist
        final_object = objects[0].child_objects[0]
        self.assertTrue(final_object)


class TestWorkflowTasks(WorkflowTasksTestCase):

    """Test meant for testing the the generic tasks available."""

    def setUp(self):
        """Setup tests."""
        self.create_registries()

    def tearDown(self):
        """Clean up tests."""
        self.delete_objects(
            Workflow.get(Workflow.module_name == "unit_tests").all())
        self.cleanup_registries()

    def test_logic_tasks_restart(self):
        """Test that the logic tasks work correctly when restarted."""
        from invenio.modules.workflows.api import (start_by_wid)

        test_object = DbWorkflowObject()
        test_object.set_data(0)
        test_object.save()

        # Initial run
        workflow = start('test_workflow_logic', [test_object])

        self.assertEqual(5, test_object.get_data())
        self.assertEqual("lt9", test_object.extra_data["test"])

        # Reset before re-starting (reset Iterator data)
        workflow.reset_extra_data()

        workflow = start_by_wid(workflow.uuid)
        self.assertEqual(5, test_object.get_data())
        self.assertEqual("lt9", test_object.extra_data["test"])

    def test_logic_tasks_continue(self):
        """Test that the logic tasks work correctly when continuing."""
        from invenio.modules.workflows.api import (continue_oid)

        test_object = DbWorkflowObject()
        test_object.set_data(0)
        test_object.save()
        workflow = start('test_workflow_logic', [test_object])

        self.assertEqual(5, test_object.get_data())
        self.assertEqual("lt9", test_object.extra_data["test"])

        workflow = continue_oid(test_object.id)
        self.assertEqual(6, test_object.get_data())
        self.assertEqual("lt9", test_object.extra_data["test"])

        workflow = continue_oid(test_object.id)
        self.assertEqual(9, test_object.get_data())
        self.assertEqual("gte9", test_object.extra_data["test"])

        workflow = continue_oid(test_object.id)
        self.assertEqual(15, test_object.get_data())
        self.assertEqual("gte9", test_object.extra_data["test"])

        workflow = continue_oid(test_object.id)
        self.assertEqual(test_object.known_statuses.COMPLETED, test_object.status)
        self.assertEqual(WorkflowStatus.COMPLETED, workflow.status)

    def test_workflow_without_workflow_object_saved(self):
        """Test that the logic tasks work correctly."""
        from invenio.modules.workflows.api import start_by_wid

        test_object = DbWorkflowObject()
        test_object.set_data(0)
        test_object.save()

        workflow = start('test_workflow_logic', [test_object])

        self.assertEqual(5, test_object.get_data())
        self.assertEqual("lt9", test_object.extra_data["test"])
        start_by_wid(workflow.uuid)
        test_object.delete(test_object.id)

    def test_workflow_task_results(self):
        """Test the setting and getting of task results."""

        test_object = DbWorkflowObject()
        test_object.save()  # Saving is needed to instantiate default values

        test_object.add_task_result("test", {"data": "testing"})
        results = test_object.get_tasks_results()
        self.assertEqual(len(results.get("test")), 1)

        result_item = results.get("test")[0]
        self.assertEqual({"data": "testing"},
                         result_item.get("result"))
        self.assertEqual("workflows/results/default.html",
                         result_item.get("template"))
        self.assertEqual("test",
                         result_item.get("name"))


TEST_SUITE = make_test_suite(WorkflowTasksTestAPI,
                             TestWorkflowTasks)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
