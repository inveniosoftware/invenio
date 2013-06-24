## This file is part of Invenio.
## Copyright (C) 2012, 2013 CERN.
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
BibWorkflow Unit tests - functions to test workflows
"""

from invenio.testutils import make_flask_test_suite, run_test_suite, \
    FlaskSQLAlchemyTest
from invenio.bibworkflow_api import run, run_by_wid, continue_oid
from invenio.inveniomanage import db
from invenio.bibworkflow_config import CFG_OBJECT_VERSION


class TestWorkflowStart(FlaskSQLAlchemyTest):
    """Tests for BibWorkflow API."""

    def setUp(self):
        self.test_data = {}
        self.workflow_ids = []
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
  2009, pp 115-122</journal-ref><doi>10.1007/978-3-540-75826-6_11</doi><abstract>  We study the dynamics of 2D and 3D barred galaxy analytical models, focusing
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
        from invenio.bibworkflow_model import BibWorkflowObject, Workflow
        for wid in self.workflow_ids:
            pass
            #BibWorkflowObject.query.filter(BibWorkflowObject.workflow_id == wid).delete()
            #Workflow.query.filter(Workflow.uuid == wid).delete()
        db.session.commit()

    def test_workflow_basic_run(self):
        """Tests running workflow with one data object"""
        from invenio.bibworkflow_model import BibWorkflowObject

        self.test_data = {'data': 20}
        initial_data = self.test_data
        final_data = {'data': 41}

        workflow = run(wname="test_workflow",
                       data=[{"data": self.test_data}],
                       task_queue=False)

        # Keep id for cleanup after
        self.workflow_ids.append(workflow.uuid)

        # Get parent object of the workflow we just ran
        # NOTE: ignore PEP8 here for None
        objects = BibWorkflowObject.query.filter(BibWorkflowObject.workflow_id == workflow.uuid,
                                                 BibWorkflowObject.parent_id == None)
        all_objects = BibWorkflowObject.query.filter(BibWorkflowObject.workflow_id == workflow.uuid)
        self.assertEqual(all_objects.count(), 2)
        self._check_workflow_execution(workflow, objects,
                                       initial_data, final_data)

    def test_workflow_complex_run(self):
        """Tests running workflow with several data objects"""
        from invenio.bibworkflow_model import BibWorkflowObject

        self.test_data = [{'data': {'data': 1}}, {'data':{'data': "wwww"}}, {'data':{'data': 20}}]
        final_data = [{'data': 19}, {'data': "wwww"}, {'data': 38}]

        workflow = run(wname="test_workflow_2",
                       data=self.test_data,
                       task_queue=False)

        # Keep id for cleanup after
        self.workflow_ids.append(workflow.uuid)

        # Get parent objects of the workflow we just ran
        # NOTE: ignore PEP8 here for None
        objects = BibWorkflowObject.query.filter(BibWorkflowObject.workflow_id == workflow.uuid,
                                                 BibWorkflowObject.parent_id == None)
        # Let's check that we found anything. There should only be three objects
        self.assertEqual(objects.count(), 3)

        all_objects = BibWorkflowObject.query.filter(BibWorkflowObject.workflow_id == workflow.uuid)
        self.assertEqual(all_objects.count(), 6)

        for obj in objects.all():
            # The child object should have the final or halted version
            self.assertTrue(obj.child_objects[0].version
                            in (CFG_OBJECT_VERSION.FINAL,
                                CFG_OBJECT_VERSION.HALTED))
            # Making sure the final data is correct
            self.assertTrue(obj.child_objects[0].data
                            in final_data)

    def test_workflow_recordxml(self):
        """Tests runnning a record ingestion workflow"""
        from invenio.bibworkflow_model import BibWorkflowObject

        initial_data = {'data': self.recxml}
        workflow = run(wname="marcxml_workflow",
                       data=[{"data": {'data': self.recxml}, 'type': "text/xml"}],
                       task_queue=False)

        # Keep id for cleanup after
        self.workflow_ids.append(workflow.uuid)

        # Get parent object of the workflow we just ran
        # NOTE: ignore PEP8 here for None
        objects = BibWorkflowObject.query.filter(BibWorkflowObject.workflow_id == workflow.uuid,
                                                 BibWorkflowObject.parent_id == None)

        all_objects = BibWorkflowObject.query.filter(BibWorkflowObject.workflow_id == workflow.uuid)
        self.assertEqual(all_objects.count(), 2)

        self._check_workflow_execution(workflow, objects,
                                       initial_data, None)

    def test_workflow_for_halted_object(self):
        """Test starting workflow with halted object given"""
        from invenio.bibworkflow_model import BibWorkflowObject
        initial_data = {'data': 1}
        obj_init = BibWorkflowObject(data=initial_data,
                                     workflow_id=123,
                                     version=CFG_OBJECT_VERSION.INITIAL)
        obj_init._update_db()
        halted_data = {'data': 1}
        obj_halted = BibWorkflowObject(data=halted_data,
                                       workflow_id=123,
                                       parent_id=obj_init.id,
                                       version=CFG_OBJECT_VERSION.HALTED)
        obj_halted._update_db()

        workflow = run('test_workflow', [{'id': obj_halted.id}], task_queue=False)

        final_data = {'data': 2}
        objects = BibWorkflowObject.query.filter(BibWorkflowObject.workflow_id == workflow.uuid,
                                                 BibWorkflowObject.parent_id == None)

        all_objects = BibWorkflowObject.query.filter(BibWorkflowObject.workflow_id == workflow.uuid)
        self.assertEqual(all_objects.count(), 2)

        # Check the workflow execution
        self._check_workflow_execution(workflow, objects, halted_data, final_data)

        # Check copied INITIAL object
        self.assertEqual(obj_halted.data, objects[0].data)

        # Check if first object were untached
        self.assertEqual(obj_init.workflow_id, "123")
        self.assertEqual(obj_halted.workflow_id, "123")

    def test_workflow_for_finished_object(self):
        """Test starting workflow with finished object given"""
        from invenio.bibworkflow_model import BibWorkflowObject
        initial_data = {'data': 20}
        obj_init = BibWorkflowObject(data=initial_data,
                                     workflow_id=253,
                                     version=CFG_OBJECT_VERSION.INITIAL)
        obj_init._update_db()
        first_final_data = {'data': 41}
        obj_final = BibWorkflowObject(data=first_final_data,
                                       workflow_id=253,
                                       parent_id=obj_init.id,
                                       version=CFG_OBJECT_VERSION.FINAL)
        obj_final._update_db()

        workflow = run('test_workflow', [{'id': obj_final.id}], task_queue=False)

        final_data = {'data': 62}
        objects = BibWorkflowObject.query.filter(BibWorkflowObject.workflow_id == workflow.uuid,
                                                 BibWorkflowObject.parent_id == None)

        all_objects = BibWorkflowObject.query.filter(BibWorkflowObject.workflow_id == workflow.uuid)
        self.assertEqual(all_objects.count(), 2)

        # Check the workflow execution
        self._check_workflow_execution(workflow, objects, first_final_data, final_data)

        # Check copied INITIAL object
        self.assertEqual(obj_final.data, objects[0].data)

        # Check if first object were untached
        self.assertEqual(obj_init.workflow_id, "253")
        self.assertEqual(obj_final.workflow_id, "253")

    def test_workflow_for_running_object(self):
        """Test starting workflow with running object given"""
        from invenio.bibworkflow_model import BibWorkflowObject
        initial_data = {'data': 20}
        obj_init = BibWorkflowObject(data=initial_data,
                                     workflow_id=11,
                                     version=CFG_OBJECT_VERSION.INITIAL)
        obj_init._update_db()
        running_data = {'data': 26}
        obj_running = BibWorkflowObject(data=running_data,
                                        workflow_id=11,
                                        parent_id=obj_init.id,
                                        version=CFG_OBJECT_VERSION.RUNNING)
        obj_running._update_db()
        workflow = run('test_workflow', [{'id': obj_running.id}], task_queue=False)

        final_data = {'data': 41}
        objects = BibWorkflowObject.query.filter(BibWorkflowObject.workflow_id == workflow.uuid,
                                                 BibWorkflowObject.parent_id == None)

        all_objects = BibWorkflowObject.query.filter(BibWorkflowObject.workflow_id == workflow.uuid)
        self.assertEqual(all_objects.count(), 2)

        # Check the workflow execution
        self._check_workflow_execution(workflow, objects, initial_data, final_data)

        # Check copied INITIAL object
        self.assertEqual(obj_init.data, objects[0].data)

        # Check if first object were untached
        self.assertEqual(obj_init.workflow_id, "11")
        objects = BibWorkflowObject.query.filter(BibWorkflowObject.id == obj_running.id)
        self.assertEqual(objects.count(), 0)

    def test_continue_execution_for_object(self):
        """Tests continuing execution of workflow for object given object from \
        prev, current and next task"""
        from invenio.bibworkflow_model import BibWorkflowObject

        initial_data = {'data': 1}
        final_data_prev = {'data': 3}
        final_data_curr = {'data': 2}
        final_data_next = {'data': 9}

        # testing restarting from previous task
        init_workflow = run("test_workflow", data=[{"data": initial_data}], task_queue=False)

        obj_halted = BibWorkflowObject.query.filter(BibWorkflowObject.workflow_id == init_workflow.uuid,
                                                    BibWorkflowObject.version == CFG_OBJECT_VERSION.HALTED).first()
        workflow = continue_oid(obj_halted.id, "restart_prev", task_queue=False)
        object = BibWorkflowObject.query.filter(BibWorkflowObject.id == obj_halted.id)
        self.assertEqual(object.count(), 1)
        self.assertEqual(object[0].data, final_data_prev)

        all_objects = BibWorkflowObject.query.filter(BibWorkflowObject.workflow_id == workflow.uuid)
        self.assertEqual(all_objects.count(), 2)

        # testing restarting from current task
        init_workflow2 = run("test_workflow", data=[{"data": initial_data}], task_queue=False)

        obj_halted2 = BibWorkflowObject.query.filter(BibWorkflowObject.workflow_id == init_workflow2.uuid,
                                                     BibWorkflowObject.version == CFG_OBJECT_VERSION.HALTED).first()
        workflow2 = continue_oid(obj_halted.id, "restart_task", task_queue=False)
        object2 = BibWorkflowObject.query.filter(BibWorkflowObject.id == obj_halted2.id)
        self.assertEqual(object2.count(), 1)
        self.assertEqual(object2[0].data, final_data_curr)

        all_objects2 = BibWorkflowObject.query.filter(BibWorkflowObject.workflow_id == workflow2.uuid)
        self.assertEqual(all_objects2.count(), 2)

        # testing continuing from next task
        init_workflow3 = run("test_workflow", data=[{"data": initial_data}], task_queue=False)

        obj_halted3 = BibWorkflowObject.query.filter(BibWorkflowObject.workflow_id == init_workflow3.uuid,
                                                     BibWorkflowObject.version == CFG_OBJECT_VERSION.HALTED).first()
        workflow3 = continue_oid(obj_halted3.id, "continue_next", task_queue=False)
        object3 = BibWorkflowObject.query.filter(BibWorkflowObject.id == obj_halted3.id)
        self.assertEqual(object3.count(), 1)
        self.assertEqual(object3[0].data, final_data_next)

        all_objects3 = BibWorkflowObject.query.filter(BibWorkflowObject.workflow_id == workflow3.uuid)
        self.assertEqual(all_objects3.count(), 2)

    def test_restart_workflow(self):
        """Tests restarting workflow for given workflow id"""
        from invenio.bibworkflow_model import BibWorkflowObject, WorkflowLogging
        from invenio.bibworkflow_api import continue_oid

        initial_data = {'data': 1}

        # testing restarting from previous task
        init_workflow = run("test_workflow", data=[{"data": initial_data}], task_queue=False)
        init_objects = BibWorkflowObject.query.filter(BibWorkflowObject.workflow_id == init_workflow.uuid)

        restarted_workflow = run_by_wid(init_workflow.uuid, task_queue=False)
        restarted_objects = BibWorkflowObject.query.filter(BibWorkflowObject.workflow_id == restarted_workflow.uuid)

        self.assertEqual(restarted_objects.count(), 1)

        self.assertEqual(restarted_objects[0].version, init_objects[1].version)
        self.assertEqual(restarted_objects[0].parent_id, init_objects[0].id)
        self.assertEqual(restarted_objects[0].data, init_objects[1].data)

    def _check_workflow_execution(self, workflow, objects,
                                  initial_data, final_data):
        # Let's check that we found anything. There should only be one object
        self.assertEqual(objects.count(), 1)

        parent_object = objects[0]

        # The object should be the inital version
        self.assertEqual(parent_object.version, CFG_OBJECT_VERSION.INITIAL)

        # The object should have the inital data
        self.assertEqual(parent_object.data, initial_data)

        # Fetch final object which should exist
        final_object = objects[0].child_objects[0]
        self.assertTrue(final_object)

        if final_data:
            # Check that final data is correct
            self.assertEqual(final_object.data, final_data)


TEST_SUITE = make_flask_test_suite(TestWorkflowStart)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
