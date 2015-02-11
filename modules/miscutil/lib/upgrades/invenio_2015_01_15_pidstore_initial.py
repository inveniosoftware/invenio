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

import warnings

from invenio.dbquery import run_sql


depends_on = []


def info():
    return "Initial creation of tables for pidstore module."


def do_upgrade():
    if not run_sql("SHOW TABLES LIKE 'pidSTORE'"):
        run_sql(
            "CREATE TABLE `pidSTORE` ("
            "`id` int(15) unsigned NOT NULL AUTO_INCREMENT,"
            "`pid_type` varchar(6) NOT NULL,"
            "`pid_value` varchar(255) NOT NULL,"
            "`pid_provider` varchar(255) NOT NULL,"
            "`status` char(1) NOT NULL,"
            "`object_type` varchar(3) DEFAULT NULL,"
            "`object_value` varchar(255) DEFAULT NULL,"
            "`created` datetime NOT NULL,"
            "`last_modified` datetime NOT NULL,"
            "PRIMARY KEY (`id`),"
            "UNIQUE KEY `uidx_type_pid` (`pid_type`,`pid_value`),"
            "KEY `idx_object` (`object_type`,`object_value`),"
            "KEY `idx_status` (`status`)"
            ") ENGINE=MyISAM;"
        )
    else:
        warnings.warn("*** Creation of 'pidSTORE' table skipped! ***")

    if not run_sql("SHOW TABLES LIKE 'pidLOG'"):
        run_sql(
            "CREATE TABLE `pidLOG` ("
            "`id` int(15) unsigned NOT NULL AUTO_INCREMENT,"
            "`id_pid` int(15) unsigned DEFAULT NULL,"
            "`timestamp` datetime NOT NULL,"
            "`action` varchar(10) NOT NULL,"
            "`message` text NOT NULL,"
            "PRIMARY KEY (`id`),"
            "KEY `id_pid` (`id_pid`),"
            "KEY `idx_action` (`action`),"
            "CONSTRAINT `pidlog_ibfk_1` FOREIGN KEY (`id_pid`) REFERENCES `pidSTORE` (`id`)"
            ") ENGINE=MYISAM;"
        )
    else:
        warnings.warn("*** Creation of 'pidLOG' table skipped! ***")


def estimate():
    """Estimate running time of upgrade in seconds (optional)."""
    return 1


def pre_upgrade():
    """Run pre-upgrade checks (optional)."""
    tables = ["pidSTORE", "pidLOG"]
    for table in tables:
        if run_sql("SHOW TABLES LIKE '%s'", (table, )):
            warnings.warn(
                "*** Table {0} already exists! *** "
                "This upgrade will *NOT* create the new table.".format(table)
            )


def post_upgrade():
    """Run post-upgrade checks (optional)."""
    pass
