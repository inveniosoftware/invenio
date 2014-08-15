# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

from invenio.dbquery import run_sql

depends_on = ['invenio_release_1_1_0']


def info():
    """Upgrader info."""
    return ("Create a new table to be used for relating comment ids and "
            "their record ids with bibdoc ids")


def do_upgrade():
    """Perform upgrade."""
    run_sql("""
        CREATE TABLE IF NOT EXISTS `cmtRECORDCOMMENT_bibdoc` (
        `id_record` mediumint(8) unsigned NOT NULL,
        `id_comment` int(15) unsigned NOT NULL,
        `id_bibdoc` mediumint(9) unsigned NOT NULL,
        `version` tinyint(4) unsigned NOT NULL,
        `format` varchar(50) NOT NULL,
        KEY `id_record` (`id_record`),
        KEY `id_comment` (`id_comment`),
        KEY `id_bibdoc` (`id_bibdoc`),
        KEY `version` (`version`),
        KEY `format` (`format`),
        PRIMARY KEY (`id_record`,`id_comment`,`id_bibdoc`,`version`,`format`),
        CONSTRAINT `cmtRECORDCOMMENT_bibdoc_ibfk_1`
            FOREIGN KEY (`id_record`)
            REFERENCES `bibrec` (`id`),
        CONSTRAINT `cmtRECORDCOMMENT_bibdoc_ibfk_2`
            FOREIGN KEY (`id_comment`)
            REFERENCES `cmtRECORDCOMMENT` (`id`),
        CONSTRAINT `cmtRECORDCOMMENT_bibdoc_ibfk_3`
            FOREIGN KEY (`id_bibdoc`,`version`,`format`)
            REFERENCES `bibdocfsinfo` (`id_bibdoc`,`version`,`format`)
        ) ENGINE=MyISAM;
        """)


def estimate():
    """  Estimate running time of upgrade in seconds (optional). """
    return 1
