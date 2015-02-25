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

depends_on = ['invenio_2013_03_29_idxINDEX_stopwords_update']

def info():
    return """Introduces bibauthority module. Adds:
              -> new indexes:
                         authorityauthor
                         authoritysubject
                         authorityjournal
                         authorityinstitution
              -> new fields:
                         authorityauthor
                         authoritysubject
                         authorityjournal
                         authorityinstitution
              -> new tags:
                         authority: main personal name
                         authority: alternative personal name
                         authority: personal name from other record
                         authority: organization main name'
                         organization alternative name
                         organization main from other record
                         authority: uniform title
                         authority: uniform title alternatives
                         authority: uniform title from other record
                         authority: subject from other record
                         authority: subject alternative name
                         authority: subject main name
            """


def do_upgrade():
    pass


def do_upgrade_atlantis():
    #first step: create tables
    run_sql("""CREATE TABLE IF NOT EXISTS idxWORD20F (
                 id mediumint(9) unsigned NOT NULL auto_increment,
                 term varchar(50) default NULL,
                 hitlist longblob,
                 PRIMARY KEY  (id),
                 UNIQUE KEY term (term)
               ) ENGINE=MyISAM; """)
    run_sql("""CREATE TABLE IF NOT EXISTS idxWORD20R (
                 id_bibrec mediumint(9) unsigned NOT NULL,
                 termlist longblob,
                 type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
                 PRIMARY KEY (id_bibrec,type)
               ) ENGINE=MyISAM;""")

    run_sql("""CREATE TABLE IF NOT EXISTS idxWORD21F (
                 id mediumint(9) unsigned NOT NULL auto_increment,
                 term varchar(50) default NULL,
                 hitlist longblob,
                 PRIMARY KEY  (id),
                 UNIQUE KEY term (term)
               ) ENGINE=MyISAM;""")
    run_sql("""CREATE TABLE IF NOT EXISTS idxWORD21R (
                 id_bibrec mediumint(9) unsigned NOT NULL,
                 termlist longblob,
                 type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
                 PRIMARY KEY (id_bibrec,type)
               ) ENGINE=MyISAM;""")

    run_sql("""CREATE TABLE IF NOT EXISTS idxWORD22F (
                 id mediumint(9) unsigned NOT NULL auto_increment,
                 term varchar(50) default NULL,
                 hitlist longblob,
                 PRIMARY KEY  (id),
                 UNIQUE KEY term (term)
               ) ENGINE=MyISAM;""")
    run_sql("""CREATE TABLE IF NOT EXISTS idxWORD22R (
                 id_bibrec mediumint(9) unsigned NOT NULL,
                 termlist longblob,
                 type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
                 PRIMARY KEY (id_bibrec,type)
               ) ENGINE=MyISAM;""")

    run_sql("""CREATE TABLE IF NOT EXISTS idxWORD23F (
                 id mediumint(9) unsigned NOT NULL auto_increment,
                 term varchar(50) default NULL,
                 hitlist longblob,
                 PRIMARY KEY  (id),
                 UNIQUE KEY term (term)
               ) ENGINE=MyISAM;""")
    run_sql("""CREATE TABLE IF NOT EXISTS idxWORD23R (
                 id_bibrec mediumint(9) unsigned NOT NULL,
                 termlist longblob,
                 type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
                 PRIMARY KEY (id_bibrec,type)
               ) ENGINE=MyISAM;""")


    run_sql("""CREATE TABLE IF NOT EXISTS idxPAIR20F (
                 id mediumint(9) unsigned NOT NULL auto_increment,
                 term varchar(100) default NULL,
                 hitlist longblob,
                 PRIMARY KEY  (id),
                 UNIQUE KEY term (term)
               ) ENGINE=MyISAM;""")
    run_sql("""CREATE TABLE IF NOT EXISTS idxPAIR20R (
                 id_bibrec mediumint(9) unsigned NOT NULL,
                 termlist longblob,
                 type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
                 PRIMARY KEY (id_bibrec,type)
               ) ENGINE=MyISAM;""")

    run_sql("""CREATE TABLE IF NOT EXISTS idxPAIR21F (
                 id mediumint(9) unsigned NOT NULL auto_increment,
                 term varchar(100) default NULL,
                 hitlist longblob,
                 PRIMARY KEY  (id),
                 UNIQUE KEY term (term)
               ) ENGINE=MyISAM;""")
    run_sql("""CREATE TABLE IF NOT EXISTS idxPAIR21R (
                 id_bibrec mediumint(9) unsigned NOT NULL,
                 termlist longblob,
                 type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
                 PRIMARY KEY (id_bibrec,type)
               ) ENGINE=MyISAM;""")

    run_sql("""CREATE TABLE IF NOT EXISTS idxPAIR22F (
                 id mediumint(9) unsigned NOT NULL auto_increment,
                 term varchar(100) default NULL,
                 hitlist longblob,
                 PRIMARY KEY  (id),
                 UNIQUE KEY term (term)
               ) ENGINE=MyISAM;""")
    run_sql("""CREATE TABLE IF NOT EXISTS idxPAIR22R (
                 id_bibrec mediumint(9) unsigned NOT NULL,
                 termlist longblob,
                 type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
                 PRIMARY KEY (id_bibrec,type)
               ) ENGINE=MyISAM;""")

    run_sql("""CREATE TABLE IF NOT EXISTS idxPAIR23F (
                 id mediumint(9) unsigned NOT NULL auto_increment,
                 term varchar(100) default NULL,
                 hitlist longblob,
                 PRIMARY KEY  (id),
                 UNIQUE KEY term (term)
               ) ENGINE=MyISAM;""")
    run_sql("""CREATE TABLE IF NOT EXISTS idxPAIR23R (
                 id_bibrec mediumint(9) unsigned NOT NULL,
                 termlist longblob,
                 type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
                 PRIMARY KEY (id_bibrec,type)
               ) ENGINE=MyISAM;""")

    run_sql("""CREATE TABLE IF NOT EXISTS idxPHRASE20F (
                 id mediumint(9) unsigned NOT NULL auto_increment,
                 term text default NULL,
                 hitlist longblob,
                 PRIMARY KEY  (id),
                 KEY term (term(50))
               ) ENGINE=MyISAM;""")
    run_sql("""CREATE TABLE IF NOT EXISTS idxPHRASE20R (
                 id_bibrec mediumint(9) unsigned NOT NULL,
                 termlist longblob,
                 type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
                 PRIMARY KEY (id_bibrec,type)
               ) ENGINE=MyISAM;""")

    run_sql("""CREATE TABLE IF NOT EXISTS idxPHRASE21F (
                 id mediumint(9) unsigned NOT NULL auto_increment,
                 term text default NULL,
                 hitlist longblob,
                 PRIMARY KEY  (id),
                 KEY term (term(50))
               ) ENGINE=MyISAM;""")
    run_sql("""CREATE TABLE IF NOT EXISTS idxPHRASE21R (
                 id_bibrec mediumint(9) unsigned NOT NULL,
                 termlist longblob,
                 type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
                 PRIMARY KEY (id_bibrec,type)
               ) ENGINE=MyISAM;""")

    run_sql("""CREATE TABLE IF NOT EXISTS idxPHRASE22F (
                 id mediumint(9) unsigned NOT NULL auto_increment,
                 term text default NULL,
                 hitlist longblob,
                 PRIMARY KEY  (id),
                 KEY term (term(50))
               ) ENGINE=MyISAM;""")
    run_sql("""CREATE TABLE IF NOT EXISTS idxPHRASE22R (
                 id_bibrec mediumint(9) unsigned NOT NULL,
                 termlist longblob,
                 type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
                 PRIMARY KEY (id_bibrec,type)
               ) ENGINE=MyISAM;""")

    run_sql("""CREATE TABLE IF NOT EXISTS idxPHRASE23F (
                 id mediumint(9) unsigned NOT NULL auto_increment,
                 term text default NULL,
                 hitlist longblob,
                 PRIMARY KEY  (id),
                 KEY term (term(50))
               ) ENGINE=MyISAM;""")
    run_sql("""CREATE TABLE IF NOT EXISTS idxPHRASE23R (
                 id_bibrec mediumint(9) unsigned NOT NULL,
                 termlist longblob,
                 type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
                 PRIMARY KEY (id_bibrec,type)
               ) ENGINE=MyISAM;""")
    #second step: fill tables with data
    run_sql("""INSERT INTO field VALUES (33,'authority author','authorityauthor')""")
    run_sql("""INSERT INTO field VALUES (34,'authority institution','authorityinstitution')""")
    run_sql("""INSERT INTO field VALUES (35,'authority journal','authorityjournal')""")
    run_sql("""INSERT INTO field VALUES (36,'authority subject','authoritysubject')""")
    run_sql("""INSERT INTO field_tag VALUES (33,1,100)""")
    run_sql("""INSERT INTO field_tag VALUES (33,146,100)""")
    run_sql("""INSERT INTO field_tag VALUES (33,140,100)""")
    run_sql("""INSERT INTO field_tag VALUES (34,148,100)""")
    run_sql("""INSERT INTO field_tag VALUES (34,149,100)""")
    run_sql("""INSERT INTO field_tag VALUES (34,150,100)""")
    run_sql("""INSERT INTO field_tag VALUES (35,151,100)""")
    run_sql("""INSERT INTO field_tag VALUES (35,152,100)""")
    run_sql("""INSERT INTO field_tag VALUES (35,153,100)""")
    run_sql("""INSERT INTO field_tag VALUES (36,154,100)""")
    run_sql("""INSERT INTO field_tag VALUES (36,155,100)""")
    run_sql("""INSERT INTO field_tag VALUES (36,156,100)""")
    run_sql("""INSERT INTO tag VALUES (145,'authority: main personal name','100__a')""")
    run_sql("""INSERT INTO tag VALUES (146,'authority: alternative personal name','400__a')""")
    run_sql("""INSERT INTO tag VALUES (147,'authority: personal name from other record','500__a')""")
    run_sql("""INSERT INTO tag VALUES (148,'authority: organization main name','110__a')""")
    run_sql("""INSERT INTO tag VALUES (149,'organization alternative name','410__a')""")
    run_sql("""INSERT INTO tag VALUES (150,'organization main from other record','510__a')""")
    run_sql("""INSERT INTO tag VALUES (151,'authority: uniform title','130__a')""")
    run_sql("""INSERT INTO tag VALUES (152,'authority: uniform title alternatives','430__a')""")
    run_sql("""INSERT INTO tag VALUES (153,'authority: uniform title from other record','530__a')""")
    run_sql("""INSERT INTO tag VALUES (154,'authority: subject from other record','150__a')""")
    run_sql("""INSERT INTO tag VALUES (155,'authority: subject alternative name','450__a')""")
    run_sql("""INSERT INTO tag VALUES (156,'authority: subject main name','550__a')""")

    run_sql("""INSERT INTO idxINDEX VALUES (20,'authorityauthor','This index contains words/phrases from author authority records.','0000-00-00 00:00:00', '', 'native', '','No','No','No', 'BibIndexAuthorTokenizer')""")
    run_sql("""INSERT INTO idxINDEX VALUES (21,'authorityinstitution','This index contains words/phrases from institution authority records.','0000-00-00 00:00:00', '', 'native', '','No','No','No', 'BibIndexDefaultTokenizer')""")
    run_sql("""INSERT INTO idxINDEX VALUES (22,'authorityjournal','This index contains words/phrases from journal authority records.','0000-00-00 00:00:00', '', 'native', '','No','No','No', 'BibIndexDefaultTokenizer')""")
    run_sql("""INSERT INTO idxINDEX VALUES (23,'authoritysubject','This index contains words/phrases from subject authority records.','0000-00-00 00:00:00', '', 'native', '','No','No','No', 'BibIndexDefaultTokenizer')""")

    run_sql("""INSERT INTO idxINDEX_field (id_idxINDEX, id_field) VALUES (20,33)""")
    run_sql("""INSERT INTO idxINDEX_field (id_idxINDEX, id_field) VALUES (21,34)""")
    run_sql("""INSERT INTO idxINDEX_field (id_idxINDEX, id_field) VALUES (22,35)""")
    run_sql("""INSERT INTO idxINDEX_field (id_idxINDEX, id_field) VALUES (23,36)""")


def estimate():
    return 1


def pre_upgrade():
    pass


def post_upgrade():
    pass
