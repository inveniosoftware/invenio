# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2014 CERN.
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

__revision__ = \
   "$Id$"

from invenio.config import \
     CFG_ELASTICSEARCH_LOGGING, \
     CFG_ELASTICSEARCH_INDEX_PREFIX, \
     CFG_ELASTICSEARCH_HOSTS, \
     CFG_ELASTICSEARCH_SUFFIX_FORMAT, \
     CFG_ELASTICSEARCH_MAX_QUEUE_LENGTH, \
     CFG_ELASTICSEARCH_FLUSH_INTERVAL

if CFG_ELASTICSEARCH_LOGGING:
    import lumberjack
    import logging
    import sys

def initialise_lumberjack():
    if not CFG_ELASTICSEARCH_LOGGING:
        return None
    config = lumberjack.get_default_config()
    config['index_prefix'] = CFG_ELASTICSEARCH_INDEX_PREFIX

    if CFG_ELASTICSEARCH_MAX_QUEUE_LENGTH == -1:
        config['max_queue_length'] = None
    else:
        config['max_queue_length'] = CFG_ELASTICSEARCH_MAX_QUEUE_LENGTH

    if CFG_ELASTICSEARCH_FLUSH_INTERVAL == -1:
        config['interval'] = None
    else:
        config['interval'] = CFG_ELASTICSEARCH_FLUSH_INTERVAL

    lj = lumberjack.Lumberjack(
        hosts=CFG_ELASTICSEARCH_HOSTS,
        config=config)

    handler = lj.get_handler(suffix_format=CFG_ELASTICSEARCH_SUFFIX_FORMAT)
    logging.getLogger('events').addHandler(handler)
    logging.getLogger('events').setLevel(logging.INFO)

    logging.getLogger('lumberjack').addHandler(
        logging.StreamHandler(sys.stderr))
    logging.getLogger('lumberjack').setLevel(logging.ERROR)

    return lj

LUMBERJACK = initialise_lumberjack()

def register_schema(*args, **kwargs):
    if not CFG_ELASTICSEARCH_LOGGING:
        return None
    return LUMBERJACK.register_schema(*args, **kwargs)
