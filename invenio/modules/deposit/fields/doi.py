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

from wtforms import TextField
from invenio.modules.deposit.field_base import WebDepositField
from invenio.webdeposit_validation_utils import doi_syntax_validator
from invenio.webdeposit_filter_utils import strip_prefixes, strip_string
from invenio.webdeposit_processor_utils import datacite_lookup

__all__ = ['DOIField']


def missing_doi_warning(dummy_form, field, dummy_submit=False):
    """
    Field processor, checking for existence of a DOI, and otherwise
    asking people to provide it.
    """
    if not field.errors and not field.data:
        field.add_message("Please provide a DOI if possible.", state="warning")
        raise StopIteration()


class DOIField(WebDepositField, TextField):
    def __init__(self, **kwargs):
        defaults = dict(
            icon='icon-barcode',
            validators=[
                doi_syntax_validator,
            ],
            filters=[
                strip_string,
                strip_prefixes("doi:", "http://dx.doi.org/"),
            ],
            processors=[
                missing_doi_warning,
                datacite_lookup(display_info=True),
            ],
            placeholder="e.g. 10.1234/foo.bar...",
        )
        defaults.update(kwargs)
        super(DOIField, self).__init__(**defaults)
