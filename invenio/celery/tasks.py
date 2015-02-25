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
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA

from invenio.celery import celery


@celery.task
def invenio_version():
    """ Task that will return the current running Invenio version """
    from invenio.base.globals import cfg
    return cfg['CFG_VERSION']


@celery.task
def invenio_db_test(num):
    """ Task will execute a simple query in the database"""
    from invenio.ext.sqlalchemy import db
    return db.engine.execute("select %s" % int(num)).scalar()
