# -*- coding: utf-8 -*-
# This file is part of Invenio.
# Copyright (C) 2013, 2014 CERN.
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

"""Generate minimal requirements from setup.py."""

from __future__ import print_function

import mock
import pkg_resources
import setuptools
import sys


if __name__ == '__main__':
    with mock.patch.object(setuptools, 'setup') as mock_setup:
        import setup  # pylint: disable=F401

    # called arguments are in `mock_setup.call_args`
    args, kwargs = mock_setup.call_args
    install_requires = kwargs.get('install_requires', [])

    for pkg in pkg_resources.parse_requirements(install_requires):
        if len(pkg.specs):
            if pkg.specs[0][0] == '>=':
                print("{0.project_name}=={0.specs[0][1]}".format(pkg))
            elif pkg.specs[0][0] == '>':
                print(
                    "{0.project_name} specify exact minimal version using "
                    "'>=' instead of '>'.".format(pkg), file=sys.stderr)
