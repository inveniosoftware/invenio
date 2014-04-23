# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2011 CERN.
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
WebAuthorProfile database interface
"""

from invenio.dbquery import run_sql
from invenio.webauthorprofile_config import CFG_WEBAUTHORPROFILE_CACHE_EXPIRED_DELAY_BIBSCHED


def _create_db_tables():
    """
    Temporary method to create/reset cache tables
    (sql code will be moved to the official sql install file).
    """
    run_sql("""CREATE TABLE IF NOT EXISTS `wapCACHE` (
          `object_name` varchar(120) NOT NULL,
          `object_key` varchar(120) NOT NULL,
          `object_value` longblob,
          `object_status` varchar(120),
          `last_updated` datetime NOT NULL,
          PRIMARY KEY  (`object_name`,`object_key`),
          INDEX `name-b` (`object_name`),
          INDEX `key-b` (`object_key`),
          INDEX `last_updated-b` (`last_updated`)
          ) ENGINE=MyISAM;
        """)

def get_cache_oldest_date(key):
    """ Returns the oldest date for a given object_key. """
    date = run_sql("select min(last_updated) from wapCACHE where object_key=%s and object_status <> 'Expired'",
                    (key,))
    if date:
        return date[0][0]
    else:
        return None

def get_cached_element(name, key):
    """
    Returns a cached element as {'value':object_value, 'upToDate':bool, 'last_updated':last_updated,
                                 'present':bool, 'precached':bool}.
    """
    el = run_sql("select object_value, object_status, last_updated from wapCACHE "
             "where object_name=%s and object_key=%s",
             (str(name), str(key)))
    if len(el) == 0:
        return {'value':'', 'upToDate':False, 'last_updated':None, 'present':False, 'precached':False}
    else:
        status = True
        precached = False
        if el[0][1] != 'UpToDate':
            status = False
        if el[0][1] == 'Precached':
            precached = True
        return {'value':el[0][0], 'upToDate':status, 'last_updated':el[0][2], 'present':True, 'precached':precached}

def precache_element(name, key):
    """ Updates the last_updated flag of a cache to prevent parallel recomputation of the same cache. """
    run_sql("insert into wapCACHE (object_name,object_key,last_updated,object_status) values (%s,%s,now(),%s) "
            "on duplicate key update last_updated=now(),object_status=%s" ,
            (str(name), str(key), 'Precached', 'Precached'))

def cache_element(name, key, value):
    """ Insert an element into cache or update already present element. """
    run_sql("insert into wapCACHE (object_name,object_key,object_value,object_status,last_updated) values (%s,%s,%s,%s,now()) "
            "on duplicate key update object_value=%s,last_updated=now(),object_status=%s" ,
            (str(name), str(key), str(value), 'UpToDate', str(value), 'UpToDate'))

def expire_cache_element(name, key):
    """ Sets cache element status to 'Expired'. """
    run_sql("update wapCACHE set object_status=%s where "
            "object_name=%s and object_key=%s", ('Expired', str(name), str(key)))

def expire_all_cache_for_person(person_id):
    """ Expires all caches for person n.canonical.1 """
    run_sql("DELETE FROM wapCACHE WHERE object_key=%s", ('pid:' + str(person_id),))

def get_expired_person_ids(expire_delay_days=CFG_WEBAUTHORPROFILE_CACHE_EXPIRED_DELAY_BIBSCHED):
    """ Returns pids with expired caches. """
    keys = run_sql("select object_key from wapCACHE where object_status=%s or last_updated < "
                   "timestampadd(day, -%s, now())", ('Expired', expire_delay_days))
    keys = [int(x[0].split(':')[1]) for x in set(keys) if ':' in x[0]]
    return keys

