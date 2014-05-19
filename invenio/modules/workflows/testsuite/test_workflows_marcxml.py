# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2014 CERN.
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

"""Test for marcxml tasks."""

from invenio.testsuite import make_test_suite, run_test_suite
from .test_workflows import WorkflowTasksTestCase


class WorkflowMarcXML(WorkflowTasksTestCase):

    """Class to test the marcxml tasks."""

    def setUp(self):
        """Setup tests."""
        self.create_registries()

    def tearDown(self):
        """ Clean up created objects."""
        from invenio.modules.workflows.utils import test_teardown
        test_teardown(self)
        self.cleanup_registries()

    def test_filtering(self):
        """ Test filtering functionnality."""
        from ..tasks.marcxml_tasks import filtering_oai_pmh_identifier
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
        engine = start("test_workflow_dummy", my_test_obj)

        my_test_obj.data = my_test_obj.get_data()
        my_test_obj_b.data = my_test_obj_b.get_data()
        engine.extra_data = engine.get_extra_data()
        self.assertEqual(filtering_oai_pmh_identifier(my_test_obj, engine),
                         True)
        engine.set_extra_data(engine.extra_data)
        engine.extra_data = engine.get_extra_data()
        self.assertEqual(filtering_oai_pmh_identifier(my_test_obj, engine),
                         False)
        engine.set_extra_data(engine.extra_data)
        engine.extra_data = engine.get_extra_data()
        self.assertEqual(filtering_oai_pmh_identifier(my_test_obj_b, engine),
                         True)
        engine.set_extra_data(engine.extra_data)
        engine.extra_data = engine.get_extra_data()
        self.assertEqual(filtering_oai_pmh_identifier(my_test_obj_b, engine),
                         False)
        engine.set_extra_data(engine.extra_data)
        engine.extra_data = engine.get_extra_data()
        self.assertEqual(filtering_oai_pmh_identifier(my_test_obj, engine),
                         False)

    def test_init_harvesting(self):
        """Test harvesting."""
        from ..tasks.marcxml_tasks import init_harvesting
        from invenio.modules.workflows.api import start
        from invenio.modules.workflows.models import BibWorkflowObject

        my_test_obj = BibWorkflowObject()
        my_test_obj.set_data([2])
        my_test_obj.save()
        engine = start("test_workflow_dummy", my_test_obj)
        my_test_obj.data = my_test_obj.get_data()
        my_test_obj.extra_data = my_test_obj.get_extra_data()
        engine.set_extra_data_params(options={'test': True})
        engine.extra_data = engine.get_extra_data()
        init_harvesting(my_test_obj, engine)
        self.assertEqual(engine.get_extra_data()["options"]["test"], True)

TEST_SUITE = make_test_suite(WorkflowMarcXML)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
