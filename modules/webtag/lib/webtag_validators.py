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

"""WebTag Forms"""

from invenio.webtag_config import \
    CFG_WEBTAG_LAST_MYSQL_CHARACTER

from invenio.webtag_config import \
    CFG_WEBTAG_NAME_MAX_LENGTH

from invenio.webinterface_handler_flask_utils import _

from invenio.wtforms_utils import InvenioBaseForm
from invenio.webuser_flask import current_user

from wtforms import IntegerField, HiddenField, TextField, validators

# Models
from invenio.sqlalchemyutils import db
from invenio.webtag_model import WtgTAG, wash_tag_silent, wash_tag_blocking

