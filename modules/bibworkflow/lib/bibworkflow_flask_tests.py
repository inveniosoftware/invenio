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

import unittest

from invenio.testutils import make_test_suite, run_test_suite
from invenio.bibworkflow_api import run
from invenio.sqlalchemyutils import db


class TestWorkflowStart(unittest.TestCase):
    """Tests for BibWorkflow API."""

    def test_workflow_first_run(self):
        """Tests running workflow with new data"""
        from invenio.bibworkflow_model import WfeObject, Workflow
        workflow1 = run("test1", [{"a":20}], task_queue=False)

        objects1 = \
            WfeObject.query. \
            filter(WfeObject.workflow_id == workflow1.uuid,
                   WfeObject.parent_id is None)

        wfeobject1 = WfeObject({"a": 20}, workflow1.uuid, 0)
        wfeobject2 = WfeObject({"a": 20}, workflow1.uuid, 1, objects1[0].id)

        ### check first object
        self.assertEqual(objects1[0], wfeobject1)
        self.assertEqual(objects1[0].child_objects[0], wfeobject2)

        WfeObject.query.filter(WfeObject.workflow_id == workflow1.uuid).delete()
        Workflow.query.filter(wfeobject1.workflowid == workflow1.uuid).delete()
        db.session.commit()
        print "Test objects deleted from database."

    def test_workflow_complex_run(self):
        """Tests running workflow with complex data"""

        workflow = run("test2", [{"a": 1}, {"a": "wwww"}, {"a": 10}],
                       task_queue=False)

        objects = WfeObject.query.filter(WfeObject.workflow_id == workflow.uuid,
                                         WfeObject.parent_id is None)
        wfeobject3 = WfeObject({"a": 1}, workflow.uuid,0)
        wfeobject4 = WfeObject({"a": 21}, workflow.uuid, 1, objects[0].id)

        wfeobject5 = WfeObject({"a": "wwww"}, workflow.uuid, 0)
        wfeobject6 = WfeObject({"a": "wwww"}, workflow.uuid, 2, objects[1].id)

        wfeobject7 = WfeObject({"a": 10}, workflow.uuid, 0)
        wfeobject8 = WfeObject({"a": 30}, workflow.uuid, 1, objects[2].id)

        ### check first object
        print "Checking first object"

        self.assertEqual(objects[0], wfeobject3)
        self.assertEqual(objects[0].child_objects[0], wfeobject4)

        print "Checking secound object"
        self.assertEqual(objects[1], wfeobject5)
        self.assertEqual(objects[1].child_objects[0], wfeobject6)

        print "Checking third object"
        self.assertEqual(objects[2], wfeobject7)
        self.assertEqual(objects[2].child_objects[0], wfeobject8)

        WfeObject.query.filter(WfeObject.workflow_id == workflow.uuid).delete()
        Workflow.query.filter(workflow.uuid == workflow.uuid).delete()
        db.session.commit()
        print "Test objects deleted from database."

TEST_SUITE = make_test_suite(TestWorkflowStart)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE, warn_user=True)
