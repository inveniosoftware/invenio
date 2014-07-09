# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2011, 2014 CERN.
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

"""WebMessage Forms"""

from invenio.base.i18n import _
from invenio.modules.search.models import get_pbx_pos
from invenio.utils.forms import InvenioBaseForm
from wtforms import TextField, HiddenField, SelectField


class CollectionForm(InvenioBaseForm):
    id = HiddenField()
    name = TextField(_('Name'))
    dbquery = TextField(_('Query'))


def TranslationsForm(language_list_long, values):

    class _TranslationsForm(InvenioBaseForm):
        collection_id = HiddenField()

    for (lang, lang_long) in language_list_long:
        setattr(_TranslationsForm, lang,
                TextField(_(lang_long),
                          default=values.get(lang, '')))

    return _TranslationsForm


class PortalBoxForm(InvenioBaseForm):
    id = HiddenField()
    postion = SelectField(u'Select Position', get_pbx_pos())
