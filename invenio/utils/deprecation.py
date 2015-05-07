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

"""Invenio deprecation policy.

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

Fast track deprecation
----------------------
Poorly tested, non-core and little used features for which alternatives already
exists in Invenio may opt to use fast track deprecation. If a feature is
fast track deprecated in version ``A.B`` it will continue to work in version
``A.B`` but raise loud warnings. It will be completely removed in version
``A.(B+1)``.

Fast track deprecation is only to be used in exceptional cases for features
that essentially nobody uses. In addition, if a fast track deprecation after
being accepted is found to have significant impact on a minority of the
community, it may be postponed to follow the standard deprecation policy.

How to deprecate a feature
--------------------------
1. Open a RFC issue on GitHub to allow discussion of the proposed
feature deprecation.

2. Issue a deprecation warning for the feature in the latest ``maint``
branch.

.. code-block:: python

    import warnings
    from invenio.utils.deprecation import RemovedInInvenio22Warning

    def old_method(a, b):
        warnings.warn(
            "Use of old_method is deprecated. Please use new_method instead.",
            RemovedInInvenio22Warning
        )
        # ...

If desired, you may already rewrite the body of ``old_method()``, but it must
be API backward compatible so that existing code does not break. Please start
fixing all places ``old_method`` is used, so that it can be easily removed
once Invenio v2.1 has been released.
"""

import warnings

from functools import wraps


class RemovedInInvenio23Warning(PendingDeprecationWarning):

    """Mark feature that will be removed in Invenio version 2.3."""


class RemovedInInvenio22Warning(DeprecationWarning):

    """Mark feature that will be removed in Invenio version 2.2."""


# Improved version of http://code.activestate.com/recipes/391367-deprecated/
def deprecated(message, category):
    def wrap(func=None):
        """Decorator which can be used to mark functions as deprecated.

        :param message: text to include in the warning
        :param category: warning category
        """
        @wraps(func)
        def new_func(*args, **kwargs):
            warnings.warn(message, category, stacklevel=3)
            return func(*args, **kwargs)
        return new_func
    return wrap
