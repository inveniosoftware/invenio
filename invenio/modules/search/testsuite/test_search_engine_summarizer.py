# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2011, 2012, 2013 CERN.
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

"""Unit tests for the search engine summarizer."""

# Note: citation summary tests were moved to BibRank as part of the
# self-cite commit 1fcbed0ec34a9c31f8a727e21890c529d8222256.  Keeping
# this file here with empty test case set in order to overwrite any
# previously installed file.  Also, keeping TEST_SUITE empty so that
# `inveniocfg --run-unit-tests' would not complain.

from invenio.testsuite import make_test_suite, run_test_suite

TEST_SUITE = make_test_suite()

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
