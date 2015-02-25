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

depends_on = ['invenio_2013_08_20_bibauthority_updates']

def info():
    return """Introduces new index: itemcount"""


def do_upgrade():
    pass


def do_upgrade_atlantis():
    #first step: create tables
    run_sql("""CREATE TABLE IF NOT EXISTS idxWORD24F (
                 id mediumint(9) unsigned NOT NULL auto_increment,
                 term varchar(50) default NULL,
                 hitlist longblob,
                 PRIMARY KEY  (id),
                 UNIQUE KEY term (term)
               ) ENGINE=MyISAM; """)
    run_sql("""CREATE TABLE IF NOT EXISTS idxWORD24R (
                 id_bibrec mediumint(9) unsigned NOT NULL,
                 termlist longblob,
                 type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
                 PRIMARY KEY (id_bibrec,type)
               ) ENGINE=MyISAM;""")

    run_sql("""CREATE TABLE IF NOT EXISTS idxPAIR24F (
                 id mediumint(9) unsigned NOT NULL auto_increment,
                 term varchar(100) default NULL,
                 hitlist longblob,
                 PRIMARY KEY  (id),
                 UNIQUE KEY term (term)
               ) ENGINE=MyISAM;""")
    run_sql("""CREATE TABLE IF NOT EXISTS idxPAIR24R (
                 id_bibrec mediumint(9) unsigned NOT NULL,
                 termlist longblob,
                 type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
                 PRIMARY KEY (id_bibrec,type)
               ) ENGINE=MyISAM;""")


    run_sql("""CREATE TABLE IF NOT EXISTS idxPHRASE24F (
                 id mediumint(9) unsigned NOT NULL auto_increment,
                 term text default NULL,
                 hitlist longblob,
                 PRIMARY KEY  (id),
                 KEY term (term(50))
               ) ENGINE=MyISAM;""")
    run_sql("""CREATE TABLE IF NOT EXISTS idxPHRASE24R (
                 id_bibrec mediumint(9) unsigned NOT NULL,
                 termlist longblob,
                 type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
                 PRIMARY KEY (id_bibrec,type)
               ) ENGINE=MyISAM;""")
    #second step: fill in idxINDEX, idxINDEX_field, field tables
    run_sql("""INSERT INTO field VALUES (37,'item count','itemcount')""")
    run_sql("""INSERT INTO idxINDEX VALUES (24,'itemcount','This index contains number of copies of items in the library.','0000-00-00 00:00:00', '', 'native', '','No','No','No', 'BibIndexItemCountTokenizer')""")
    run_sql("""INSERT INTO idxINDEX_field (id_idxINDEX, id_field) VALUES (24,37)""")


def estimate():
    return 1


def pre_upgrade():
    pass


def post_upgrade():
    pass
