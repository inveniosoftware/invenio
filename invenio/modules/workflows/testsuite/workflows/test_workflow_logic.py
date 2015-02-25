# -*- coding: utf-8 -*-
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

""" Implements a workflow for testing."""

from ...tasks.logic_tasks import (end_for, foreach, simple_for, workflow_else,
                                  workflow_if, compare_logic,)
from ...tasks.sample_tasks import add_data

from ...tasks.workflows_tasks import interrupt_workflow

from ...tasks.marcxml_tasks import get_data, set_obj_extra_data_key


class test_workflow_logic(object):

    """Test workflow for unit-tests."""

    workflow = [
        foreach([0, 1, 4, 10], "step", True),
        [
            simple_for(0, 4, 1, "Iterator"),
            [
                add_data(1),
            ],
            end_for,
            workflow_if(compare_logic(get_data, 9, "gte")),
            [
                set_obj_extra_data_key("test", "gte9"),
                interrupt_workflow
            ],
            workflow_else,
            [
                set_obj_extra_data_key("test", "lt9"),
                interrupt_workflow
            ],
        ],
        end_for,
    ]
