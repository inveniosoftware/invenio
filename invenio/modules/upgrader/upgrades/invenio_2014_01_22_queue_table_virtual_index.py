# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2012, 2013, 2014 CERN.
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

depends_on = ['invenio_2013_09_30_indexer_interface']

def info():
	return "New queue tables for virtual indexes: idxWORD/PAIR/PHRASExxQ"

def do_upgrade():
	global_id = 1

	run_sql("""CREATE TABLE IF NOT EXISTS idxWORD%02dQ (
				  id mediumint(10) unsigned NOT NULL auto_increment,
				  runtime datetime NOT NULL default '0000-00-00 00:00:00',
				  id_bibrec_low mediumint(9) unsigned NOT NULL,
				  id_bibrec_high mediumint(9) unsigned NOT NULL,
				  index_name varchar(50) NOT NULL default '',
				  mode varchar(50) NOT NULL default 'update',
				  PRIMARY KEY (id),
				  INDEX (index_name),
				  INDEX (runtime)
				) ENGINE=MyISAM;""" % global_id)

	run_sql("""CREATE TABLE IF NOT EXISTS idxPAIR%02dQ (
				  id mediumint(10) unsigned NOT NULL auto_increment,
				  runtime datetime NOT NULL default '0000-00-00 00:00:00',
				  id_bibrec_low mediumint(9) unsigned NOT NULL,
				  id_bibrec_high mediumint(9) unsigned NOT NULL,
				  index_name varchar(50) NOT NULL default '',
				  mode varchar(50) NOT NULL default 'update',
				  PRIMARY KEY (id),
				  INDEX (index_name),
				  INDEX (runtime)
				) ENGINE=MyISAM;""" % global_id)

	run_sql("""CREATE TABLE IF NOT EXISTS idxPHRASE%02dQ (
				  id mediumint(10) unsigned NOT NULL auto_increment,
				  runtime datetime NOT NULL default '0000-00-00 00:00:00',
				  id_bibrec_low mediumint(9) unsigned NOT NULL,
				  id_bibrec_high mediumint(9) unsigned NOT NULL,
				  index_name varchar(50) NOT NULL default '',
				  mode varchar(50) NOT NULL default 'update',
				  PRIMARY KEY (id),
				  INDEX (index_name),
				  INDEX (runtime)
				) ENGINE=MyISAM;""" % global_id)


def estimate():
	return 1

def pre_upgrade():
	pass

def post_upgrade():
	print "NOTE: If you plan to change some of your indexes " \
              "to virtual type, please note that you need to run " \
              "new separate bibindex process for them"
