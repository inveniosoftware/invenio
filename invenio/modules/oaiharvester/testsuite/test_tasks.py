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

"""Test for workflow tasks used by OAI harvester."""

from invenio.testsuite import make_test_suite, run_test_suite
from invenio.modules.workflows.testsuite.test_workflows import WorkflowTasksTestCase


class OAIHarvesterTasks(WorkflowTasksTestCase):

    """Class to test the harvesting related workflow tasks."""

    def setUp(self):
        """Setup tests."""
        self.create_registries()

    def tearDown(self):
        """Clean up created objects."""
        from invenio.modules.workflows.models import Workflow
        Workflow.get(Workflow.module_name == "unit_tests").delete()
        self.cleanup_registries()

    def test_filtering(self):
        """Test filtering functionality."""
        from ..tasks.harvesting import filtering_oai_pmh_identifier
        from invenio.modules.workflows.api import start
        from invenio.modules.workflows.models import BibWorkflowObject

        my_test_obj = BibWorkflowObject()
        my_test_obj.set_data("<record><test></test>"
                             "<identifier>identifier1</identifier></record>")
        my_test_obj.save()

        my_test_obj_b = BibWorkflowObject()
        my_test_obj_b.set_data(["<record><test></test><identifier>identifier2"
                                "</identifier></record>"])
        my_test_obj_b.save()
        engine = start("test_workflow_dummy",
                       my_test_obj,
                       module_name="unit_tests")

        # Initialize these attributes to simulate task running in workflows
        my_test_obj.data = my_test_obj.get_data()
        my_test_obj.extra_data = my_test_obj.get_extra_data()
        my_test_obj_b.data = my_test_obj_b.get_data()
        my_test_obj_b.extra_data = my_test_obj_b.get_extra_data()
        engine.extra_data = engine.get_extra_data()

        # Try to add an identifier
        self.assertTrue(filtering_oai_pmh_identifier(my_test_obj, engine))

        # Update engine with the added identifier
        engine.set_extra_data(engine.extra_data)
        engine.extra_data = engine.get_extra_data()

        # False because it is already added
        self.assertFalse(filtering_oai_pmh_identifier(my_test_obj, engine))
        engine.set_extra_data(engine.extra_data)
        engine.extra_data = engine.get_extra_data()

        self.assertTrue(filtering_oai_pmh_identifier(my_test_obj_b, engine))
        engine.set_extra_data(engine.extra_data)
        engine.extra_data = engine.get_extra_data()

        # False because it is already added
        self.assertFalse(filtering_oai_pmh_identifier(my_test_obj_b, engine))
        engine.set_extra_data(engine.extra_data)
        engine.extra_data = engine.get_extra_data()

    def test_init_harvesting(self):
        """Test harvesting."""
        from ..tasks.harvesting import init_harvesting
        from invenio.modules.workflows.api import start
        from invenio.modules.workflows.models import BibWorkflowObject

        my_test_obj = BibWorkflowObject()
        my_test_obj.set_data([2])
        my_test_obj.save()
        engine = start("test_workflow_dummy",
                       my_test_obj,
                       module_name="unit_tests")
        my_test_obj.data = my_test_obj.get_data()
        my_test_obj.extra_data = my_test_obj.get_extra_data()
        engine.set_extra_data_params(options={'test': True})
        engine.extra_data = engine.get_extra_data()
        init_harvesting(my_test_obj, engine)
        self.assertTrue(engine.get_extra_data()["options"]["test"])

TEST_SUITE = make_test_suite(OAIHarvesterTasks)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
