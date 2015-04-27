# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014, 2015 CERN.
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

"""Define caches for sorter module."""

from invenio.legacy.miscutil.data_cacher import DataCacher
from invenio.utils.datastructures import LazyDict

from .models import BsrMETHOD


class BibSortDataCacher(DataCacher):

    """Cache holding all structures created by sorter."""

    def __init__(self, method_name):
        """Initialize data cacher for given method."""
        self.method_name = method_name

        def cache_filler():
            """Return data to populate cache."""
            method = BsrMETHOD.query.filter_by(name=self.method_name).first()
            return dict(method.get_cache()) if method is not None else {}

        def timestamp_verifier():
            """Return string representing last update datetime."""
            return BsrMETHOD.timestamp_verifier(self.method_name).strftime(
                "%Y-%m-%d %H:%M:%S")

        DataCacher.__init__(self, cache_filler, timestamp_verifier)


SORTING_METHODS = LazyDict(BsrMETHOD.get_sorting_methods)

CACHE_SORTED_DATA = LazyDict(lambda: dict([
    (sorting_method, BibSortDataCacher(sorting_method))
    for sorting_method in SORTING_METHODS
]))
