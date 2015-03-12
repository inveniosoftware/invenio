# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015 CERN.
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

"""Define exceptions that follows deprecation policy.

A minor release version (``A.B``) may deprecate certain features from previous
releases. If a feature is deprecated in version ``A.B`` it will continue to
work in version ``A.B`` and ``A.(B+1)`` but raise warnings. It will be
completely removed in version ``A.(B+2)``.

Example:
- Feature X is mark in version *2.0* as deprecated. The feature will still
  work, but it will issue the silent warning ``RemovedInInvenio22Warning``
  (`PendingDeprecationWarning`).
- Version *2.1* still contains the feature, but the warning
  ``RemovedInInvenio22Warning`` is now loud by default (`DeprecationWarning`).
- Version *2.2* will completely remove the feature.
"""


class RemovedInInvenio22Warning(PendingDeprecationWarning):

    """Mark feature that will be removed in current version +0.2."""


class RemovedInInvenio21Warning(DeprecationWarning):

    """Mark feature that will be removed in current version +0.1."""
