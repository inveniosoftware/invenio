# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013 CERN.
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

from invenio.legacy.dbquery import run_sql

depends_on = ['invenio_release_1_1_0']

def info():
    return "Tables for new webauthorlist module"

def do_upgrade():
    run_sql("""
    CREATE TABLE IF NOT EXISTS `aulPAPERS` (
      `id` int(15) unsigned NOT NULL auto_increment,
      `id_user` int(15) unsigned NOT NULL,
      `title` varchar(255) NOT NULL,
      `collaboration` varchar(255) NOT NULL,
      `experiment_number` varchar(255) NOT NULL,
      `last_modified` int unsigned NOT NULL,
      PRIMARY KEY (`id`),
      INDEX(`id_user`)
    ) ENGINE=MyISAM;""")

    run_sql("""
    CREATE TABLE IF NOT EXISTS `aulREFERENCES` (
      `item` int(15) unsigned NOT NULL,
      `reference` varchar(120) NOT NULL,
      `paper_id` int(15) unsigned NOT NULL REFERENCES `aulPAPERS(id)`,
      PRIMARY KEY (`item`, `paper_id`),
      INDEX(`item`),
      INDEX(`paper_id`)
    ) ENGINE=MyISAM;""")

    run_sql("""
    CREATE TABLE IF NOT EXISTS `aulAFFILIATIONS` (
      `item` int(15) unsigned NOT NULL,
      `acronym` varchar(120) NOT NULL,
      `umbrella` varchar(120) NOT NULL,
      `name_and_address` varchar(255) NOT NULL,
      `domain` varchar(120) NOT NULL,
      `member` boolean NOT NULL,
      `spires_id` varchar(60) NOT NULL,
      `paper_id` int(15) unsigned NOT NULL REFERENCES `aulPAPERS(id)`,
      PRIMARY KEY (`item`, `paper_id`),
      INDEX(`item`),
      INDEX(`paper_id`),
      INDEX (`acronym`)
    ) ENGINE=MyISAM;""")

    run_sql("""
    CREATE TABLE IF NOT EXISTS `aulAUTHORS` (
      `item` int(15) unsigned NOT NULL,
      `family_name` varchar(255) NOT NULL,
      `given_name` varchar(255) NOT NULL,
      `name_on_paper` varchar(255) NOT NULL,
      `status` varchar(30) NOT NULL,
      `paper_id` int(15) unsigned NOT NULL REFERENCES `aulPAPERS(id)`,
      PRIMARY KEY (`item`, `paper_id`),
      INDEX(`item`),
      INDEX(`paper_id`)
    ) ENGINE=MyISAM;""")

    run_sql("""
    CREATE TABLE IF NOT EXISTS `aulAUTHOR_AFFILIATIONS` (
      `item` int(15) unsigned NOT NULL,
      `affiliation_acronym` varchar(120) NOT NULL,
      `affiliation_status` varchar(120) NOT NULL,
      `author_item` int(15) unsigned NOT NULL,
      `paper_id` int(15) unsigned NOT NULL REFERENCES `aulPAPERS(id)`,
      PRIMARY KEY (`item`, `author_item`, `paper_id`),
      INDEX(`item`),
      INDEX(`author_item`),
      INDEX(`paper_id`)
    ) ENGINE=MyISAM;""")

    run_sql("""
    CREATE TABLE IF NOT EXISTS `aulAUTHOR_IDENTIFIERS` (
      `item` int(15) unsigned NOT NULL,
      `identifier_number` varchar(120) NOT NULL,
      `identifier_name` varchar(120) NOT NULL,
      `author_item` int(15) unsigned NOT NULL,
      `paper_id` int(15) unsigned NOT NULL REFERENCES `aulPAPERS(id)`,
      PRIMARY KEY (`item`, `author_item`, `paper_id`),
      INDEX(`item`),
      INDEX(`author_item`),
      INDEX(`paper_id`)
    ) ENGINE=MyISAM;""")

def estimate():
    """  Estimate running time of upgrade in seconds (optional). """
    return 1
