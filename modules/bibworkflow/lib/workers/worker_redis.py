## This file is part of Invenio.
## Copyright (C) 2012 CERN.
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

from redis import Redis
from rq.decorators import job
from invenio.bibworkflow_worker_engine import runit, restartit

#FIXME: add configuration variables
redis_conn = Redis()


class worker_redis(object):
    def run(self, wname, data, external_save=None):
        """
        Registers runit function as a new task in RQ
        The delay method executes it asynchronously

        @wname: str, name of the workflow to be run
        @data: list of dictionaries, objects for the workflow
        """
        return job(queue='default', connection=redis_conn)(runit). \
            delay(wname, data, external_save=external_save)

    def restart(self, wid, data=None, restart_point="beginning",
                external_save=None):
        """
        Registers restartit as a new task in RQ
        The delay method executes it asynchronously

        @wname: str, name of the workflow to be run
        @data:  set to None if not given. In this case they are retrieved
        from the db
        list of dictionaries, objects for the workflow
        @restart_point: str, sets the restart point
        """
        return job(queue='default', connection=redis_conn)(restartit).\
            delay(wid, data=data, restart_point=restart_point,
                  external_save=external_save)
