# -*- coding: utf-8 -*-
#
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

from .receivers import post_handler_database_create
from invenio.base.scripts.database import create as database_create
from invenio.base.scripts.database import recreate as database_recreate
from invenio.base.scripts.demosite import populate as demosite_populate
from invenio.base.signals import post_command

post_command.connect(post_handler_database_create, sender=database_create)
post_command.connect(post_handler_database_create, sender=database_recreate)
post_command.connect(post_handler_database_create, sender=demosite_populate)
