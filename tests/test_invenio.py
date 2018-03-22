# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Tests for Invenio Digital Library Framework."""

from __future__ import absolute_import, print_function


def test_version():
    """Test version import."""
    from invenio import __version__
    assert __version__
