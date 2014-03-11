# -*- coding: utf-8 -*-
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

import logging

from invenio.ext.sqlalchemy import db


def get_logger(logger_name, db_handler_obj,
               level=10, **kwargs):
    """
    Will initialize and return a Python logger object with
    handlers to output logs in sys.stderr as well as the
    datebase.
    """
    logging.basicConfig(level=level)

    # Get a basic logger object
    logger = logging.getLogger(logger_name)

    # Create formatter and add it to the handlers
    formatter = logging.Formatter('%(levelname)s %(asctime)s %(name)s    %(message)s')

    db_handler_obj.setFormatter(formatter)
    db_handler_obj.setLevel(level)
    should_we_add = True
    for handler in logger.handlers:
        if handler.name == db_handler_obj.name:
            should_we_add = False
    if should_we_add:
        logger.addHandler(db_handler_obj)
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        stream_handler.setLevel(level)
        logger.addHandler(stream_handler)

    # Let's not propagate to root logger..
    logger.propagate = 0

    # FIXME: loglevels are simply overwritten somewhere in Celery
    #        even if Celery is not being "used".
    #
    #        This means log.DEBUG is NOT working at the moment!
    logger.setLevel(level)

    # Add any kwargs to extra parameter and return logger
    wrapped_logger = BibWorkflowLogAdapter(logger, kwargs)
    return wrapped_logger


class BibWorkflowLogHandler(logging.Handler):
    """
    Implements a handler for logging to database
    """

    def __init__(self, model, id_name):

        logging.Handler.__init__(self)

        self.model = model
        self.id_name = id_name



    def emit(self, record):
        log_obj = self.model(id_object=getattr(record.obj, self.id_name),
                             log_type=record.levelno,
                             message=record.msg)
        db.session.add(log_obj)
        db.session.commit()


class BibWorkflowLogAdapter(logging.LoggerAdapter):
    """
    This example adapter expects the passed in dict-like object to have a
    'obj' key, whose value in brackets is used during logging.
    """

    def process(self, msg, kwargs):
        kwargs['extra'] = self.extra
        return msg, kwargs
