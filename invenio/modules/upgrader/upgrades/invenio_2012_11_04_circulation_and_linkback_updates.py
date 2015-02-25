# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2012 CERN.
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

import warnings
from invenio.legacy.dbquery import run_sql
from invenio.utils.text import wait_for_user

depends_on = ['invenio_release_1_1_0']

def info():
    return "WebLinkback and BibCirculation updates"

def do_upgrade():

    ## Since Invenio Upgrader was committed to maint-1.1 and merged to
    ## master in 8d7ed84, some of the tables that were different in
    ## maint-1.1 and master at the time needed upgrade recipe.  This
    ## commit fixes the situation in gentle manner (by checking column
    ## existence etc), since some sites may have upgraded DB schema in
    ## various times.

    ## Firstly, BibCirculation tables:

    # crcBORROWER
    create_statement = run_sql('SHOW CREATE TABLE crcBORROWER')[0][1]
    if '`ccid` int(15)' not in create_statement:
        run_sql("ALTER TABLE crcBORROWER ADD COLUMN ccid int(15) " \
                "unsigned NULL default NULL AFTER id")
    if 'KEY `ccid`' not in create_statement:
        run_sql("ALTER TABLE crcBORROWER ADD UNIQUE KEY ccid (ccid)")
    if 'KEY `name`' not in create_statement:
        run_sql("ALTER TABLE crcBORROWER ADD KEY name (name)")
    if 'KEY `email`' not in create_statement:
        run_sql("ALTER TABLE crcBORROWER ADD KEY email (email)")

    # crcILLREQUEST
    create_statement = run_sql('SHOW CREATE TABLE crcILLREQUEST')[0][1]
    if '`budget_code` varchar(60)' not in create_statement:
        run_sql("ALTER TABLE crcILLREQUEST ADD COLUMN budget_code varchar(60) " \
                "NOT NULL default '' AFTER cost")

    # crcITEM.expected_arrival_date
    create_statement = run_sql('SHOW CREATE TABLE crcITEM')[0][1]
    if '`expected_arrival_date` varchar(60)' not in create_statement:
        run_sql("ALTER TABLE crcITEM ADD COLUMN expected_arrival_date varchar(60) " \
                "NOT NULL default '' AFTER status")

    ## Secondly, WebLinkback tables:

    run_sql("""
CREATE TABLE IF NOT EXISTS lnkENTRY (
  id int(15) NOT NULL auto_increment,
  origin_url varchar(100) NOT NULL, -- url of the originating resource
  id_bibrec mediumint(8) unsigned NOT NULL, -- bibrecord
  additional_properties longblob,
  type varchar(30) NOT NULL,
  status varchar(30) NOT NULL default 'PENDING',
  insert_time datetime default '0000-00-00 00:00:00',
  PRIMARY KEY (id),
  INDEX (id_bibrec),
  INDEX (type),
  INDEX (status),
  INDEX (insert_time)
) ENGINE=MyISAM;
""")

    run_sql("""
CREATE TABLE IF NOT EXISTS lnkENTRYURLTITLE (
  id int(15) unsigned NOT NULL auto_increment,
  url varchar(100) NOT NULL,
  title varchar(100) NOT NULL,
  manual_set boolean NOT NULL default 0,
  broken_count int(5) default 0,
  broken boolean NOT NULL default 0,
  PRIMARY KEY (id),
  UNIQUE (url),
  INDEX (title)
) ENGINE=MyISAM;
""")

    run_sql("""
CREATE TABLE IF NOT EXISTS lnkENTRYLOG (
  id_lnkENTRY int(15) unsigned NOT NULL,
  id_lnkLOG int(15) unsigned NOT NULL,
  FOREIGN KEY (id_lnkENTRY) REFERENCES lnkENTRY(id),
  FOREIGN KEY (id_lnkLOG) REFERENCES lnkLOG(id)
) ENGINE=MyISAM;
""")

    run_sql("""
CREATE TABLE IF NOT EXISTS lnkLOG (
  id int(15) unsigned NOT NULL auto_increment,
  id_user int(15) unsigned,
  action varchar(30) NOT NULL,
  log_time datetime default '0000-00-00 00:00:00',
  PRIMARY KEY (id),
  INDEX (id_user),
  INDEX (action),
  INDEX (log_time)
) ENGINE=MyISAM;
""")

    run_sql("""
CREATE TABLE IF NOT EXISTS lnkADMINURL (
  id int(15) unsigned NOT NULL auto_increment,
  url varchar(100) NOT NULL,
  list varchar(30) NOT NULL,
  PRIMARY KEY (id),
  UNIQUE (url),
  INDEX (list)
) ENGINE=MyISAM;
""")

    run_sql("""
CREATE TABLE IF NOT EXISTS lnkADMINURLLOG (
  id_lnkADMINURL int(15) unsigned NOT NULL,
  id_lnkLOG int(15) unsigned NOT NULL,
  FOREIGN KEY (id_lnkADMINURL) REFERENCES lnkADMINURL(id),
  FOREIGN KEY (id_lnkLOG) REFERENCES lnkLOG(id)
) ENGINE=MyISAM;
""")

def estimate():
    return 10

def pre_upgrade():
    pass

def post_upgrade():
    pass
