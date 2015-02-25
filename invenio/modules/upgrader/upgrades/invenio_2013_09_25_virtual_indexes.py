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

from __future__ import print_function

from invenio.legacy.dbquery import run_sql

depends_on = ['invenio_2013_08_22_new_index_itemcount',
              'invenio_2013_08_22_hstRECORD_affected_fields']

def info():
    return "BibIndex virtual indexes"

def do_upgrade():
    run_sql("""CREATE TABLE IF NOT EXISTS idxINDEX_idxINDEX (
                 id_virtual mediumint(9) unsigned NOT NULL,
                 id_normal mediumint(9) unsigned NOT NULL,
                 PRIMARY KEY (id_virtual,id_normal)
               ) ENGINE=MyISAM""")

def do_upgrade_atlantis():
    #0 step: parametrize script for quick change
    misc_field = 39
    misc_index = 26
    #1st step: create tables for miscellaneous index
    run_sql("""CREATE TABLE IF NOT EXISTS idxWORD%02dF (
                 id mediumint(9) unsigned NOT NULL auto_increment,
                 term varchar(50) default NULL,
                 hitlist longblob,
                 PRIMARY KEY  (id),
                 UNIQUE KEY term (term)
               ) ENGINE=MyISAM""" % misc_index)
    run_sql("""CREATE TABLE IF NOT EXISTS idxWORD%02dR (
                 id_bibrec mediumint(9) unsigned NOT NULL,
                 termlist longblob,
                 type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
                 PRIMARY KEY (id_bibrec,type)
               ) ENGINE=MyISAM""" % misc_index)
    run_sql("""CREATE TABLE IF NOT EXISTS idxPAIR%02dF (
                 id mediumint(9) unsigned NOT NULL auto_increment,
                 term varchar(100) default NULL,
                 hitlist longblob,
                 PRIMARY KEY  (id),
                 UNIQUE KEY term (term)
               ) ENGINE=MyISAM""" % misc_index)
    run_sql("""CREATE TABLE IF NOT EXISTS idxPAIR%02dR (
                 id_bibrec mediumint(9) unsigned NOT NULL,
                 termlist longblob,
                 type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
                 PRIMARY KEY (id_bibrec,type)
               ) ENGINE=MyISAM""" % misc_index)
    run_sql("""CREATE TABLE IF NOT EXISTS idxPHRASE%02dF (
                 id mediumint(9) unsigned NOT NULL auto_increment,
                 term text default NULL,
                 hitlist longblob,
                 PRIMARY KEY  (id),
                 KEY term (term(50))
               ) ENGINE=MyISAM""" % misc_index)
    run_sql("""CREATE TABLE IF NOT EXISTS idxPHRASE%02dR (
                 id_bibrec mediumint(9) unsigned NOT NULL,
                 termlist longblob,
                 type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
                 PRIMARY KEY (id_bibrec,type)
               ) ENGINE=MyISAM""" % misc_index)

    #2nd step: add 'miscellaneous' index to idxINDEX table
    run_sql("""INSERT INTO idxINDEX VALUES (%s,'miscellaneous','This index contains words/phrases from miscellaneous fields','0000-00-00 00:00:00', '', 'native','','No','No','No', 'BibIndexDefaultTokenizer')""" % misc_index)

    #3rd step: add 'miscellaneous' field
    run_sql("""INSERT INTO field VALUES (%s,'miscellaneous', 'miscellaneous')""" % misc_field)

    #4th step: add idxINDEX_field map
    run_sql("""INSERT INTO idxINDEX_field (id_idxINDEX, id_field) VALUES (%s,%s)""" % (misc_index, misc_field))

    #5th step: add tags
    run_sql("""INSERT INTO tag VALUES (157,'031x','031%')""")
    run_sql("""INSERT INTO tag VALUES (158,'032x','032%')""")
    run_sql("""INSERT INTO tag VALUES (159,'033x','033%')""")
    run_sql("""INSERT INTO tag VALUES (160,'034x','034%')""")
    run_sql("""INSERT INTO tag VALUES (161,'035x','035%')""")
    run_sql("""INSERT INTO tag VALUES (162,'036x','036%')""")
    run_sql("""INSERT INTO tag VALUES (163,'037x','037%')""")
    run_sql("""INSERT INTO tag VALUES (164,'038x','038%')""")
    run_sql("""INSERT INTO tag VALUES (165,'080x','080%')""")
    run_sql("""INSERT INTO tag VALUES (166,'082x','082%')""")
    run_sql("""INSERT INTO tag VALUES (167,'083x','083%')""")
    run_sql("""INSERT INTO tag VALUES (168,'084x','084%')""")
    run_sql("""INSERT INTO tag VALUES (169,'085x','085%')""")
    run_sql("""INSERT INTO tag VALUES (170,'086x','086%')""")
    run_sql("""INSERT INTO tag VALUES (171,'240x','240%')""")
    run_sql("""INSERT INTO tag VALUES (172,'242x','242%')""")
    run_sql("""INSERT INTO tag VALUES (173,'243x','243%')""")
    run_sql("""INSERT INTO tag VALUES (174,'244x','244%')""")
    run_sql("""INSERT INTO tag VALUES (175,'247x','247%')""")
    run_sql("""INSERT INTO tag VALUES (176,'521x','521%')""")
    run_sql("""INSERT INTO tag VALUES (177,'522x','522%')""")
    run_sql("""INSERT INTO tag VALUES (178,'524x','524%')""")
    run_sql("""INSERT INTO tag VALUES (179,'525x','525%')""")
    run_sql("""INSERT INTO tag VALUES (180,'526x','526%')""")
    run_sql("""INSERT INTO tag VALUES (181,'650x','650%')""")
    run_sql("""INSERT INTO tag VALUES (182,'651x','651%')""")
    run_sql("""INSERT INTO tag VALUES (183,'6531_v','6531_v')""")
    run_sql("""INSERT INTO tag VALUES (184,'6531_y','6531_y')""")
    run_sql("""INSERT INTO tag VALUES (185,'6531_9','6531_9')""")
    run_sql("""INSERT INTO tag VALUES (186,'654x','654%')""")
    run_sql("""INSERT INTO tag VALUES (187,'655x','655%')""")
    run_sql("""INSERT INTO tag VALUES (188,'656x','656%')""")
    run_sql("""INSERT INTO tag VALUES (189,'657x','657%')""")
    run_sql("""INSERT INTO tag VALUES (190,'658x','658%')""")
    run_sql("""INSERT INTO tag VALUES (191,'711x','711%')""")
    run_sql("""INSERT INTO tag VALUES (192,'900x','900%')""")
    run_sql("""INSERT INTO tag VALUES (193,'901x','901%')""")
    run_sql("""INSERT INTO tag VALUES (194,'902x','902%')""")
    run_sql("""INSERT INTO tag VALUES (195,'903x','903%')""")
    run_sql("""INSERT INTO tag VALUES (196,'904x','904%')""")
    run_sql("""INSERT INTO tag VALUES (197,'905x','905%')""")
    run_sql("""INSERT INTO tag VALUES (198,'906x','906%')""")
    run_sql("""INSERT INTO tag VALUES (199,'907x','907%')""")
    run_sql("""INSERT INTO tag VALUES (200,'908x','908%')""")
    run_sql("""INSERT INTO tag VALUES (201,'909C1x','909C1%')""")
    run_sql("""INSERT INTO tag VALUES (202,'909C5x','909C5%')""")
    run_sql("""INSERT INTO tag VALUES (203,'909CSx','909CS%')""")
    run_sql("""INSERT INTO tag VALUES (204,'909COx','909CO%')""")
    run_sql("""INSERT INTO tag VALUES (205,'909CKx','909CK%')""")
    run_sql("""INSERT INTO tag VALUES (206,'909CPx','909CP%')""")
    run_sql("""INSERT INTO tag VALUES (207,'981x','981%')""")
    run_sql("""INSERT INTO tag VALUES (208,'982x','982%')""")
    run_sql("""INSERT INTO tag VALUES (209,'983x','983%')""")
    run_sql("""INSERT INTO tag VALUES (210,'984x','984%')""")
    run_sql("""INSERT INTO tag VALUES (211,'985x','985%')""")
    run_sql("""INSERT INTO tag VALUES (212,'986x','986%')""")
    run_sql("""INSERT INTO tag VALUES (213,'987x','987%')""")
    run_sql("""INSERT INTO tag VALUES (214,'988x','988%')""")
    run_sql("""INSERT INTO tag VALUES (215,'989x','989%')""")
    run_sql("""INSERT INTO tag VALUES (216,'author control','100__0')""")
    run_sql("""INSERT INTO tag VALUES (217,'institution control','110__0')""")
    run_sql("""INSERT INTO tag VALUES (218,'journal control','130__0')""")
    run_sql("""INSERT INTO tag VALUES (219,'subject control','150__0')""")
    run_sql("""INSERT INTO tag VALUES (220,'additional institution control', '260__0')""")
    run_sql("""INSERT INTO tag VALUES (221,'additional author control', '700__0')""")

    #6th step: add field tag mapping
    run_sql("""INSERT INTO field_tag VALUES (%s,17,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,18,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,157,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,158,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,159,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,160,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,161,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,162,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,163,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,164,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,20,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,21,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,22,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,23,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,165,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,166,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,167,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,168,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,169,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,170,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,25,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,27,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,28,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,29,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,30,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,31,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,32,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,33,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,34,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,35,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,36,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,37,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,38,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,39,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,171,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,172,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,173,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,174,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,175,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,41,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,42,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,43,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,44,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,45,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,46,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,47,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,48,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,49,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,50,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,51,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,52,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,53,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,54,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,55,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,56,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,57,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,58,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,59,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,60,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,61,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,62,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,63,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,64,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,65,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,66,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,67,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,176,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,177,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,178,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,179,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,180,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,69,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,70,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,71,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,72,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,73,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,74,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,75,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,76,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,77,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,78,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,79,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,80,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,181,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,182,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,183,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,184,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,185,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,186,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,82,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,83,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,84,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,85,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,187,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,88,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,89,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,90,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,91,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,92,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,93,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,94,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,95,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,96,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,97,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,98,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,99,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,100,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,102,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,103,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,104,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,105,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,188,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,189,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,190,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,191,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,192,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,193,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,194,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,195,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,196,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,107,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,108,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,109,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,110,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,111,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,112,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,113,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,197,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,198,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,199,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,200,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,201,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,202,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,203,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,204,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,205,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,206,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,207,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,208,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,209,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,210,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,211,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,212,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,213,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,214,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,215,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,122,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,123,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,124,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,125,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,126,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,127,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,128,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,129,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,130,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,1,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,2,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,216,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,217,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,218,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,219,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,220,10)""" % misc_field)
    run_sql("""INSERT INTO field_tag VALUES (%s,221,10)""" % misc_field)

    #7th step: remove old unneeded field tag mapping
    run_sql("""DELETE FROM field_tag WHERE id_field=1""")

    #8th step: add mapping between indexes for global index
    query = """SELECT name, id FROM idxINDEX"""
    ids = dict(run_sql(query))
    run_sql("""INSERT INTO idxINDEX_idxINDEX (id_virtual, id_normal) VALUES (%s, %s)""" % (ids['global'], ids['collection']))
    run_sql("""INSERT INTO idxINDEX_idxINDEX (id_virtual, id_normal) VALUES (%s, %s)""" % (ids['global'], ids['abstract']))
    run_sql("""INSERT INTO idxINDEX_idxINDEX (id_virtual, id_normal) VALUES (%s, %s)""" % (ids['global'], ids['collection']))
    run_sql("""INSERT INTO idxINDEX_idxINDEX (id_virtual, id_normal) VALUES (%s, %s)""" % (ids['global'], ids['reportnumber']))
    run_sql("""INSERT INTO idxINDEX_idxINDEX (id_virtual, id_normal) VALUES (%s, %s)""" % (ids['global'], ids['title']))
    run_sql("""INSERT INTO idxINDEX_idxINDEX (id_virtual, id_normal) VALUES (%s, %s)""" % (ids['global'], ids['year']))
    run_sql("""INSERT INTO idxINDEX_idxINDEX (id_virtual, id_normal) VALUES (%s, %s)""" % (ids['global'], ids['journal']))
    run_sql("""INSERT INTO idxINDEX_idxINDEX (id_virtual, id_normal) VALUES (%s, %s)""" % (ids['global'], ids['collaboration']))
    run_sql("""INSERT INTO idxINDEX_idxINDEX (id_virtual, id_normal) VALUES (%s, %s)""" % (ids['global'], ids['affiliation']))
    run_sql("""INSERT INTO idxINDEX_idxINDEX (id_virtual, id_normal) VALUES (%s, %s)""" % (ids['global'], ids['exacttitle']))
    run_sql("""INSERT INTO idxINDEX_idxINDEX (id_virtual, id_normal) VALUES (%s, %s)""" % (ids['global'], ids['miscellaneous']))


def estimate():
    return 1

def pre_upgrade():
    pass

def post_upgrade():
    print('NOTE: please double check your index settings in BibIndex Admin Interface; you can make your global index virtual.')
