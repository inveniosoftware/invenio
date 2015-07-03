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

"""Unit tests for workflows models."""

from __future__ import absolute_import

from invenio.ext.sqlalchemy import db
from invenio.testsuite import InvenioTestCase, make_test_suite, run_test_suite


class TestWorkflowModels(InvenioTestCase):

    """Test meant for testing the models available."""

    def setUp(self):
        """Setup tests."""
        from invenio.modules.workflows.models import BibWorkflowObject, \
            Workflow
        from uuid import uuid1 as new_uuid

        self.workflow = Workflow(name='test_workflow', uuid=new_uuid(),
                                 id_user=0, module_name="Unknown")
        self.bibworkflowobject = BibWorkflowObject(workflow=self.workflow)

        self.create_objects([self.workflow, self.bibworkflowobject])

    def tearDown(self):
        """Clean up tests."""
        self.delete_objects([self.workflow, self.bibworkflowobject])

    def test_deleting_workflow(self):
        """Test deleting workflow."""
        from invenio.modules.workflows.models import BibWorkflowObject, \
            Workflow
        bwo_id = self.bibworkflowobject.id

        # delete workflow
        Workflow.delete(self.workflow.uuid)

        # assert bibworkflowobject is deleted
        self.assertFalse(
            db.session.query(
                BibWorkflowObject.query.filter(
                    BibWorkflowObject.id == bwo_id).exists()).scalar())

    def test_deleting_bibworkflowobject(self):
        """Test deleting workflowobject."""
        from invenio.modules.workflows.models import Workflow
        w_uuid = self.workflow.uuid

        # delete bibworkflowobject
        self.bibworkflowobject.delete(self.bibworkflowobject.id)

        # assert workflow is not deleted
        self.assertTrue(
            db.session.query(
                Workflow.query.filter(
                    Workflow.uuid == w_uuid).exists()).scalar())


TEST_SUITE = make_test_suite(TestWorkflowModels)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
