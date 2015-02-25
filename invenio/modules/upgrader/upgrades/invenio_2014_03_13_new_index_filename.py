# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2012, 2013 CERN.
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


depends_on = ['invenio_2013_10_18_new_index_filetype']

def info():
    return "New index filename."


def do_upgrade():
    pass


def do_upgrade_atlantis():
    index_id = 28
    run_sql("""
            CREATE TABLE IF NOT EXISTS idxWORD%02dF (
              id mediumint(9) unsigned NOT NULL auto_increment,
              term varchar(50) default NULL,
              hitlist longblob,
              PRIMARY KEY  (id),
              UNIQUE KEY term (term)
            ) ENGINE=MyISAM;
            """ % index_id)
    run_sql("""
            CREATE TABLE IF NOT EXISTS idxWORD%02dR (
              id_bibrec mediumint(9) unsigned NOT NULL,
              termlist longblob,
              type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
              PRIMARY KEY (id_bibrec,type)
            ) ENGINE=MyISAM;
            """ % index_id)
    run_sql("""
            CREATE TABLE IF NOT EXISTS idxPAIR%02dF (
              id mediumint(9) unsigned NOT NULL auto_increment,
              term varchar(100) default NULL,
              hitlist longblob,
              PRIMARY KEY  (id),
              UNIQUE KEY term (term)
            ) ENGINE=MyISAM;
            """ % index_id)
    run_sql("""
            CREATE TABLE IF NOT EXISTS idxPAIR%02dR (
              id_bibrec mediumint(9) unsigned NOT NULL,
              termlist longblob,
              type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
              PRIMARY KEY (id_bibrec,type)
            ) ENGINE=MyISAM;
            """ % index_id)
    run_sql("""
            CREATE TABLE IF NOT EXISTS idxPHRASE%02dF (
              id mediumint(9) unsigned NOT NULL auto_increment,
              term text default NULL,
              hitlist longblob,
              PRIMARY KEY  (id),
              KEY term (term(50))
            ) ENGINE=MyISAM;
            """ % index_id)
    run_sql("""
            CREATE TABLE IF NOT EXISTS idxPHRASE%02dR (
              id_bibrec mediumint(9) unsigned NOT NULL,
              termlist longblob,
              type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
              PRIMARY KEY (id_bibrec,type)
            ) ENGINE=MyISAM;
            """ % index_id)
    run_sql("""INSERT INTO idxINDEX VALUES (28,'filename','This index contains names of all files attached to the record.', '0000-00-00 00:00:00', '', 'native', '', 'No', 'No', 'No', 'BibIndexFilenameTokenizer')""")
    run_sql("""INSERT INTO field VALUES (43,'file name', 'filename')""")
    run_sql("""INSERT INTO idxINDEX_field (id_idxINDEX, id_field) VALUES (28,43)""")

def estimate():
    return 1

def pre_upgrade():
    pass

def post_upgrade():
    pass
