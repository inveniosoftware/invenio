# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2013 CERN.
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


"""
This module makes all WTForms fields available in WebDeposit, and ensure that
they subclass WebDepositField for added functionality

The code is basically identical to importing all the WTForm fields and for each
field make a subclass according to the pattern (using FloatField as
an example)::

    class FloatField(WebDepositField, wtforms.FloatField):
        pass
"""

import wtforms
from invenio.webdeposit_field import WebDepositField


__all__ = []

for attr_name in dir(wtforms):
    attr = getattr(wtforms, attr_name)
    try:
        if issubclass(attr, wtforms.Field):
            # From a WTForm field, dynamically create a new class the same name as
            # the WTForm field (inheriting from WebDepositField() and the WTForm
            # field itself). Store the new class in the current module with the
            # same name as the WTForms.
            #
            # For further information please see Python reference documne for
            # globals() and type() functions.
            globals()[attr_name] = type(str(attr_name), (WebDepositField, attr), {})
            __all__.append(attr_name)
    except TypeError:
        pass
