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
## 59 Temple Place, Suite 330, Boston, MA 021111307, USA.

from invenio.legacy.bibsched.bibtask import (write_message,
                                             task_get_task_param
                                             )


def write_something_bibsched(messagea="This is the default message"):
    """
    This function allows to send a message to bibsched...
    This messages will be store into log.
    """
    def _write_something_bibsched(obj, eng):

        if isinstance(messagea, basestring):
            write_message(messagea)
            return None

        if not isinstance(messagea, list):
            if callable(messagea):
                write_message(messagea(obj, eng))
            return None

        if len(messagea) > 0:
            temp = ""
            for I in messagea:
                if callable(I):
                    temp += str(I(obj, eng))
                elif isinstance(I, basestring):
                    temp += I
            write_message(temp)
            return None

    return _write_something_bibsched


def get_and_save_task_parameter(obj, eng):
    eng.log.error("trying to retrieve param")
    eng.log.error(str(task_get_task_param(None)))
    eng.log.error("END OF RETRIEVING")

#def task_update_progress(msg):
#    def _task_update_progress(obj, eng):
#        """Updates progress information in the BibSched task table."""
#        write_message("Updating task progress to %s." % msg, verbose=9)
#        if "task_id" in _TASK_PARAMS:
#            return run_sql("UPDATE schTASK SET progress=%s where id=%s",
#                (msg, _TASK_PARAMS["task_id"]))
#
#
#def task_update_status(val):
#    def _task_update_status(obj, eng):
#        """Updates status information in the BibSched task table."""
#        write_message("Updating task status to %s." % val, verbose=9)
#        if "task_id" in _TASK_PARAMS:
#            return run_sql("UPDATE schTASK SET status=%s where id=%s",
#                (val, _TASK_PARAMS["task_id"]))
#

