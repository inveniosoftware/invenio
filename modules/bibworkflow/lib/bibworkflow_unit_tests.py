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

from invenio.importutils import lazy_import
from invenio.testutils import make_test_suite, run_test_suite, \
    InvenioTestCase
from invenio.sqlalchemyutils import db
from invenio.bibworkflow_config import CFG_OBJECT_VERSION

run = lazy_import('invenio.bibworkflow_api:run')


class TestWorkflowStart(InvenioTestCase):
    """Tests for BibWorkflow API."""

    def setUp(self):
        super(TestWorkflowStart, self).setUp()
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
        from invenio.bibworkflow_model import WfeObject, Workflow
        for wid in self.workflow_ids:
            WfeObject.query.filter(WfeObject.workflow_id == wid).delete()
            Workflow.query.filter(Workflow.uuid == wid).delete()
        db.session.commit()
        super(TestWorkflowStart, self).tearDown()

    def test_workflow_basic_run(self):
        """Tests running workflow with one data object"""
        from invenio.bibworkflow_model import WfeObject

        self.test_data = {'data': 20}
        initial_data = self.test_data
        final_data = {'data': 41}

        workflow = run(wname="test_workflow",
                       data=[self.test_data],
                       task_queue=False)

        # Keep id for cleanup after
        self.workflow_ids.append(workflow.uuid)

        # Get parent object of the workflow we just ran
        # NOTE: ignore PEP8 here for None
        objects = WfeObject.query.filter(WfeObject.workflow_id == workflow.uuid,
                                         WfeObject.parent_id == None)

        self._check_workflow_execution(workflow, objects,
                                       initial_data, final_data)

    def test_workflow_complex_run(self):
        """Tests running workflow with several data objects"""
        from invenio.bibworkflow_model import WfeObject

        self.test_data = [{"data": 1}, {"data": "wwww"}, {"data": 20}]
        final_data = [{"data": 19}, {"data": "wwww"}, {"data": 38}]

        workflow = run(wname="test_workflow_2",
                       data=self.test_data,
                       task_queue=False)

        # Keep id for cleanup after
        self.workflow_ids.append(workflow.uuid)

        # Get parent objects of the workflow we just ran
        # NOTE: ignore PEP8 here for None
        objects = WfeObject.query.filter(WfeObject.workflow_id == workflow.uuid,
                                         WfeObject.parent_id == None)

        # Let's check that we found anything. There should only be three objects
        self.assertEqual(objects.count(), 3)

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
        from invenio.bibworkflow_model import WfeObject

        initial_data = {"data": self.recxml, 'type': "text/xml"}
        workflow = run(wname="marcxml_workflow",
                       data=[{"data": self.recxml, 'type': "text/xml"}],
                       task_queue=False)

        # Keep id for cleanup after
        self.workflow_ids.append(workflow.uuid)

        # Get parent object of the workflow we just ran
        # NOTE: ignore PEP8 here for None
        objects = WfeObject.query.filter(WfeObject.workflow_id == workflow.uuid,
                                         WfeObject.parent_id == None)

        self._check_workflow_execution(workflow, objects,
                                       initial_data, None)

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


TEST_SUITE = make_test_suite(TestWorkflowStart)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
