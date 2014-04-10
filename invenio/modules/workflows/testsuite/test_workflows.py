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

"""Unit tests for workflows views."""

from __future__ import absolute_import

import random
import time
import logging

from invenio.testsuite import InvenioTestCase, make_test_suite, \
    run_test_suite
from ..registry import WorkflowsRegistry
from flask.ext.registry import ImportPathRegistry


TEST_PACKAGES = [
    'invenio.modules.*',
    'invenio.modules.workflows.testsuite',
]


class WorkflowViewTest(InvenioTestCase):
    """ Test search view functions. """

    def test_main_admin_availability(self):
        from flask import url_for

        response = self.client.get(url_for('workflows.index'))
        # FIXME: tmp 401 due to missing file
        self.assert401(response)

    def test_workflow_list_availability(self):
        from flask import url_for

        response = self.client.get(url_for('workflows.show_workflows'))
        # FIXME: tmp 401 due to missing file
        self.assert401(response)


class WorkflowTasksTestCase(InvenioTestCase):
    def create_registries(self):
        self.app.extensions['registry']['workflows.tests'] = \
            ImportPathRegistry(initial=TEST_PACKAGES)
        self.app.extensions['registry']['workflows'] = \
            WorkflowsRegistry(
                'workflows', app=self.app, registry_namespace='workflows.tests'
            )
        self.app.extensions['registry']['workflows.widgets'] = \
            WorkflowsRegistry(
                'widgets', app=self.app, registry_namespace='workflows.tests'
            )

    def cleanup_registries(self):
        del self.app.extensions['registry']['workflows.tests']
        del self.app.extensions['registry']['workflows']
        del self.app.extensions['registry']['workflows.widgets']


class WorkflowTasksTestAPI(WorkflowTasksTestCase):
    """ Test basic workflow API """
    def setUp(self):
        self.create_registries()

        self.test_data = {}
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
        """ Clean up created objects """
        from invenio.modules.workflows.models import (BibWorkflowObject,
                                                      Workflow,
                                                      BibWorkflowEngineLog,
                                                      BibWorkflowObjectLog)
        from invenio.ext.sqlalchemy import db
        workflows = Workflow.get(Workflow.module_name == "unit_tests").all()
        for workflow in workflows:
            BibWorkflowObject.query.filter(
                BibWorkflowObject.id_workflow == workflow.uuid
            ).delete()

            objects = BibWorkflowObjectLog.query.filter(
                BibWorkflowObject.id_workflow == workflow.uuid
            ).all()
            for obj in objects:
                db.session.delete(obj)
            db.session.delete(workflow)

            objects = BibWorkflowObjectLog.query.filter(
                BibWorkflowObject.id_workflow == workflow.uuid
            ).all()
            for obj in objects:
                BibWorkflowObjectLog.delete(id=obj.id)
            BibWorkflowEngineLog.delete(uuid=workflow.uuid)
            # Deleting dumy object created in tests
        db.session.query(BibWorkflowObject).filter(
            BibWorkflowObject.id_workflow.in_([11, 123, 253])
        ).delete(synchronize_session='fetch')
        Workflow.query.filter(Workflow.module_name == "unit_tests").delete()
        db.session.commit()
        self.cleanup_registries()

    def test_halt(self):
        from invenio.modules.workflows.registry import workflows
        from invenio.modules.workflows.api import start
        from invenio.modules.workflows.engine import WorkflowStatus
        from invenio.modules.workflows.models import (BibWorkflowObjectLog,
                                                      ObjectVersion)

        halt_engine = lambda obj, eng: eng.halt("Test")

        class HaltTest(object):
            workflow = [halt_engine]

        workflows['halttest'] = HaltTest

        data = [set(('somekey', 'somevalue'))]
        eng = start('halttest', data)
        idx, obj = list(eng.getObjects())[0]

        assert obj.version == ObjectVersion.HALTED
        assert eng.status == WorkflowStatus.HALTED
        assert BibWorkflowObjectLog.get(
            id_object=obj.id, log_type=logging.ERROR).count() == 0

    def test_halt_in_branch(self):
        from workflow.patterns import IF_ELSE
        from invenio.modules.workflows.registry import workflows
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

        data = [set(('somekey', 'somevalue'))]
        eng = start('branchtest', data)
        idx, obj = list(eng.getObjects())[0]

        assert obj.version == ObjectVersion.HALTED
        assert eng.status == WorkflowStatus.HALTED
        assert BibWorkflowObjectLog.get(
            id_object=obj.id, log_type=logging.ERROR).count() == 0

    def test_object_creation_complete(self):
        """
        Test status of object before/after workflow when
        created before calling API, with "high" test-data that will
        make the workflow complete.
        """
        from invenio.modules.workflows.models import (BibWorkflowObject,
                                                      ObjectVersion)
        from invenio.modules.workflows.engine import WorkflowStatus
        from invenio.modules.workflows.api import start

        test_object = BibWorkflowObject()
        test_object.set_data(20)
        test_object.save()

        self.assertEqual(test_object.version, ObjectVersion.INITIAL)
        self.assertEqual(test_object.id_parent, None)
        self.assertEqual(test_object.get_data(), 20)

        engine = start('test_workflow', [test_object],
                       module_name="unit_tests")

        self.assertEqual(test_object.get_data(), 38)
        self.assertNotEqual(test_object.id_parent, None)
        self.assertEqual(engine.status, WorkflowStatus.COMPLETED)
        self.assertEqual(test_object.version, ObjectVersion.FINAL)

    def test_object_creation_halt(self):
        """
        Test status of object before/after workflow when
        created before calling API, with "low" test-data that will
        make the workflow halt.
        """
        from invenio.modules.workflows.models import (BibWorkflowObject,
                                                      ObjectVersion)
        from invenio.modules.workflows.api import start
        from invenio.modules.workflows.engine import WorkflowStatus

        test_object = BibWorkflowObject()
        test_object.save()
        test_object.set_data(2)

        self.assertEqual(test_object.version, ObjectVersion.INITIAL)
        self.assertEqual(test_object.id_parent, None)
        self.assertEqual(test_object.get_data(), 2)

        engine = start('test_workflow', [test_object],
                       module_name="unit_tests")

        self.assertEqual(test_object.get_data(), 2)
        self.assertEqual(test_object.version, ObjectVersion.HALTED)
        self.assertEqual(engine.status, WorkflowStatus.HALTED)

    def test_workflow_engine_instantiation(self):
        """
        Checking the proper instantiation of the Workflow model
        and BibWorkflowEngine object.
        """
        from invenio.modules.workflows.models import Workflow
        from invenio.modules.workflows.engine import BibWorkflowEngine
        from uuid import uuid1 as new_uuid

        test_workflow = Workflow(name='test_workflow', uuid=new_uuid(),
                                 id_user=0, module_name="Unknown", )
        test_workflow_engine = BibWorkflowEngine(name=test_workflow.name,
                                                 uuid=test_workflow.uuid)
        self.assertEqual(test_workflow.name, test_workflow_engine.name)

    def test_workflow_restarts(self):
        """
        Checks if all is well when restarting a workflow an arbitrary
        number of times.
        """
        from invenio.modules.workflows.models import (BibWorkflowObject,
                                                      ObjectVersion)
        from invenio.modules.workflows.api import start, continue_oid
        from invenio.modules.workflows.engine import WorkflowStatus

        test_object = BibWorkflowObject()

        random.seed(time.time())
        tries = random.randint(5, 15)

        test_object.set_data(tries)
        test_object.save()

        engine = start('test_workflow_hardcore', [test_object],
                       module_name="unit_tests")
        for i in range(0, tries):
            self.assertEqual(engine.status, WorkflowStatus.HALTED)
            for my_object_b in engine.getObjects():
                engine = continue_oid(my_object_b[1].id, "restart_task")
        self.assertEqual(test_object.get_data(), 0)
        self.assertEqual(test_object.version, ObjectVersion.FINAL)
        self.assertEqual(engine.status, WorkflowStatus.COMPLETED)

    def test_workflow_object_creation(self):
        """
        Tests to see if the right snapshots or object versions
        are created when passing existing objects.
        """
        from invenio.modules.workflows.models import (BibWorkflowObject,
                                                      ObjectVersion)
        from invenio.modules.workflows.api import start

        initial_data = 22
        final_data = 40

        test_object = BibWorkflowObject()
        test_object.set_data(initial_data)
        test_object.save()

        workflow = start(workflow_name="test_workflow",
                         data=[test_object],
                         module_name="unit_tests")

        # Get parent object of the workflow we just ran
        initial_object = BibWorkflowObject.query.get(test_object.id_parent)
        all_objects = BibWorkflowObject.query.filter(
            BibWorkflowObject.id_workflow == workflow.uuid
        ).order_by(BibWorkflowObject.id).all()

        # There should only be 2 objects (initial, final)
        self.assertEqual(len(all_objects), 2)
        self.assertEqual(test_object.id_parent, initial_object.id)
        self.assertEqual(initial_object.version, ObjectVersion.INITIAL)
        self.assertEqual(initial_object.get_data(), initial_data)
        self.assertEqual(test_object.get_data(), final_data)
        self.assertEqual(test_object.version, ObjectVersion.FINAL)

    def test_workflow_object_creation_simple(self):
        """
        Tests to see if the right snapshots or object versions
        are created with simple data.
        """
        from invenio.modules.workflows.models import (BibWorkflowObject,
                                                      ObjectVersion)
        from invenio.modules.workflows.api import start

        initial_data = 22
        final_data = 40

        workflow = start(workflow_name="test_workflow",
                         data=[initial_data],
                         module_name="unit_tests")

        # Get parent object of the workflow we just ran
        initial_object = BibWorkflowObject.query.filter(
            BibWorkflowObject.id_workflow == workflow.uuid,
            BibWorkflowObject.id_parent == None).first()  # noqa E711
        test_object = BibWorkflowObject.query.filter(
            BibWorkflowObject.id_workflow == workflow.uuid,
            BibWorkflowObject.id_parent == initial_object.id).first()
        all_objects = BibWorkflowObject.query.filter(
            BibWorkflowObject.id_workflow == workflow.uuid
        ).order_by(BibWorkflowObject.id).all()

        # There should only be 2 objects (initial, final)
        self.assertEqual(len(all_objects), 2)
        self.assertEqual(test_object.id_parent, initial_object.id)
        self.assertEqual(initial_object.version, ObjectVersion.INITIAL)
        self.assertEqual(initial_object.get_data(), initial_data)
        self.assertEqual(test_object.get_data(), final_data)
        self.assertEqual(test_object.version, ObjectVersion.FINAL)

    def test_workflow_complex_run(self):
        """Tests running workflow with several data objects"""
        from invenio.modules.workflows.models import (BibWorkflowObject,
                                                      ObjectVersion)
        from invenio.modules.workflows.api import start

        self.test_data = [1, 20]
        final_data = [1, 38]

        workflow = start(workflow_name="test_workflow",
                         data=self.test_data,
                         module_name="unit_tests")

        # Get parent objects of the workflow we just ran
        objects = BibWorkflowObject.query.filter(
            BibWorkflowObject.id_workflow == workflow.uuid,
            BibWorkflowObject.id_parent == None  # noqa E711
        ).order_by(BibWorkflowObject.id).all()

        # Let's check that we found anything.
        # There should only be three objects
        self.assertEqual(len(objects), 2)

        all_objects = BibWorkflowObject.query.filter(
            BibWorkflowObject.id_workflow == workflow.uuid
        ).order_by(BibWorkflowObject.id).all()

        self.assertEqual(len(all_objects), 4)

        for obj in objects:
            # The child object should have the final or halted version
            self.assertTrue(obj.child_objects[0].version in (ObjectVersion.FINAL,
                                                             ObjectVersion.HALTED))
            # Making sure the final data is correct
            self.assertTrue(obj.child_objects[0].get_data() in final_data)

    def test_workflow_marcxml(self):
        """Tests runnning a record ingestion workflow with a widget step"""
        from invenio.modules.workflows.models import (BibWorkflowObject,
                                                      ObjectVersion)
        from invenio.modules.workflows.engine import WorkflowStatus
        from invenio.modules.workflows.api import start

        initial_data = self.recxml
        workflow = start(workflow_name="marcxml_workflow",
                         data=[initial_data],
                         module_name="unit_tests")

        # Get objects of the workflow we just ran
        objects = BibWorkflowObject.query.filter(
            BibWorkflowObject.id_workflow == workflow.uuid,
            BibWorkflowObject.id_parent == None  # noqa E711
        ).order_by(BibWorkflowObject.id).all()

        self._check_workflow_execution(objects,
                                       initial_data, None)

        all_objects = BibWorkflowObject.query.filter(
            BibWorkflowObject.id_workflow == workflow.uuid
        ).order_by(BibWorkflowObject.id).all()

        self.assertEqual(len(all_objects), 2)

        self.assertEqual(workflow.status, WorkflowStatus.HALTED)

        current = BibWorkflowObject.query.filter(
            BibWorkflowObject.id_workflow == workflow.uuid,
            BibWorkflowObject.version == ObjectVersion.HALTED
        ).one()

        self.assertEqual(current.get_widget(), "approval_widget")

    def test_workflow_for_halted_object(self):
        """Test workflow with continuing a halted object"""
        from invenio.modules.workflows.models import (BibWorkflowObject,
                                                      ObjectVersion)
        from invenio.modules.workflows.api import start, continue_oid
        from invenio.modules.workflows.engine import WorkflowStatus

        current = BibWorkflowObject()
        current.set_data(self.recxml)
        current.save()

        workflow = start(workflow_name="marcxml_workflow",
                         data=[current],
                         module_name="unit_tests")

        self.assertEqual(workflow.status, WorkflowStatus.HALTED)
        self.assertEqual(current.version, ObjectVersion.HALTED)

        workflow = continue_oid(current.id,
                                module_name="unit_tests")
        self.assertEqual(workflow.status, WorkflowStatus.COMPLETED)
        self.assertEqual(current.version, ObjectVersion.FINAL)

    def test_workflow_for_finished_object(self):
        """Test starting workflow with finished object given"""
        from invenio.modules.workflows.models import (BibWorkflowObject,
                                                      ObjectVersion)
        from invenio.modules.workflows.api import start
        from invenio.modules.workflows.engine import WorkflowStatus

        current = BibWorkflowObject()
        current.set_data(20)
        current.save()

        workflow = start(workflow_name="test_workflow",
                         data=[current],
                         module_name="unit_tests")

        self.assertEqual(workflow.status, WorkflowStatus.COMPLETED)
        self.assertEqual(current.version, ObjectVersion.FINAL)
        self.assertEqual(current.get_data(), 38)

        previous = BibWorkflowObject.query.get(current.id)

        workflow_2 = start(workflow_name="test_workflow",
                           data=[previous],
                           module_name="unit_tests")

        self.assertEqual(workflow_2.status, WorkflowStatus.COMPLETED)
        self.assertEqual(previous.version, ObjectVersion.FINAL)
        self.assertEqual(previous.get_data(), 56)

    def test_logging_for_workflow_objects_without_workflow(self):
        """This test run a virtual object out of a workflow for
test purpose, this object will log several things"""
        from invenio.modules.workflows.models import (BibWorkflowObject,
                                                      BibWorkflowObjectLog,
                                                      ObjectVersion)

        initial_data = 20
        obj_init = BibWorkflowObject(id_workflow=11,
                                     version=ObjectVersion.INITIAL)
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

        obj_test = BibWorkflowObjectLog.query.filter(
            BibWorkflowObjectLog.id_object == obj_init.id).all()
        messages_found = 0
        for current_obj in obj_test:
            if current_obj.message == info_msg and messages_found == 0:
                messages_found += 1
            elif current_obj.message == err_msg and messages_found == 1:
                messages_found += 1
        self.assertEqual(messages_found, 2)

    def test_workflow_for_running_object(self):
        """
        Test starting workflow with running object given and watch it fail.
        """
        from invenio.modules.workflows.models import (BibWorkflowObject,
                                                      ObjectVersion)
        from invenio.modules.workflows.api import start_by_oids
        from invenio.modules.workflows.errors import WorkflowObjectVersionError

        obj_running = BibWorkflowObject()
        obj_running.set_data(1234)
        obj_running.save(version=ObjectVersion.RUNNING)

        self.assertRaises(WorkflowObjectVersionError,
                          start_by_oids,
                          'test_workflow',
                          [obj_running.id],
                          module_name="unit_tests")

    def test_continue_execution_for_object(self):
        """
        Tests continuing execution of workflow for object
        given object from prev, current and next task.
        """
        from invenio.modules.workflows.models import (BibWorkflowObject,
                                                      ObjectVersion)
        from invenio.modules.workflows.api import (start,
                                                   continue_oid)

        initial_data = 1

        # testing restarting from previous task
        init_workflow = start("test_workflow",
                              data=[initial_data],
                              module_name="unit_tests")

        obj_halted = BibWorkflowObject.query.filter(
            BibWorkflowObject.id_workflow == init_workflow.uuid,
            BibWorkflowObject.version == ObjectVersion.HALTED
        ).first()

        self.assertTrue(obj_halted)
        self.assertEqual(obj_halted.get_data(), 1)

        # Try to restart, we should halt again actually.
        continue_oid(oid=obj_halted.id,
                     start_point="restart_task",
                     module_name="unit_tests")

        self.assertEqual(obj_halted.get_data(), 1)
        self.assertEqual(obj_halted.version, ObjectVersion.HALTED)

        # We skip to next part, this should work
        continue_oid(oid=obj_halted.id,
                     start_point="continue_next",
                     module_name="unit_tests")

        self.assertEqual(obj_halted.get_data(), 19)
        self.assertEqual(obj_halted.version, ObjectVersion.FINAL)

        # Let's do that last task again, shall we?
        continue_oid(oid=obj_halted.id,
                     start_point="restart_prev",
                     module_name="unit_tests")

        self.assertEqual(obj_halted.get_data(), 37)
        self.assertEqual(obj_halted.version, ObjectVersion.FINAL)

    def test_restart_workflow(self):
        """Tests restarting workflow for given workflow id"""
        from invenio.modules.workflows.models import (BibWorkflowObject,
                                                      ObjectVersion)
        from invenio.modules.workflows.api import (start,
                                                   start_by_wid)

        initial_data = 1

        init_workflow = start(workflow_name="test_workflow",
                              data=[initial_data],
                              module_name="unit_tests")

        init_objects = BibWorkflowObject.query.filter(
            BibWorkflowObject.id_workflow == init_workflow.uuid
        ).order_by(BibWorkflowObject.id).all()
        self.assertEqual(len(init_objects), 2)

        restarted_workflow = start_by_wid(wid=init_workflow.uuid,
                                          module_name="unit_tests")

        restarted_objects = BibWorkflowObject.query.filter(
            BibWorkflowObject.id_workflow == restarted_workflow.uuid
        ).order_by(BibWorkflowObject.id).all()

        # This time we should only have one more initial object
        self.assertEqual(len(restarted_objects), 3)

        # First and last object will be INITIAL
        self.assertEqual(restarted_objects[0].version,
                         ObjectVersion.INITIAL)

        self.assertEqual(restarted_objects[0].version,
                         restarted_objects[2].version)

        self.assertEqual(restarted_objects[1].id_parent,
                         restarted_objects[2].id)

        self.assertEqual(restarted_objects[0].get_data(),
                         restarted_objects[2].get_data())

    def test_object_workflow_api(self):
        """ Test the object bound workflow start/continue functions"""
        from invenio.modules.workflows.models import (BibWorkflowObject,
                                                      ObjectVersion)
        from invenio.modules.workflows.engine import WorkflowStatus

        obj = BibWorkflowObject.create_object(id_user=1234)
        obj.set_data(10)
        obj.save()

        engine = obj.start_workflow("test_workflow",
                                    module_name="unit_tests")

        self.assertEqual(engine.status, WorkflowStatus.HALTED)
        self.assertEqual(obj.version, ObjectVersion.HALTED)

        # Now we amend data again
        obj.set_data(49)
        engine = obj.continue_workflow(start_point="restart_task",
                                       module_name="unit_tests")

        self.assertEqual(engine.status, WorkflowStatus.COMPLETED)
        self.assertEqual(obj.get_data(), 49 + 18)
        self.assertEqual(obj.version, ObjectVersion.FINAL)

    def _check_workflow_execution(self, objects, initial_data, final_data):
        from invenio.modules.workflows.models import ObjectVersion

        # Let's check that we found anything. There should only be one object
        self.assertEqual(len(objects), 1)
        parent_object = objects[0]

        # The object should be the inital version
        self.assertEqual(parent_object.version, ObjectVersion.INITIAL)

        # The object should have the inital data
        self.assertEqual(parent_object.get_data(), initial_data)

        # Fetch final object which should exist
        final_object = objects[0].child_objects[0]
        self.assertTrue(final_object)

        if final_data:
            # Check that final data is correct
            self.assertEqual(final_object.get_data(), final_data)


class TestWorkflowTasks(WorkflowTasksTestCase):
    """
    Tests meant for testing the the generic tasks available.
    """
    def setUp(self):
        self.create_registries()

    def tearDown(self):
        self.cleanup_registries()

    def test_logic_tasks(self):
        """
        Tests that the logic tasks work correctly.
        """
        from invenio.modules.workflows.models import BibWorkflowObject
        from invenio.modules.workflows.api import start, continue_oid

        test_object = BibWorkflowObject()
        test_object.set_data(0)
        test_object.save()

        start('test_workflow_logic', [test_object])

        self.assertEqual(test_object.get_data(), 5)
        self.assertEqual(test_object.get_extra_data()["test"], "lt9")
        continue_oid(test_object.id,
                     start_point="continue_next")

        self.assertEqual(test_object.get_data(), 6)
        self.assertEqual(test_object.get_extra_data()["test"], "lt9")
        continue_oid(test_object.id,
                     start_point="continue_next")

        self.assertEqual(test_object.get_data(), 9)
        self.assertEqual(test_object.get_extra_data()["test"], "gte9")
        continue_oid(test_object.id,
                     start_point="continue_next")

        self.assertEqual(test_object.get_data(), 15)
        self.assertEqual(test_object.get_extra_data()["test"], "gte9")
        continue_oid(test_object.id,
                     start_point="continue_next")

TEST_SUITE = make_test_suite(WorkflowViewTest,
                             WorkflowTasksTestAPI,
                             TestWorkflowTasks)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
