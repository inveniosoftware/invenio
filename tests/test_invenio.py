# SPDX-FileCopyrightText: 2015-2018 CERN.
# SPDX-License-Identifier: MIT

"""Tests for Invenio Digital Library Framework."""

from __future__ import absolute_import, print_function


def test_version():
    """Test version import."""
    from invenio import __version__
    assert __version__
