-- This file is part of Invenio.
-- Copyright (C) 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014 CERN.
--
-- Invenio is free software; you can redistribute it and/or
-- modify it under the terms of the GNU General Public License as
-- published by the Free Software Foundation; either version 2 of the
-- License, or (at your option) any later version.
--
-- Invenio is distributed in the hope that it will be useful, but
-- WITHOUT ANY WARRANTY; without even the implied warranty of
-- MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
-- General Public License for more details.
--
-- You should have received a copy of the GNU General Public License
-- along with Invenio; if not, write to the Free Software Foundation, Inc.,
-- 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

-- tables for bibliographic records:

CREATE TABLE IF NOT EXISTS bibrec (
  id mediumint(8) unsigned NOT NULL auto_increment,
  creation_date datetime NOT NULL default '0000-00-00',
  modification_date datetime NOT NULL default '0000-00-00',
  master_format varchar(16) NOT NULL default 'marc',
  PRIMARY KEY  (id),
  KEY creation_date (creation_date),
  KEY modification_date (modification_date)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib00x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib01x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib02x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib03x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib04x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib05x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib06x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib07x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib08x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib09x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib10x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib11x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib12x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib13x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib14x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib15x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib16x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib17x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib18x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib19x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib20x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib21x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib22x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib23x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib24x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib25x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib26x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib27x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib28x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib29x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib30x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib31x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib32x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib33x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib34x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib35x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib36x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib37x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib38x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib39x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib40x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib41x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib42x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib43x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib44x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib45x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib46x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib47x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib48x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib49x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib50x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib51x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib52x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib53x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib54x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib55x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib56x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib57x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib58x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib59x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib60x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib61x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib62x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib63x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib64x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib65x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib66x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib67x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib68x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib69x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib70x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib71x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib72x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib73x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib74x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib75x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib76x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib77x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib78x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib79x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib80x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib81x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib82x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib83x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib84x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib85x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(100)) -- URLs need usually a larger index for speedy lookups
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib86x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib87x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib88x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib89x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib90x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib91x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib92x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib93x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib94x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib95x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib96x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib97x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib98x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bib99x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib00x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib01x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib02x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib03x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib04x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib05x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib06x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib07x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib08x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib09x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib10x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib11x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib12x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib13x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib14x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib15x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib16x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib17x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib18x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib19x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib20x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib21x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib22x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib23x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib24x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib25x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib26x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib27x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib28x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib29x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib30x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib31x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib32x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib33x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib34x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib35x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib36x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib37x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib38x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib39x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib40x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib41x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib42x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib43x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib44x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib45x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib46x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib47x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib48x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib49x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib50x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib51x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib52x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib53x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib54x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib55x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib56x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib57x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib58x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib59x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib60x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib61x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib62x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib63x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib64x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib65x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib66x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib67x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib68x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib69x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib70x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib71x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib72x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib73x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib74x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib75x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib76x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib77x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib78x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib79x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib80x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib81x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib82x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib83x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib84x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib85x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib86x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib87x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib88x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib89x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib90x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib91x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib92x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib93x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib94x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib95x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib96x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib97x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib98x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib99x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

-- tables for bibliographic records formatted:

CREATE TABLE IF NOT EXISTS bibfmt (
  id_bibrec int(8) unsigned NOT NULL default '0',
  format varchar(10) NOT NULL default '',
  last_updated datetime NOT NULL default '0000-00-00',
  value longblob,
  needs_2nd_pass TINYINT(1) DEFAULT 0,
  PRIMARY KEY  (id_bibrec, format),
  KEY format (format),
  KEY last_updated (last_updated)
) ENGINE=MyISAM;

-- tables for index files:

CREATE TABLE IF NOT EXISTS idxINDEX (
  id mediumint(9) unsigned NOT NULL,
  name varchar(50) NOT NULL default '',
  description varchar(255) NOT NULL default '',
  last_updated datetime NOT NULL default '0000-00-00 00:00:00',
  stemming_language varchar(10) NOT NULL default '',
  indexer varchar(10) NOT NULL default 'native',
  synonym_kbrs varchar(255) NOT NULL default '',
  remove_stopwords varchar(255) NOT NULL default '',
  remove_html_markup varchar(10) NOT NULL default '',
  remove_latex_markup varchar(10) NOT NULL default '',
  tokenizer varchar(50) NOT NULL default '',
  PRIMARY KEY  (id),
  UNIQUE KEY name (name)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxINDEXNAME (
  id_idxINDEX mediumint(9) unsigned NOT NULL,
  ln char(5) NOT NULL default '',
  type char(3) NOT NULL default 'sn',
  value varchar(255) NOT NULL,
  PRIMARY KEY  (id_idxINDEX,ln,type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxINDEX_field (
  id_idxINDEX mediumint(9) unsigned NOT NULL,
  id_field mediumint(9) unsigned NOT NULL,
  regexp_punctuation varchar(255) NOT NULL default "[\.\,\:\;\?\!\"]",
  regexp_alphanumeric_separators varchar(255) NOT NULL default "[\!\"\#\$\%\&\'\(\)\*\+\,\-\.\/\:\;\<\=\>\?\@\[\\\]\^\_\`\{\|\}\~]",
  PRIMARY KEY  (id_idxINDEX,id_field)
) ENGINE=MyISAM;

-- this comment line here is just to fix the SQL display mode in Emacs '

CREATE TABLE IF NOT EXISTS idxINDEX_idxINDEX (
  id_virtual mediumint(9) unsigned NOT NULL,
  id_normal mediumint(9) unsigned NOT NULL,
  PRIMARY KEY (id_virtual,id_normal)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxWORD01F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term varchar(50) default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  UNIQUE KEY term (term)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxWORD01R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  KEY type (type),
  PRIMARY KEY (id_bibrec,type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxWORD01Q (
  id mediumint(10) unsigned NOT NULL auto_increment,
  runtime datetime NOT NULL default '0000-00-00 00:00:00',
  id_bibrec_low mediumint(9) unsigned NOT NULL,
  id_bibrec_high mediumint(9) unsigned NOT NULL,
  index_name varchar(50) NOT NULL default '',
  mode varchar(50) NOT NULL default 'update',
  PRIMARY KEY (id),
  INDEX (index_name),
  INDEX (runtime)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxWORD02F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term varchar(50) default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  UNIQUE KEY term (term)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxWORD02R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  KEY type (type),
  PRIMARY KEY (id_bibrec,type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxWORD03F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term varchar(50) default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  UNIQUE KEY term (term)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxWORD03R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  KEY type (type),
  PRIMARY KEY (id_bibrec,type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxWORD04F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term varchar(50) default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  UNIQUE KEY term (term)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxWORD04R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  KEY type (type),
  PRIMARY KEY (id_bibrec,type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxWORD05F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term varchar(50) default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  UNIQUE KEY term (term)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxWORD05R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  KEY type (type),
  PRIMARY KEY (id_bibrec,type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxWORD06F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term varchar(50) default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  UNIQUE KEY term (term)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxWORD06R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  KEY type (type),
  PRIMARY KEY (id_bibrec,type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxWORD07F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term varchar(50) default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  UNIQUE KEY term (term)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxWORD07R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  KEY type (type),
  PRIMARY KEY (id_bibrec,type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxWORD08F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term varchar(50) default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  UNIQUE KEY term (term)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxWORD08R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  KEY type (type),
  PRIMARY KEY (id_bibrec,type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxWORD09F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term varchar(50) default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  UNIQUE KEY term (term)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxWORD09R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  KEY type (type),
  PRIMARY KEY (id_bibrec,type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxWORD10F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term varchar(50) default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  UNIQUE KEY term (term)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxWORD10R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  KEY type (type),
  PRIMARY KEY (id_bibrec,type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxWORD11F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term varchar(50) default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  UNIQUE KEY term (term)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxWORD11R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  KEY type (type),
  PRIMARY KEY (id_bibrec,type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxWORD12F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term varchar(50) default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  UNIQUE KEY term (term)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxWORD12R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  KEY type (type),
  PRIMARY KEY (id_bibrec,type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxWORD13F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term varchar(50) default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  UNIQUE KEY term (term)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxWORD13R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  KEY type (type),
  PRIMARY KEY (id_bibrec,type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxWORD14F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term varchar(50) default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  UNIQUE KEY term (term)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxWORD14R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  KEY type (type),
  PRIMARY KEY (id_bibrec,type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxWORD15F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term varchar(50) default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  UNIQUE KEY term (term)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxWORD15R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  KEY type (type),
  PRIMARY KEY (id_bibrec,type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxWORD16F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term varchar(50) default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  UNIQUE KEY term (term)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxWORD16R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  KEY type (type),
  PRIMARY KEY (id_bibrec,type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxWORD17F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term varchar(50) default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  UNIQUE KEY term (term)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxWORD17R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  KEY type (type),
  PRIMARY KEY (id_bibrec,type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxWORD18F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term varchar(50) default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  UNIQUE KEY term (term)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxWORD18R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  KEY type (type),
  PRIMARY KEY (id_bibrec,type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxWORD19F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term varchar(50) default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  UNIQUE KEY term (term)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxWORD19R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  KEY type (type),
  PRIMARY KEY (id_bibrec,type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxWORD20F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term varchar(50) default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  UNIQUE KEY term (term)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxWORD20R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  KEY type (type),
  PRIMARY KEY (id_bibrec,type)
) ENGINE=MyISAM;


CREATE TABLE IF NOT EXISTS idxWORD21F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term varchar(50) default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  UNIQUE KEY term (term)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxWORD21R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  KEY type (type),
  PRIMARY KEY (id_bibrec,type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxWORD22F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term varchar(50) default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  UNIQUE KEY term (term)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxWORD22R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  KEY type (type),
  PRIMARY KEY (id_bibrec,type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxWORD23F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term varchar(50) default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  UNIQUE KEY term (term)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxWORD23R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  KEY type (type),
  PRIMARY KEY (id_bibrec,type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxWORD24F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term varchar(50) default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  UNIQUE KEY term (term)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxWORD24R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  KEY type (type),
  PRIMARY KEY (id_bibrec,type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxWORD25F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term varchar(50) default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  UNIQUE KEY term (term)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxWORD25R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  KEY type (type),
  PRIMARY KEY (id_bibrec,type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxWORD26F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term varchar(50) default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  UNIQUE KEY term (term)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxWORD26R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  PRIMARY KEY (id_bibrec,type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxWORD27F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term varchar(50) default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  UNIQUE KEY term (term)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxWORD27R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  PRIMARY KEY (id_bibrec,type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxWORD28F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term varchar(50) default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  UNIQUE KEY term (term)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxWORD28R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  PRIMARY KEY (id_bibrec,type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPAIR01F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term varchar(100) default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  UNIQUE KEY term (term)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPAIR01R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  KEY type (type),
  PRIMARY KEY (id_bibrec,type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPAIR01Q (
  id mediumint(10) unsigned NOT NULL auto_increment,
  runtime datetime NOT NULL default '0000-00-00 00:00:00',
  id_bibrec_low mediumint(9) unsigned NOT NULL,
  id_bibrec_high mediumint(9) unsigned NOT NULL,
  index_name varchar(50) NOT NULL default '',
  mode varchar(50) NOT NULL default 'update',
  PRIMARY KEY (id),
  INDEX (index_name),
  INDEX (runtime)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPAIR02F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term varchar(100) default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  UNIQUE KEY term (term)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPAIR02R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  KEY type (type),
  PRIMARY KEY (id_bibrec,type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPAIR03F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term varchar(100) default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  UNIQUE KEY term (term)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPAIR03R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  KEY type (type),
  PRIMARY KEY (id_bibrec,type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPAIR04F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term varchar(100) default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  UNIQUE KEY term (term)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPAIR04R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  KEY type (type),
  PRIMARY KEY (id_bibrec,type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPAIR05F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term varchar(100) default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  UNIQUE KEY term (term)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPAIR05R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  KEY type (type),
  PRIMARY KEY (id_bibrec,type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPAIR06F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term varchar(100) default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  UNIQUE KEY term (term)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPAIR06R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  KEY type (type),
  PRIMARY KEY (id_bibrec,type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPAIR07F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term varchar(100) default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  UNIQUE KEY term (term)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPAIR07R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  KEY type (type),
  PRIMARY KEY (id_bibrec,type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPAIR08F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term varchar(100) default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  UNIQUE KEY term (term)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPAIR08R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  KEY type (type),
  PRIMARY KEY (id_bibrec,type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPAIR09F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term varchar(100) default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  UNIQUE KEY term (term)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPAIR09R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  KEY type (type),
  PRIMARY KEY (id_bibrec,type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPAIR10F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term varchar(100) default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  UNIQUE KEY term (term)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPAIR10R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  KEY type (type),
  PRIMARY KEY (id_bibrec,type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPAIR11F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term varchar(100) default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  UNIQUE KEY term (term)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPAIR11R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  KEY type (type),
  PRIMARY KEY (id_bibrec,type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPAIR12F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term varchar(100) default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  UNIQUE KEY term (term)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPAIR12R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  KEY type (type),
  PRIMARY KEY (id_bibrec,type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPAIR13F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term varchar(100) default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  UNIQUE KEY term (term)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPAIR13R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  KEY type (type),
  PRIMARY KEY (id_bibrec,type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPAIR14F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term varchar(100) default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  UNIQUE KEY term (term)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPAIR14R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  KEY type (type),
  PRIMARY KEY (id_bibrec,type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPAIR15F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term varchar(100) default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  UNIQUE KEY term (term)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPAIR15R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  KEY type (type),
  PRIMARY KEY (id_bibrec,type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPAIR16F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term varchar(100) default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  UNIQUE KEY term (term)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPAIR16R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  KEY type (type),
  PRIMARY KEY (id_bibrec,type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPAIR17F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term varchar(100) default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  UNIQUE KEY term (term)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPAIR17R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  KEY type (type),
  PRIMARY KEY (id_bibrec,type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPAIR18F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term varchar(100) default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  UNIQUE KEY term (term)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPAIR18R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  KEY type (type),
  PRIMARY KEY (id_bibrec,type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPAIR19F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term varchar(100) default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  UNIQUE KEY term (term)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPAIR19R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  KEY type (type),
  PRIMARY KEY (id_bibrec,type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPAIR20F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term varchar(100) default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  UNIQUE KEY term (term)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPAIR20R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  KEY type (type),
  PRIMARY KEY (id_bibrec,type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPAIR21F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term varchar(100) default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  UNIQUE KEY term (term)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPAIR21R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  KEY type (type),
  PRIMARY KEY (id_bibrec,type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPAIR22F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term varchar(100) default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  UNIQUE KEY term (term)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPAIR22R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  KEY type (type),
  PRIMARY KEY (id_bibrec,type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPAIR23F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term varchar(100) default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  UNIQUE KEY term (term)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPAIR23R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  KEY type (type),
  PRIMARY KEY (id_bibrec,type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPAIR24F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term varchar(100) default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  UNIQUE KEY term (term)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPAIR24R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  KEY type (type),
  PRIMARY KEY (id_bibrec,type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPAIR25F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term varchar(100) default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  UNIQUE KEY term (term)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPAIR25R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  KEY type (type),
  PRIMARY KEY (id_bibrec,type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPAIR26F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term varchar(100) default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  UNIQUE KEY term (term)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPAIR26R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  PRIMARY KEY (id_bibrec,type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPAIR27F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term varchar(100) default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  UNIQUE KEY term (term)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPAIR27R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  PRIMARY KEY (id_bibrec,type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPAIR28F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term varchar(100) default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  UNIQUE KEY term (term)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPAIR28R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  PRIMARY KEY (id_bibrec,type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPHRASE01F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term text default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  KEY term (term(50))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPHRASE01R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  KEY type (type),
  PRIMARY KEY (id_bibrec,type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPHRASE02F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term text default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  KEY term (term(50))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPHRASE01Q (
  id mediumint(10) unsigned NOT NULL auto_increment,
  runtime datetime NOT NULL default '0000-00-00 00:00:00',
  id_bibrec_low mediumint(9) unsigned NOT NULL,
  id_bibrec_high mediumint(9) unsigned NOT NULL,
  index_name varchar(50) NOT NULL default '',
  mode varchar(50) NOT NULL default 'update',
  PRIMARY KEY (id),
  INDEX (index_name),
  INDEX (runtime)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPHRASE02R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  KEY type (type),
  PRIMARY KEY (id_bibrec,type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPHRASE03F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term text default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  KEY term (term(50))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPHRASE03R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  KEY type (type),
  PRIMARY KEY (id_bibrec,type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPHRASE04F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term text default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  KEY term (term(50))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPHRASE04R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  KEY type (type),
  PRIMARY KEY (id_bibrec,type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPHRASE05F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term text default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  KEY term (term(50))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPHRASE05R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  KEY type (type),
  PRIMARY KEY (id_bibrec,type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPHRASE06F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term text default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  KEY term (term(50))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPHRASE06R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  KEY type (type),
  PRIMARY KEY (id_bibrec,type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPHRASE07F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term text default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  KEY term (term(50))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPHRASE07R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  KEY type (type),
  PRIMARY KEY (id_bibrec,type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPHRASE08F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term text default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  KEY term (term(50))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPHRASE08R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  PRIMARY KEY (id_bibrec,type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPHRASE09F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term text default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  KEY term (term(50))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPHRASE09R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  PRIMARY KEY (id_bibrec,type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPHRASE10F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term text default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  KEY term (term(50))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPHRASE10R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  PRIMARY KEY (id_bibrec,type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPHRASE11F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term text default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  KEY term (term(50))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPHRASE11R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  PRIMARY KEY (id_bibrec,type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPHRASE12F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term text default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  KEY term (term(50))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPHRASE12R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  PRIMARY KEY (id_bibrec,type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPHRASE13F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term text default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  KEY term (term(50))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPHRASE13R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  PRIMARY KEY (id_bibrec,type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPHRASE14F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term text default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  KEY term (term(50))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPHRASE14R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  PRIMARY KEY (id_bibrec,type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPHRASE15F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term text default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  KEY term (term(50))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPHRASE15R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  PRIMARY KEY (id_bibrec,type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPHRASE16F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term text default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  KEY term (term(50))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPHRASE16R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  PRIMARY KEY (id_bibrec,type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPHRASE17F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term text default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  KEY term (term(50))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPHRASE17R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  PRIMARY KEY (id_bibrec,type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPHRASE18F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term text default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  KEY term (term(50))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPHRASE18R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  PRIMARY KEY (id_bibrec,type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPHRASE19F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term text default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  KEY term (term(50))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPHRASE19R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  PRIMARY KEY (id_bibrec,type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPHRASE20F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term text default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  KEY term (term(50))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPHRASE20R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  PRIMARY KEY (id_bibrec,type)
) ENGINE=MyISAM;


CREATE TABLE IF NOT EXISTS idxPHRASE21F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term text default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  KEY term (term(50))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPHRASE21R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  PRIMARY KEY (id_bibrec,type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPHRASE22F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term text default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  KEY term (term(50))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPHRASE22R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  PRIMARY KEY (id_bibrec,type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPHRASE23F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term text default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  KEY term (term(50))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPHRASE23R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  PRIMARY KEY (id_bibrec,type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPHRASE24F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term text default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  KEY term (term(50))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPHRASE24R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  PRIMARY KEY (id_bibrec,type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPHRASE25F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term text default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  KEY term (term(50))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPHRASE25R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  PRIMARY KEY (id_bibrec,type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPHRASE26F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term text default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  KEY term (term(50))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPHRASE26R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  PRIMARY KEY (id_bibrec,type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPHRASE27F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term text default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  KEY term (term(50))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPHRASE27R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  PRIMARY KEY (id_bibrec,type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPHRASE28F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term text default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  KEY term (term(50))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPHRASE28R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  PRIMARY KEY (id_bibrec,type)
) ENGINE=MyISAM;

-- tables for ranking:

CREATE TABLE IF NOT EXISTS rnkMETHOD (
  id mediumint(9) unsigned NOT NULL auto_increment,
  name varchar(20) NOT NULL default '',
  last_updated datetime NOT NULL default '0000-00-00 00:00:00',
  PRIMARY KEY (id),
  UNIQUE KEY name (name)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS rnkMETHODNAME (
  id_rnkMETHOD mediumint(9) unsigned NOT NULL,
  ln char(5) NOT NULL default '',
  type char(3) NOT NULL default 'sn',
  value varchar(255) NOT NULL,
  PRIMARY KEY  (id_rnkMETHOD,ln,type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS rnkMETHODDATA (
  id_rnkMETHOD mediumint(9) unsigned NOT NULL,
  relevance_data longblob,
  PRIMARY KEY  (id_rnkMETHOD)
) ENGINE=MyISAM;


CREATE TABLE IF NOT EXISTS collection_rnkMETHOD (
  id_collection mediumint(9) unsigned NOT NULL,
  id_rnkMETHOD mediumint(9) unsigned NOT NULL,
  score tinyint(4) unsigned NOT NULL default '0',
  PRIMARY KEY  (id_collection,id_rnkMETHOD)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS rnkWORD01F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term varchar(50) default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  UNIQUE KEY term (term)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS rnkWORD01R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  KEY type (type),
  PRIMARY KEY  (id_bibrec,type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS rnkAUTHORDATA (
  aterm varchar(50) default NULL,
  hitlist longblob,
  UNIQUE KEY aterm (aterm)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS rnkPAGEVIEWS (
  id_bibrec mediumint(8) unsigned default NULL,
  id_user int(15) unsigned default '0',
  client_host int(10) unsigned default NULL,
  view_time datetime default '0000-00-00 00:00:00',
  KEY view_time (view_time),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS rnkDOWNLOADS (
  id_bibrec mediumint(8) unsigned default NULL,
  download_time datetime default '0000-00-00 00:00:00',
  client_host int(10) unsigned default NULL,
  id_user int(15) unsigned default NULL,
  id_bibdoc mediumint(9) unsigned default NULL,
  file_version smallint(2) unsigned default NULL,
  file_format varchar(50) NULL default NULL,
  KEY download_time (download_time),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

-- a table for citations. record-cites-record

CREATE TABLE IF NOT EXISTS rnkCITATIONDICT (
  citee int(10) unsigned NOT NULL,
  citer int(10) unsigned NOT NULL,
  last_updated datetime NOT NULL,
  PRIMARY KEY id (citee, citer),
  KEY reverse (citer, citee)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS rnkSELFCITEDICT (
  citee int(10) unsigned NOT NULL,
  citer int(10) unsigned NOT NULL,
  last_updated datetime NOT NULL,
  PRIMARY KEY id (citee, citer),
  KEY reverse (citer, citee)
) ENGINE=MyISAM;

-- a table for logging changes in the citation dict
CREATE TABLE IF NOT EXISTS rnkCITATIONLOG (
  id int(11) unsigned NOT NULL auto_increment,
  citee int(10) unsigned NOT NULL,
  citer int(10) unsigned NOT NULL,
  `type` ENUM('added', 'removed'),
  action_date datetime NOT NULL,
  PRIMARY KEY (id),
  KEY citee (citee),
  KEY citer (citer)
) ENGINE=MyISAM;


-- a table for missing citations. This should be scanned by a program
-- occasionally to check if some publication has been cited more than
-- 50 times (or such), and alert cataloguers to create record for that
-- external citation
--
-- id_bibrec is the id of the record. extcitepubinfo is publication info
-- that looks in general like hep-th/0112088
CREATE TABLE IF NOT EXISTS rnkCITATIONDATAEXT (
  id_bibrec int(8) unsigned,
  extcitepubinfo varchar(255) NOT NULL,
  PRIMARY KEY (id_bibrec, extcitepubinfo),
  KEY extcitepubinfo (extcitepubinfo)
) ENGINE=MyISAM;

-- tables for self-citations computation

CREATE TABLE IF NOT EXISTS `rnkRECORDSCACHE` (
  `id_bibrec` int(10) unsigned NOT NULL,
  `authorid` bigint(10) NOT NULL,
  PRIMARY KEY (`id_bibrec`,`authorid`)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS `rnkEXTENDEDAUTHORS` (
  `id` int(10) unsigned NOT NULL,
  `authorid` bigint(10) NOT NULL,
  PRIMARY KEY (`id`,`authorid`)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS `rnkSELFCITES` (
  `id_bibrec` int(10) unsigned NOT NULL,
  `count` int(10) unsigned NOT NULL,
  `references` text NOT NULL,
  `last_updated` datetime NOT NULL,
  PRIMARY KEY (`id_bibrec`)
) ENGINE=MyISAM;

-- a table for storing invalid or ambiguous references encountered
CREATE TABLE IF NOT EXISTS rnkCITATIONDATAERR (
  `type` ENUM('multiple-matches', 'not-well-formed'),
  citinfo varchar(255) NOT NULL default '',
  PRIMARY KEY (`type`, citinfo)
) ENGINE=MyISAM;

-- tables for collections and collection tree:

CREATE TABLE IF NOT EXISTS collection (
  id mediumint(9) unsigned NOT NULL auto_increment,
  name varchar(255) NOT NULL,
  dbquery text,
  nbrecs int(10) unsigned default '0',
  reclist longblob,
  PRIMARY KEY  (id),
  UNIQUE KEY name (name),
  KEY dbquery (dbquery(50))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS collectionname (
  id_collection mediumint(9) unsigned NOT NULL,
  ln char(5) NOT NULL default '',
  type char(3) NOT NULL default 'sn',
  value varchar(255) NOT NULL,
  PRIMARY KEY  (id_collection,ln,type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS collection_collection (
  id_dad mediumint(9) unsigned NOT NULL,
  id_son mediumint(9) unsigned NOT NULL,
  type char(1) NOT NULL default 'r',
  score tinyint(4) unsigned NOT NULL default '0',
  PRIMARY KEY (id_dad,id_son)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS collectionboxname (
  id_collection mediumint(9) unsigned NOT NULL,
  ln char(5) NOT NULL default '',
  type char(1) NOT NULL default 'r',
  value varchar(255) NOT NULL,
  PRIMARY KEY  (id_collection,ln,type)
) ENGINE=MyISAM;

-- tables for OAI sets:

CREATE TABLE IF NOT EXISTS oaiREPOSITORY (
  id mediumint(9) unsigned NOT NULL auto_increment,
  setName varchar(255) NOT NULL default '',
  setSpec varchar(255) NOT NULL default 'GLOBAL_SET',
  setCollection varchar(255) NOT NULL default '',
  setDescription text NOT NULL default '',
  setDefinition text NOT NULL default '',
  setRecList longblob,
  last_updated datetime NOT NULL default '1970-01-01',
  p1 text NOT NULL default '',
  f1 text NOT NULL default '',
  m1 text NOT NULL default '',
  p2 text NOT NULL default '',
  f2 text NOT NULL default '',
  m2 text NOT NULL default '',
  p3 text NOT NULL default '',
  f3 text NOT NULL default '',
  m3 text NOT NULL default '',
  PRIMARY KEY (id)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS oaiHARVEST (
  id mediumint(9) unsigned NOT NULL auto_increment,
  baseurl varchar(255) NOT NULL default '',
  metadataprefix varchar(255) NOT NULL default 'oai_dc',
  arguments BLOB NULL default NULL,
  comment text,
  name varchar(255) NOT NULL,
  lastrun datetime,
  frequency mediumint(12) NOT NULL default '0',
  postprocess varchar(20) NOT NULL default 'h',
  setspecs text NOT NULL default '',
  PRIMARY KEY  (id)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS oaiHARVESTLOG (
  id_oaiHARVEST mediumint(9) unsigned NOT NULL REFERENCES oaiHARVEST, -- source we harvest from
  id_bibrec mediumint(8) unsigned NOT NULL default '0', -- internal record id ( filled by bibupload )
  bibupload_task_id int NOT NULL default 0, -- bib upload task number
  oai_id varchar(40) NOT NULL default "", -- OAI record identifier we harvested
  date_harvested datetime NOT NULL default '0000-00-00', -- when we harvested
  date_inserted datetime NOT NULL default '0000-00-00', -- when it was inserted
  inserted_to_db char(1) NOT NULL default 'P', -- where it was inserted (P=prod, H=holding-pen, etc)
  PRIMARY KEY (bibupload_task_id, oai_id, date_harvested)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibHOLDINGPEN (
  changeset_id INT NOT NULL AUTO_INCREMENT, -- the identifier of the changeset stored in the holding pen
  changeset_date datetime NOT NULL DEFAULT '0000:00:00 00:00:00', -- when was the changeset inserted
  changeset_xml longblob NOT NULL,
  oai_id varchar(40) NOT NULL DEFAULT '', -- OAI identifier of concerned record
  id_bibrec mediumint(8) unsigned NOT NULL default '0', -- record ID of concerned record (filled by bibupload)
  PRIMARY KEY (changeset_id),
  KEY changeset_date (changeset_date),
  KEY id_bibrec (id_bibrec)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibARXIVPDF (
  id_bibrec mediumint(8) unsigned NOT NULL,
  status ENUM('ok', 'missing') NOT NULL,
  date_harvested datetime NOT NULL,
  version tinyint(2) NOT NULL,
  PRIMARY KEY (id_bibrec),
  KEY status (status)
) ENGINE=MyISAM;

-- tables for portal elements:

CREATE TABLE IF NOT EXISTS collection_portalbox (
  id_collection mediumint(9) unsigned NOT NULL,
  id_portalbox mediumint(9) unsigned NOT NULL,
  ln char(5) NOT NULL default '',
  position char(3) NOT NULL default 'top',
  score tinyint(4) unsigned NOT NULL default '0',
  PRIMARY KEY  (id_collection,id_portalbox,ln)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS portalbox (
  id mediumint(9) unsigned NOT NULL auto_increment,
  title text NOT NULL,
  body text NOT NULL,
  UNIQUE KEY id (id)
) ENGINE=MyISAM;

-- tables for search examples:

CREATE TABLE IF NOT EXISTS collection_example (
  id_collection mediumint(9) unsigned NOT NULL,
  id_example mediumint(9) unsigned NOT NULL,
  score tinyint(4) unsigned NOT NULL default '0',
  PRIMARY KEY  (id_collection,id_example)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS example (
  id mediumint(9) unsigned NOT NULL auto_increment,
  type text NOT NULL default '',
  body text NOT NULL,
  PRIMARY KEY  (id)
) ENGINE=MyISAM;

-- tables for collection formats:

CREATE TABLE IF NOT EXISTS collection_format (
  id_collection mediumint(9) unsigned NOT NULL,
  id_format mediumint(9) unsigned NOT NULL,
  score tinyint(4) unsigned NOT NULL default '0',
  PRIMARY KEY  (id_collection,id_format)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS format (
  id mediumint(9) unsigned NOT NULL auto_increment,
  name varchar(255) NOT NULL,
  code varchar(6) NOT NULL,
  description varchar(255) default '',
  content_type varchar(255) default '',
  visibility tinyint NOT NULL default '1',
  last_updated datetime NOT NULL default '0000-00-00',
  PRIMARY KEY  (id),
  UNIQUE KEY code (code)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS formatname (
  id_format mediumint(9) unsigned NOT NULL,
  ln char(5) NOT NULL default '',
  type char(3) NOT NULL default 'sn',
  value varchar(255) NOT NULL,
  PRIMARY KEY  (id_format,ln,type)
) ENGINE=MyISAM;

-- tables for collection detailed page options

CREATE TABLE IF NOT EXISTS collectiondetailedrecordpagetabs (
  id_collection mediumint(9) unsigned NOT NULL,
  tabs varchar(255) NOT NULL default '',
  PRIMARY KEY (id_collection)
) ENGINE=MyISAM;

-- tables for search options and MARC tags:

CREATE TABLE IF NOT EXISTS collection_field_fieldvalue (
  id_collection mediumint(9) unsigned NOT NULL,
  id_field mediumint(9) unsigned NOT NULL,
  id_fieldvalue mediumint(9) unsigned,
  type char(3) NOT NULL default 'src',
  score tinyint(4) unsigned NOT NULL default '0',
  score_fieldvalue tinyint(4) unsigned NOT NULL default '0',
  KEY id_collection (id_collection),
  KEY id_field (id_field),
  KEY id_fieldvalue (id_fieldvalue)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS field (
  id mediumint(9) unsigned NOT NULL auto_increment,
  name varchar(255) NOT NULL,
  code varchar(255) NOT NULL,
  PRIMARY KEY  (id),
  UNIQUE KEY code (code)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS fieldname (
  id_field mediumint(9) unsigned NOT NULL,
  ln char(5) NOT NULL default '',
  type char(3) NOT NULL default 'sn',
  value varchar(255) NOT NULL,
  PRIMARY KEY  (id_field,ln,type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS fieldvalue (
  id mediumint(9) unsigned NOT NULL auto_increment,
  name varchar(255) NOT NULL,
  value text NOT NULL,
  PRIMARY KEY  (id)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS field_tag (
  id_field mediumint(9) unsigned NOT NULL,
  id_tag mediumint(9) unsigned NOT NULL,
  score tinyint(4) unsigned NOT NULL default '0',
  PRIMARY KEY  (id_field,id_tag)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS tag (
  id mediumint(9) unsigned NOT NULL auto_increment,
  name varchar(255) NOT NULL,
  value varchar(6) default '',
  recjson_value text,
  PRIMARY KEY  (id)
) ENGINE=MyISAM;

-- tables for file management

CREATE TABLE IF NOT EXISTS bibdoc (
  id mediumint(9) unsigned NOT NULL auto_increment,
  status text NOT NULL default '',
  docname varchar(250) COLLATE utf8_bin default NULL, -- now NULL means that this is new version bibdoc
  creation_date datetime NOT NULL default '0000-00-00',
  modification_date datetime NOT NULL default '0000-00-00',
  text_extraction_date datetime NOT NULL default '0000-00-00',
  doctype varchar(255),
  PRIMARY KEY  (id),
  KEY docname (docname),
  KEY creation_date (creation_date),
  KEY modification_date (modification_date)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bibdoc (
  id_bibrec mediumint(9) unsigned NOT NULL default '0',
  id_bibdoc mediumint(9) unsigned NOT NULL default '0',
  docname varchar(250) COLLATE utf8_bin NOT NULL default 'file',
  type varchar(255),
  KEY docname (docname),
  KEY  (id_bibrec),
  KEY  (id_bibdoc)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibdoc_bibdoc (
  id mediumint(9) unsigned NOT NULL auto_increment,
  id_bibdoc1 mediumint(9) unsigned DEFAULT NULL,
  version1 tinyint(4) unsigned, -- NULL means all versions
  format1 varchar(50),
  id_bibdoc2 mediumint(9) unsigned DEFAULT NULL,
  version2 tinyint(4) unsigned, -- NULL means all versions
  format2 varchar(50),
  rel_type varchar(255),
  KEY  (id_bibdoc1),
  KEY  (id_bibdoc2),
  KEY  (id)
) ENGINE=MyISAM;

-- Storage of moreInfo fields
CREATE TABLE IF NOT EXISTS bibdocmoreinfo (
  id_bibdoc mediumint(9) unsigned DEFAULT NULL,
  version tinyint(4) unsigned DEFAULT NULL, -- NULL means all versions
  format VARCHAR(50) DEFAULT NULL,
  id_rel mediumint(9) unsigned DEFAULT NULL,
  namespace VARCHAR(25) DEFAULT NULL, -- namespace in the moreinfo dictionary
  data_key VARCHAR(25), -- key in the moreinfo dictionary
  data_value MEDIUMBLOB,
  KEY (id_bibdoc, version, format, id_rel, namespace, data_key)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bibdocfsinfo (
  id_bibdoc mediumint(9) unsigned NOT NULL,
  version tinyint(4) unsigned NOT NULL,
  format varchar(50) NOT NULL,
  last_version boolean NOT NULL,
  cd datetime NOT NULL,
  md datetime NOT NULL,
  checksum char(32) NOT NULL,
  filesize bigint(15) unsigned NOT NULL,
  mime varchar(100) NOT NULL,
  master_format varchar(50) NULL default NULL,
  PRIMARY KEY (id_bibdoc, version, format),
  KEY (last_version),
  KEY (format),
  KEY (cd),
  KEY (md),
  KEY (filesize),
  KEY (mime)
) ENGINE=MyISAM;

-- tables for publication requests:

CREATE TABLE IF NOT EXISTS publreq (
  id int(11) NOT NULL auto_increment,
  host varchar(255) NOT NULL default '',
  date varchar(255) NOT NULL default '',
  name varchar(255) NOT NULL default '',
  email varchar(255) NOT NULL default '',
  address text NOT NULL,
  publication text NOT NULL,
  PRIMARY KEY  (id)
) ENGINE=MyISAM;

-- table for sessions and users:

CREATE TABLE IF NOT EXISTS session (
  session_key varchar(32) NOT NULL default '',
  session_expiry datetime NOT NULL default '0000-00-00 00:00:00',
  session_object longblob,
  uid int(15) unsigned NOT NULL,
  UNIQUE KEY session_key (session_key),
  KEY uid (uid),
  KEY session_expiry (session_expiry)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS user (
  id int(15) unsigned NOT NULL auto_increment,
  email varchar(255) NOT NULL default '',
  password blob NOT NULL,
  note varchar(255) default NULL,
  settings blob default NULL,
  nickname varchar(255) NOT NULL default '',
  last_login datetime NOT NULL default '0000-00-00 00:00:00',
  PRIMARY KEY id (id),
  KEY email (email),
  KEY nickname (nickname)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS userEXT (
  id varbinary(255) NOT NULL,
  method varchar(50) NOT NULL,
  id_user int(15) unsigned NOT NULL,
  PRIMARY KEY (id, method),
  UNIQUE KEY (id_user, method)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS oauth1_storage (
  token varchar(255) NOT NULL,
  secret varchar(255) NOT NULL,
  date_creation datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
  PRIMARY KEY (token)
) ENGINE=MyISAM;

-- tables for usergroups

CREATE TABLE IF NOT EXISTS usergroup (
  id int(15) unsigned NOT NULL auto_increment,
  name varchar(255) NOT NULL default '',
  description text default '',
  join_policy char(2) NOT NULL default '',
  login_method varchar(255) NOT NULL default 'INTERNAL',
  PRIMARY KEY  (id),
  UNIQUE KEY login_method_name (login_method(70), name),
  KEY name (name)
) ENGINE=MyISAM;


CREATE TABLE IF NOT EXISTS user_usergroup (
  id_user int(15) unsigned NOT NULL default '0',
  id_usergroup int(15) unsigned NOT NULL default '0',
  user_status char(1) NOT NULL default '',
  user_status_date datetime NOT NULL default '0000-00-00 00:00:00',
  KEY id_user (id_user),
  KEY id_usergroup (id_usergroup)
) ENGINE=MyISAM;

-- tables for access control engine

CREATE TABLE IF NOT EXISTS accROLE (
  id int(15) unsigned NOT NULL auto_increment,
  name varchar(32),
  description varchar(255),
  firerole_def_ser blob NULL,
  firerole_def_src text NULL,
  PRIMARY KEY (id),
  UNIQUE KEY name (name)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS user_accROLE (
  id_user int(15) unsigned NOT NULL,
  id_accROLE int(15) unsigned NOT NULL,
  expiration datetime NOT NULL default '9999-12-31 23:59:59',
  PRIMARY KEY (id_user, id_accROLE)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS accMAILCOOKIE (
  id int(15) unsigned NOT NULL auto_increment,
  data blob NOT NULL,
  expiration datetime NOT NULL default '9999-12-31 23:59:59',
  kind varchar(32) NOT NULL,
  onetime boolean NOT NULL default 0,
  status char(1) NOT NULL default 'W',
  PRIMARY KEY (id),
  KEY expiration (expiration)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS accACTION (
  id int(15) unsigned NOT NULL auto_increment,
  name varchar(32),
  description varchar(255),
  allowedkeywords varchar(255),
  optional ENUM ('yes', 'no') NOT NULL default 'no',
  PRIMARY KEY (id),
  UNIQUE KEY name (name)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS accARGUMENT (
  id int(15) unsigned NOT NULL auto_increment,
  keyword varchar (32),
  value varchar(255),
  PRIMARY KEY (id),
  KEY KEYVAL (keyword, value)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS accROLE_accACTION_accARGUMENT (
  id_accROLE int(15),
  id_accACTION int(15),
  id_accARGUMENT int(15),
  argumentlistid mediumint(8),
  KEY id_accROLE     (id_accROLE),
  KEY id_accACTION   (id_accACTION),
  KEY id_accARGUMENT (id_accARGUMENT)
) ENGINE=MyISAM;

-- tables for personal/collaborative features (baskets, alerts, searches, messages, usergroups):

CREATE TABLE IF NOT EXISTS user_query (
  id_user int(15) unsigned NOT NULL default '0',
  id_query int(15) unsigned NOT NULL default '0',
  hostname varchar(50) default 'unknown host',
  date datetime default NULL,
  KEY id_user (id_user,id_query)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS query (
  id int(15) unsigned NOT NULL auto_increment,
  type char(1) NOT NULL default 'r',
  urlargs text NOT NULL,
  PRIMARY KEY  (id),
  KEY urlargs (urlargs(100))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS user_query_basket (
  id_user int(15) unsigned NOT NULL default '0',
  id_query int(15) unsigned NOT NULL default '0',
  id_basket int(15) unsigned NOT NULL default '0',
  frequency varchar(5) NOT NULL default '',
  date_creation date default NULL,
  date_lastrun date default '0000-00-00',
  alert_name varchar(30) NOT NULL default '',
  alert_desc text default NULL,
  alert_recipient text default NULL,
  notification char(1) NOT NULL default 'y',
  PRIMARY KEY  (id_user,id_query,frequency,id_basket),
  KEY alert_name (alert_name)
) ENGINE=MyISAM;

-- baskets
CREATE TABLE IF NOT EXISTS bskBASKET (
  id int(15) unsigned NOT NULL auto_increment,
  id_owner int(15) unsigned NOT NULL default '0',
  name varchar(50) NOT NULL default '',
  date_modification datetime NOT NULL default '0000-00-00 00:00:00',
  nb_views int(15) NOT NULL default '0',
  PRIMARY KEY  (id),
  KEY id_owner (id_owner),
  KEY name (name)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bskREC (
  id_bibrec_or_bskEXTREC int(16) NOT NULL default '0',
  id_bskBASKET int(15) unsigned NOT NULL default '0',
  id_user_who_added_item int(15) NOT NULL default '0',
  score int(15) NOT NULL default '0',
  date_added datetime NOT NULL default '0000-00-00 00:00:00',
  PRIMARY KEY  (id_bibrec_or_bskEXTREC,id_bskBASKET),
  KEY id_bibrec_or_bskEXTREC (id_bibrec_or_bskEXTREC),
  KEY id_bskBASKET (id_bskBASKET),
  KEY score (score),
  KEY date_added (date_added)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bskEXTREC (
  id int(15) unsigned NOT NULL auto_increment,
  external_id int(15) NOT NULL default '0',
  collection_id int(15) unsigned NOT NULL default '0',
  original_url text,
  creation_date datetime NOT NULL default '0000-00-00 00:00:00',
  modification_date datetime NOT NULL default '0000-00-00 00:00:00',
  PRIMARY KEY  (id)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bskEXTFMT (
   id int(15) unsigned NOT NULL auto_increment,
   id_bskEXTREC int(15) unsigned NOT NULL default '0',
   format varchar(10) NOT NULL default '',
   last_updated datetime NOT NULL default '0000-00-00 00:00:00',
   value longblob,
   PRIMARY KEY (id),
   KEY id_bskEXTREC (id_bskEXTREC),
   KEY format (format)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS user_bskBASKET (
  id_user int(15) unsigned NOT NULL default '0',
  id_bskBASKET int(15) unsigned NOT NULL default '0',
  topic varchar(50) NOT NULL default '',
  PRIMARY KEY  (id_user,id_bskBASKET),
  KEY id_user (id_user),
  KEY id_bskBASKET (id_bskBASKET)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS usergroup_bskBASKET (
  id_usergroup int(15) unsigned NOT NULL default '0',
  id_bskBASKET int(15) unsigned NOT NULL default '0',
  topic varchar(50) NOT NULL default '',
  date_shared datetime NOT NULL default '0000-00-00 00:00:00',
  share_level char(2) NOT NULL default '',
  PRIMARY KEY  (id_usergroup,id_bskBASKET),
  KEY id_usergroup (id_usergroup),
  KEY id_bskBASKET (id_bskBASKET)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bskRECORDCOMMENT (
  id int(15) unsigned NOT NULL auto_increment,
  id_bibrec_or_bskEXTREC int(16) NOT NULL default '0',
  id_bskBASKET int(15) unsigned NOT NULL default '0',
  id_user int(15) unsigned NOT NULL default '0',
  title varchar(255) NOT NULL default '',
  body text NOT NULL,
  date_creation datetime NOT NULL default '0000-00-00 00:00:00',
  priority int(15) NOT NULL default '0',
  in_reply_to_id_bskRECORDCOMMENT int(15) unsigned NOT NULL default '0',
  reply_order_cached_data blob NULL default NULL,
  PRIMARY KEY  (id),
  KEY id_bskBASKET (id_bskBASKET),
  KEY id_bibrec_or_bskEXTREC (id_bibrec_or_bskEXTREC),
  KEY date_creation (date_creation),
  KEY in_reply_to_id_bskRECORDCOMMENT (in_reply_to_id_bskRECORDCOMMENT),
  INDEX (reply_order_cached_data(40))
) ENGINE=MyISAM;

-- tables for messaging system

CREATE TABLE IF NOT EXISTS msgMESSAGE (
  id int(15) unsigned NOT NULL auto_increment,
  id_user_from int(15) unsigned NOT NULL default '0',
  sent_to_user_nicks text NOT NULL default '',
  sent_to_group_names text NOT NULL default '',
  subject text NOT NULL default '',
  body text default NULL,
  sent_date datetime NOT NULL default '0000-00-00 00:00:00',
  received_date datetime NULL default '0000-00-00 00:00:00',
  PRIMARY KEY id (id),
  KEY id_user_from (id_user_from)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS user_msgMESSAGE (
  id_user_to int(15) unsigned NOT NULL default '0',
  id_msgMESSAGE int(15) unsigned NOT NULL default '0',
  status char(1) NOT NULL default 'N',
  PRIMARY KEY id (id_user_to, id_msgMESSAGE),
  KEY id_user_to (id_user_to),
  KEY id_msgMESSAGE (id_msgMESSAGE)
) ENGINE=MyISAM;

-- tables for WebComment

CREATE TABLE IF NOT EXISTS cmtRECORDCOMMENT (
  id int(15) unsigned NOT NULL auto_increment,
  id_bibrec int(15) unsigned NOT NULL default '0',
  id_user int(15) unsigned NOT NULL default '0',
  title varchar(255) NOT NULL default '',
  body text NOT NULL default '',
  date_creation datetime NOT NULL default '0000-00-00 00:00:00',
  star_score tinyint(5) unsigned NOT NULL default '0',
  nb_votes_yes int(10) NOT NULL default '0',
  nb_votes_total int(10) unsigned NOT NULL default '0',
  nb_abuse_reports int(10) NOT NULL default '0',
  status char(2) NOT NULL default 'ok',
  round_name varchar(255) NOT NULL default '',
  restriction varchar(50) NOT NULL default '',
  in_reply_to_id_cmtRECORDCOMMENT int(15) unsigned NOT NULL default '0',
  reply_order_cached_data blob NULL default NULL,
  PRIMARY KEY  (id),
  KEY id_bibrec (id_bibrec),
  KEY id_user (id_user),
  KEY status (status),
  KEY in_reply_to_id_cmtRECORDCOMMENT (in_reply_to_id_cmtRECORDCOMMENT),
  INDEX (reply_order_cached_data(40))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS cmtACTIONHISTORY (
  id_cmtRECORDCOMMENT int(15) unsigned NULL,
  id_bibrec int(15) unsigned NULL,
  id_user int(15) unsigned NULL default NULL,
  client_host int(10) unsigned default NULL,
  action_time datetime NOT NULL default '0000-00-00 00:00:00',
  action_code char(1) NOT NULL,
  KEY id_cmtRECORDCOMMENT (id_cmtRECORDCOMMENT),
  KEY client_host (client_host),
  KEY id_user (id_user),
  KEY action_code (action_code)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS cmtSUBSCRIPTION (
  id_bibrec mediumint(8) unsigned NOT NULL,
  id_user int(15) unsigned NOT NULL,
  creation_time datetime NOT NULL default '0000-00-00 00:00:00',
  KEY id_user (id_bibrec, id_user)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS cmtCOLLAPSED (
  id_bibrec int(15) unsigned NOT NULL default '0',
  id_cmtRECORDCOMMENT int(15) unsigned NULL,
  id_user int(15) unsigned NOT NULL,
  PRIMARY KEY (id_user, id_bibrec, id_cmtRECORDCOMMENT)
) ENGINE=MyISAM;

-- tables for BibKnowledge:

CREATE TABLE IF NOT EXISTS knwKB (
  id mediumint(8) unsigned NOT NULL auto_increment,
  name varchar(255) default '',
  description text default '',
  kbtype char default NULL,
  PRIMARY KEY  (id),
  UNIQUE KEY name (name)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS knwKBRVAL (
  id mediumint(8) unsigned NOT NULL auto_increment,
  m_key varchar(255) NOT NULL default '',
  m_value text NOT NULL default '',
  id_knwKB mediumint(8) NOT NULL default '0',
  PRIMARY KEY  (id),
  KEY id_knwKB (id_knwKB),
  KEY m_key (m_key(30)),
  KEY m_value (m_value(30))
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS knwKBDDEF (
  id_knwKB mediumint(8) unsigned NOT NULL,
  id_collection mediumint(9),
  output_tag text default '',
  search_expression text default '',
  PRIMARY KEY  (id_knwKB)
) ENGINE=MyISAM;

-- tables for WebSubmit:

CREATE TABLE IF NOT EXISTS sbmACTION (
  lactname text,
  sactname char(3) NOT NULL default '',
  dir text,
  cd date default NULL,
  md date default NULL,
  actionbutton text,
  statustext text,
  PRIMARY KEY  (sactname)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS sbmALLFUNCDESCR (
  function varchar(40) NOT NULL default '',
  description tinytext,
  PRIMARY KEY  (function)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS sbmAPPROVAL (
  doctype varchar(10) NOT NULL default '',
  categ varchar(50) NOT NULL default '',
  rn varchar(50) NOT NULL default '',
  status varchar(10) NOT NULL default '',
  dFirstReq datetime NOT NULL default '0000-00-00 00:00:00',
  dLastReq datetime NOT NULL default '0000-00-00 00:00:00',
  dAction datetime NOT NULL default '0000-00-00 00:00:00',
  access varchar(20) NOT NULL default '0',
  note text NOT NULL default '',
  PRIMARY KEY  (rn)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS sbmCPLXAPPROVAL (
  doctype varchar(10) NOT NULL default '',
  categ varchar(50) NOT NULL default '',
  rn varchar(50) NOT NULL default '',
  type varchar(10) NOT NULL,
  status varchar(10) NOT NULL,
  id_group int(15) unsigned NOT NULL default '0',
  id_bskBASKET int(15) unsigned NOT NULL default '0',
  id_EdBoardGroup int(15) unsigned NOT NULL default '0',
  dFirstReq datetime NOT NULL default '0000-00-00 00:00:00',
  dLastReq datetime NOT NULL default '0000-00-00 00:00:00',
  dEdBoardSel datetime NOT NULL default '0000-00-00 00:00:00',
  dRefereeSel datetime NOT NULL default '0000-00-00 00:00:00',
  dRefereeRecom datetime NOT NULL default '0000-00-00 00:00:00',
  dEdBoardRecom datetime NOT NULL default '0000-00-00 00:00:00',
  dPubComRecom datetime NOT NULL default '0000-00-00 00:00:00',
  dProjectLeaderAction datetime NOT NULL default '0000-00-00 00:00:00',
  PRIMARY KEY  (rn, type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS sbmCOLLECTION (
  id int(11) NOT NULL auto_increment,
  name varchar(100) NOT NULL default '',
  PRIMARY KEY  (id)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS sbmCOLLECTION_sbmCOLLECTION (
  id_father int(11) NOT NULL default '0',
  id_son int(11) NOT NULL default '0',
  catalogue_order int(11) NOT NULL default '0'
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS sbmCOLLECTION_sbmDOCTYPE (
  id_father int(11) NOT NULL default '0',
  id_son char(10) NOT NULL default '0',
  catalogue_order int(11) NOT NULL default '0'
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS sbmCATEGORIES (
  doctype varchar(10) NOT NULL default '',
  sname varchar(75) NOT NULL default '',
  lname varchar(75) NOT NULL default '',
  score tinyint unsigned NOT NULL default 0,
  PRIMARY KEY (doctype, sname),
  KEY doctype (doctype),
  KEY sname (sname)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS sbmCHECKS (
  chname varchar(15) NOT NULL default '',
  chdesc text,
  cd date default NULL,
  md date default NULL,
  chefi1 text,
  chefi2 text,
  PRIMARY KEY  (chname)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS sbmDOCTYPE (
  ldocname text,
  sdocname varchar(10) default NULL,
  cd date default NULL,
  md date default NULL,
  description text
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS sbmFIELD (
  subname varchar(13) default NULL,
  pagenb int(11) default NULL,
  fieldnb int(11) default NULL,
  fidesc varchar(15) default NULL,
  fitext text,
  level char(1) default NULL,
  sdesc text,
  checkn text,
  cd date default NULL,
  md date default NULL,
  fiefi1 text,
  fiefi2 text
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS sbmFIELDDESC (
  name varchar(15) NOT NULL default '',
  alephcode varchar(50) default NULL,
  marccode varchar(50) NOT NULL default '',
  type char(1) default NULL,
  size int(11) default NULL,
  rows int(11) default NULL,
  cols int(11) default NULL,
  maxlength int(11) default NULL,
  val text,
  fidesc text,
  cd date default NULL,
  md date default NULL,
  modifytext text,
  fddfi2 text,
  cookie int(11) default '0',
  PRIMARY KEY  (name)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS sbmFORMATEXTENSION (
  FILE_FORMAT text NOT NULL,
  FILE_EXTENSION text NOT NULL
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS sbmFUNCTIONS (
  action varchar(10) NOT NULL default '',
  doctype varchar(10) NOT NULL default '',
  function varchar(40) NOT NULL default '',
  score int(11) NOT NULL default '0',
  step tinyint(4) NOT NULL default '1'
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS sbmFUNDESC (
  function varchar(40) NOT NULL default '',
  param varchar(40) default NULL
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS sbmGFILERESULT (
  FORMAT text NOT NULL,
  RESULT text NOT NULL
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS sbmIMPLEMENT (
  docname varchar(10) default NULL,
  actname char(3) default NULL,
  displayed char(1) default NULL,
  subname varchar(13) default NULL,
  nbpg int(11) default NULL,
  cd date default NULL,
  md date default NULL,
  buttonorder int(11) default NULL,
  statustext text,
  level char(1) NOT NULL default '',
  score int(11) NOT NULL default '0',
  stpage int(11) NOT NULL default '0',
  endtxt varchar(100) NOT NULL default ''
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS sbmPARAMETERS (
  doctype varchar(10) NOT NULL default '',
  name varchar(40) NOT NULL default '',
  value text NOT NULL default '',
  PRIMARY KEY  (doctype,name)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS sbmPUBLICATION (
  doctype varchar(10) NOT NULL default '',
  categ varchar(50) NOT NULL default '',
  rn varchar(50) NOT NULL default '',
  status varchar(10) NOT NULL default '',
  dFirstReq datetime NOT NULL default '0000-00-00 00:00:00',
  dLastReq datetime NOT NULL default '0000-00-00 00:00:00',
  dAction datetime NOT NULL default '0000-00-00 00:00:00',
  accessref varchar(20) NOT NULL default '',
  accessedi varchar(20) NOT NULL default '',
  access varchar(20) NOT NULL default '',
  referees varchar(50) NOT NULL default '',
  authoremail varchar(50) NOT NULL default '',
  dRefSelection datetime NOT NULL default '0000-00-00 00:00:00',
  dRefRec datetime NOT NULL default '0000-00-00 00:00:00',
  dEdiRec datetime NOT NULL default '0000-00-00 00:00:00',
  accessspo varchar(20) NOT NULL default '',
  journal varchar(100) default NULL,
  PRIMARY KEY  (doctype,categ,rn)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS sbmPUBLICATIONCOMM (
  id int(11) NOT NULL auto_increment,
  id_parent int(11) default '0',
  rn varchar(100) NOT NULL default '',
  firstname varchar(100) default NULL,
  secondname varchar(100) default NULL,
  email varchar(100) default NULL,
  date varchar(40) NOT NULL default '',
  synopsis varchar(255) NOT NULL default '',
  commentfulltext text,
  PRIMARY KEY  (id)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS sbmPUBLICATIONDATA (
  doctype varchar(10) NOT NULL default '',
  editoboard varchar(250) NOT NULL default '',
  base varchar(10) NOT NULL default '',
  logicalbase varchar(10) NOT NULL default '',
  spokesperson varchar(50) NOT NULL default '',
  PRIMARY KEY  (doctype)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS sbmREFEREES (
  doctype varchar(10) NOT NULL default '',
  categ varchar(10) NOT NULL default '',
  name varchar(50) NOT NULL default '',
  address varchar(50) NOT NULL default '',
  rid int(11) NOT NULL auto_increment,
  PRIMARY KEY  (rid)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS sbmSUBMISSIONS (
  email varchar(50) NOT NULL default '',
  doctype varchar(10) NOT NULL default '',
  action varchar(10) NOT NULL default '',
  status varchar(10) NOT NULL default '',
  id varchar(30) NOT NULL default '',
  reference varchar(40) NOT NULL default '',
  cd datetime NOT NULL default '0000-00-00 00:00:00',
  md datetime NOT NULL default '0000-00-00 00:00:00'
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS sbmCOOKIES (
  id int(15) unsigned NOT NULL auto_increment,
  name varchar(100) NOT NULL,
  value text,
  uid int(15) NOT NULL,
  PRIMARY KEY  (id)
) ENGINE=MyISAM;

-- Scheduler tables

CREATE TABLE IF NOT EXISTS schTASK (
  id int(15) unsigned NOT NULL auto_increment,
  proc varchar(255) NOT NULL,
  host varchar(255) NOT NULL default '',
  user varchar(50) NOT NULL,
  runtime datetime NOT NULL,
  sleeptime varchar(20),
  arguments mediumblob,
  status varchar(50),
  progress varchar(255),
  priority tinyint(4) NOT NULL default 0,
  sequenceid int(8) NULL default NULL,
  PRIMARY KEY  (id),
  KEY status (status),
  KEY runtime (runtime),
  KEY priority (priority),
  KEY sequenceid (sequenceid)
) ENGINE=MyISAM;

-- FIXME, To be moved to redis when available
CREATE TABLE IF NOT EXISTS schSTATUS (
  name varchar(50),
  value mediumblob,
  PRIMARY KEY (name)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS hstTASK (
  id int(15) unsigned NOT NULL,
  proc varchar(255) NOT NULL,
  host varchar(255) NOT NULL default '',
  user varchar(50) NOT NULL,
  runtime datetime NOT NULL,
  sleeptime varchar(20),
  arguments mediumblob,
  status varchar(50),
  progress varchar(255),
  priority tinyint(4) NOT NULL default 0,
  sequenceid int(8) NULL default NULL,
  PRIMARY KEY  (id),
  KEY status (status),
  KEY runtime (runtime),
  KEY priority (priority),
  KEY sequenceid (sequenceid)
) ENGINE=MyISAM;

-- Batch Upload History

CREATE TABLE IF NOT EXISTS hstBATCHUPLOAD (
  id int(15) unsigned NOT NULL auto_increment,
  user varchar(50) NOT NULL,
  submitdate datetime NOT NULL,
  filename varchar(255) NOT NULL,
  execdate datetime NOT NULL,
  id_schTASK int(15) unsigned NOT NULL,
  batch_mode varchar(15) NOT NULL,
  PRIMARY KEY (id),
  KEY user (user)
) ENGINE=MyISAM;

-- External collections

CREATE TABLE IF NOT EXISTS collection_externalcollection (
  id_collection         mediumint(9) unsigned NOT NULL default '0',
  id_externalcollection mediumint(9) unsigned NOT NULL default '0',
  type tinyint(4) unsigned NOT NULL default '0',
  PRIMARY KEY (id_collection, id_externalcollection)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS externalcollection (
  id mediumint(9) unsigned NOT NULL auto_increment,
  name varchar(255) NOT NULL default '',
  PRIMARY KEY (id),
  UNIQUE KEY name (name)
) ENGINE=MyISAM;

-- WebStat tables:

CREATE TABLE IF NOT EXISTS staEVENT (
  id varchar(255) NOT NULL,
  number smallint(2) unsigned ZEROFILL NOT NULL auto_increment,
  name varchar(255),
  creation_time TIMESTAMP DEFAULT NOW(),
  cols varchar(255),
  PRIMARY KEY  (id),
  UNIQUE KEY number (number)
) ENGINE=MyISAM;

-- BibClassify tables:

CREATE TABLE IF NOT EXISTS clsMETHOD (
  id mediumint(9) unsigned NOT NULL,
  name varchar(50) NOT NULL default '',
  location varchar(255) NOT NULL default '',
  description varchar(255) NOT NULL default '',
  last_updated datetime NOT NULL default '0000-00-00 00:00:00',
  PRIMARY KEY  (id),
  UNIQUE KEY name (name)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS collection_clsMETHOD (
  id_collection mediumint(9) unsigned NOT NULL,
  id_clsMETHOD mediumint(9) unsigned NOT NULL,
  PRIMARY KEY  (id_collection, id_clsMETHOD)
) ENGINE=MyISAM;

-- WebJournal tables:

CREATE TABLE IF NOT EXISTS jrnJOURNAL (
  id mediumint(9) unsigned NOT NULL auto_increment,
  name varchar(50) NOT NULL default '',
  PRIMARY KEY (id),
  UNIQUE KEY name (name)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS jrnISSUE (
  id_jrnJOURNAL mediumint(9) unsigned NOT NULL,
  issue_number varchar(50) NOT NULL default '',
  issue_display varchar(50) NOT NULL default '',
  date_released datetime NOT NULL default '0000-00-00 00:00:00',
  date_announced datetime NOT NULL default '0000-00-00 00:00:00',
  PRIMARY KEY (id_jrnJOURNAL,issue_number)
) ENGINE=MyISAM;

-- tables recording history of record's metadata and fulltext documents:

CREATE TABLE IF NOT EXISTS hstRECORD (
  id_bibrec mediumint(8) unsigned NOT NULL,
  marcxml longblob NOT NULL,
  job_id mediumint(15) unsigned NOT NULL,
  job_name varchar(255) NOT NULL,
  job_person varchar(255) NOT NULL,
  job_date datetime NOT NULL,
  job_details blob NOT NULL,
  affected_fields text NOT NULL default '',
  KEY (id_bibrec),
  KEY (job_id),
  KEY (job_name),
  KEY (job_person),
  KEY (job_date)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS hstDOCUMENT (
  id_bibdoc mediumint(9) unsigned NOT NULL,
  docname varchar(250) NOT NULL,
  docformat varchar(50) NOT NULL,
  docversion tinyint(4) unsigned NOT NULL,
  docsize bigint(15) unsigned NOT NULL,
  docchecksum char(32) NOT NULL,
  doctimestamp datetime NOT NULL,
  action varchar(50) NOT NULL,
  job_id mediumint(15) unsigned NULL default NULL,
  job_name varchar(255) NULL default NULL,
  job_person varchar(255) NULL default NULL,
  job_date datetime NULL default NULL,
  job_details blob NULL default NULL,
  KEY (action),
  KEY (id_bibdoc),
  KEY (docname),
  KEY (docformat),
  KEY (doctimestamp),
  KEY (job_id),
  KEY (job_name),
  KEY (job_person),
  KEY (job_date)
) ENGINE=MyISAM;

-- BibCirculation tables:

CREATE TABLE IF NOT EXISTS crcBORROWER (
  id int(15) unsigned NOT NULL auto_increment,
  ccid int(15) unsigned NULL default NULL,
  name varchar(255) NOT NULL default '',
  email varchar(255) NOT NULL default '',
  phone varchar(60) default NULL,
  address varchar(60) default NULL,
  mailbox varchar(30) default NULL,
  borrower_since datetime NOT NULL default '0000-00-00 00:00:00',
  borrower_until datetime NOT NULL default '0000-00-00 00:00:00',
  notes text,
  PRIMARY KEY  (id),
  UNIQUE KEY (ccid),
  KEY (name),
  KEY (email)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS crcILLREQUEST (
  id int(15) unsigned NOT NULL auto_increment,
  id_crcBORROWER int(15) unsigned NOT NULL default '0',
  barcode varchar(30) NOT NULL default '',
  period_of_interest_from datetime NOT NULL default '0000-00-00 00:00:00',
  period_of_interest_to datetime NOT NULL default '0000-00-00 00:00:00',
  id_crcLIBRARY int(15) unsigned NOT NULL default '0',
  request_date datetime NOT NULL default '0000-00-00 00:00:00',
  expected_date datetime NOT NULL default '0000-00-00 00:00:00',
  arrival_date datetime NOT NULL default '0000-00-00 00:00:00',
  due_date datetime NOT NULL default '0000-00-00 00:00:00',
  return_date datetime NOT NULL default '0000-00-00 00:00:00',
  status varchar(20) NOT NULL default '',
  cost varchar(30) NOT NULL default '',
  budget_code varchar(60) NOT NULL default '',
  item_info text,
  request_type text,
  borrower_comments text,
  only_this_edition varchar(10) NOT NULL default '',
  library_notes text,
  overdue_letter_number int(3) unsigned NOT NULL default '0',
  overdue_letter_date datetime NOT NULL default '0000-00-00 00:00:00',
  PRIMARY KEY (id),
  KEY id_crcborrower (id_crcBORROWER),
  KEY id_crclibrary (id_crcLIBRARY)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS crcITEM (
  barcode varchar(30) NOT NULL default '',
  id_bibrec int(15) unsigned NOT NULL default '0',
  id_crcLIBRARY int(15) unsigned NOT NULL default '0',
  collection varchar(60) default NULL,
  location varchar(60) default NULL,
  description varchar(60) default NULL,
  loan_period varchar(30) NOT NULL default '',
  status varchar(20) NOT NULL default '',
  expected_arrival_date varchar(60) NOT NULL default '',
  creation_date datetime NOT NULL default '0000-00-00 00:00:00',
  modification_date datetime NOT NULL default '0000-00-00 00:00:00',
  number_of_requests int(3) unsigned NOT NULL default '0',
  PRIMARY KEY (barcode),
  KEY id_bibrec (id_bibrec),
  KEY id_crclibrary (id_crcLIBRARY)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS crcLIBRARY (
  id int(15) unsigned NOT NULL auto_increment,
  name varchar(80) NOT NULL default '',
  address varchar(255) NOT NULL default '',
  email varchar(255) NOT NULL default '',
  phone varchar(30) NOT NULL default '',
  type varchar(30) NOT NULL default 'main',
  notes text,
  PRIMARY KEY (id)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS crcLOAN (
  id int(15) unsigned NOT NULL auto_increment,
  id_crcBORROWER int(15) unsigned NOT NULL default '0',
  id_bibrec int(15) unsigned NOT NULL default '0',
  barcode varchar(30) NOT NULL default '',
  loaned_on datetime NOT NULL default '0000-00-00 00:00:00',
  returned_on date NOT NULL default '0000-00-00',
  due_date datetime NOT NULL default '0000-00-00 00:00:00',
  number_of_renewals int(3) unsigned NOT NULL default '0',
  overdue_letter_number int(3) unsigned NOT NULL default '0',
  overdue_letter_date datetime NOT NULL default '0000-00-00 00:00:00',
  status varchar(20) NOT NULL default '',
  type varchar(20) NOT NULL default '',
  notes text,
  PRIMARY KEY (id),
  KEY id_crcborrower (id_crcBORROWER),
  KEY id_bibrec (id_bibrec),
  KEY barcode (barcode)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS crcLOANREQUEST (
  id int(15) unsigned NOT NULL auto_increment,
  id_crcBORROWER int(15) unsigned NOT NULL default '0',
  id_bibrec int(15) unsigned NOT NULL default '0',
  barcode varchar(30) NOT NULL default '',
  period_of_interest_from datetime NOT NULL default '0000-00-00 00:00:00',
  period_of_interest_to datetime NOT NULL default '0000-00-00 00:00:00',
  status varchar(20) NOT NULL default '',
  notes text,
  request_date datetime NOT NULL default '0000-00-00 00:00:00',
  PRIMARY KEY (id),
  KEY id_crcborrower (id_crcBORROWER),
  KEY id_bibrec (id_bibrec),
  KEY barcode (barcode)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS crcPURCHASE (
  id int(15) unsigned NOT NULL auto_increment,
  id_bibrec int(15) unsigned NOT NULL default '0',
  id_crcVENDOR int(15) unsigned NOT NULL default '0',
  ordered_date datetime NOT NULL default '0000-00-00 00:00:00',
  expected_date datetime NOT NULL default '0000-00-00 00:00:00',
  price varchar(20) NOT NULL default '0',
  status varchar(20) NOT NULL default '',
  notes text,
  PRIMARY KEY (id),
  KEY id_bibrec (id_bibrec),
  KEY id_crcVENDOR (id_crcVENDOR)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS crcVENDOR (
  id int(15) unsigned NOT NULL auto_increment,
  name varchar(80) NOT NULL default '',
  address varchar(255) NOT NULL default '',
  email varchar(255) NOT NULL default '',
  phone varchar(30) NOT NULL default '',
  notes text,
  PRIMARY KEY (id)
) ENGINE=MyISAM;

-- BibExport tables:

CREATE TABLE IF NOT EXISTS expJOB (
  id int(15) unsigned NOT NULL auto_increment,
  jobname varchar(50) NOT NULL default '',
  jobfreq mediumint(12) NOT NULL default '0',
  output_format mediumint(12) NOT NULL default '0',
  deleted mediumint(12) NOT NULL default '0',
  lastrun datetime NOT NULL default '0000-00-00 00:00:00',
  output_directory text,
  PRIMARY KEY (id),
  UNIQUE KEY jobname (jobname)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS expQUERY (
  id int(15) unsigned NOT NULL auto_increment,
  name varchar(255) NOT NULL,
  search_criteria text NOT NULL,
  output_fields text NOT NULL,
  notes text,
  deleted mediumint(12) NOT NULL default '0',
  PRIMARY KEY (id)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS expJOB_expQUERY (
  id_expJOB int(15) NOT NULL,
  id_expQUERY int(15) NOT NULL,
  PRIMARY KEY (id_expJOB,id_expQUERY),
  KEY id_expJOB (id_expJOB),
  KEY id_expQUERY (id_expQUERY)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS expQUERYRESULT (
  id int(15) unsigned NOT NULL auto_increment,
  id_expQUERY int(15) NOT NULL,
  result text NOT NULL,
  status mediumint(12) NOT NULL default '0',
  status_message text NOT NULL,
  PRIMARY KEY (id)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS expJOBRESULT (
  id int(15) unsigned NOT NULL auto_increment,
  id_expJOB int(15) NOT NULL,
  execution_time datetime NOT NULL default '0000-00-00 00:00:00',
  status mediumint(12) NOT NULL default '0',
  status_message text NOT NULL,
  PRIMARY KEY (id)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS expJOBRESULT_expQUERYRESULT (
  id_expJOBRESULT int(15) NOT NULL,
  id_expQUERYRESULT int(15) NOT NULL,
  PRIMARY KEY (id_expJOBRESULT, id_expQUERYRESULT),
  KEY id_expJOBRESULT (id_expJOBRESULT),
  KEY id_expQUERYRESULT (id_expQUERYRESULT)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS user_expJOB (
  id_user int(15) NOT NULL,
  id_expJOB int(15) NOT NULL,
  PRIMARY KEY (id_user, id_expJOB),
  KEY id_user (id_user),
  KEY id_expJOB (id_expJOB)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS swrREMOTESERVER (
  id int(15) unsigned NOT NULL auto_increment,
  name varchar(50) unique NOT NULL,
  host varchar(50) NOT NULL,
  username varchar(50) NOT NULL,
  password varchar(50) NOT NULL,
  email varchar(50) NOT NULL,
  realm varchar(50) NOT NULL,
  url_base_record varchar(50) NOT NULL,
  url_servicedocument varchar(80) NOT NULL,
  xml_servicedocument longblob,
  last_update int(15) unsigned NOT NULL,
  PRIMARY KEY (id)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS swrCLIENTDATA (
  id int(15) unsigned NOT NULL auto_increment,
  id_swrREMOTESERVER int(15) NOT NULL,
  id_record int(15) NOT NULL,
  report_no varchar(50) NOT NULL,
  id_remote varchar(50) NOT NULL,
  id_user int(15) NOT NULL,
  user_name varchar(100) NOT NULL,
  user_email varchar(100) NOT NULL,
  xml_media_deposit longblob NOT NULL,
  xml_metadata_submit longblob NOT NULL,
  submission_date datetime NOT NULL default '0000-00-00 00:00:00',
  publication_date datetime NOT NULL default '0000-00-00 00:00:00',
  removal_date datetime NOT NULL default '0000-00-00 00:00:00',
  link_medias varchar(150) NOT NULL,
  link_metadata varchar(150) NOT NULL,
  link_status varchar(150) NOT NULL,
  status varchar(150) NOT NULL default 'submitted',
  last_update datetime NOT NULL,
  PRIMARY KEY (id)
) ENGINE=MyISAM;

-- tables for exception management

-- This table is used to log exceptions
-- to discover the full details of an exception either check the email
-- that are sent to CFG_SITE_ADMIN_EMAIL or look into invenio.err
CREATE TABLE IF NOT EXISTS hstEXCEPTION (
  id int(15) unsigned NOT NULL auto_increment,
  name varchar(50) NOT NULL, -- name of the exception
  filename varchar(255) NULL, -- file where the exception was raised
  line int(9) NULL, -- line at which the exception was raised
  last_seen datetime NOT NULL default '0000-00-00 00:00:00', -- last time this exception has been seen
  last_notified datetime NOT NULL default '0000-00-00 00:00:00', -- last time this exception has been notified
  counter int(15) NOT NULL default 0, -- internal counter to decide when to notify this exception
  total int(15) NOT NULL default 0, -- total number of times this exception has been seen
  PRIMARY KEY (id),
  KEY (last_seen),
  KEY (last_notified),
  KEY (total),
  UNIQUE KEY (name(50), filename(255), line)
) ENGINE=MyISAM;

-- tables for BibAuthorID module:

CREATE TABLE IF NOT EXISTS `aidPERSONIDPAPERS` (
  `personid` BIGINT( 16 ) UNSIGNED NOT NULL ,
  `bibref_table` ENUM(  '100',  '700' ) NOT NULL ,
  `bibref_value` MEDIUMINT( 8 ) UNSIGNED NOT NULL ,
  `bibrec` MEDIUMINT( 8 ) UNSIGNED NOT NULL ,
  `name` VARCHAR( 256 ) NOT NULL ,
  `flag` SMALLINT( 2 ) NOT NULL DEFAULT  '0' ,
  `lcul` SMALLINT( 2 ) NOT NULL DEFAULT  '0' ,
  `last_updated` TIMESTAMP ON UPDATE CURRENT_TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ,
  INDEX `personid-b` (`personid`) ,
  INDEX `reftable-b` (`bibref_table`) ,
  INDEX `refvalue-b` (`bibref_value`) ,
  INDEX `rec-b` (`bibrec`) ,
  INDEX `name-b` (`name`) ,
  INDEX `pn-b` (`personid`, `name`) ,
  INDEX `timestamp-b` (`last_updated`) ,
  INDEX `flag-b` (`flag`) ,
  INDEX `personid-flag-b` (`personid`,`flag`),
  INDEX `ptvrf-b` (`personid`, `bibref_table`, `bibref_value`, `bibrec`, `flag`)
) ENGINE=MYISAM;

CREATE TABLE IF NOT EXISTS `aidRESULTS` (
  `personid` VARCHAR( 256 ) NOT NULL ,
  `bibref_table` ENUM(  '100',  '700' ) NOT NULL ,
  `bibref_value` MEDIUMINT( 8 ) UNSIGNED NOT NULL ,
  `bibrec` MEDIUMINT( 8 ) UNSIGNED NOT NULL ,
  INDEX `personid-b` (`personid`) ,
  INDEX `reftable-b` (`bibref_table`) ,
  INDEX `refvalue-b` (`bibref_value`) ,
  INDEX `rec-b` (`bibrec`)
) ENGINE=MYISAM;

CREATE TABLE IF NOT EXISTS `aidPERSONIDDATA` (
  `personid` BIGINT( 16 ) UNSIGNED NOT NULL ,
  `tag` VARCHAR( 64 ) NOT NULL ,
  `data` VARCHAR( 256 ) NULL DEFAULT NULL ,
  `datablob` LONGBLOB NULL DEFAULT NULL ,
  `opt1` MEDIUMINT( 8 ) NULL DEFAULT NULL ,
  `opt2` MEDIUMINT( 8 ) NULL DEFAULT NULL ,
  `opt3` VARCHAR( 256 ) NULL DEFAULT NULL ,
  `last_updated` TIMESTAMP ON UPDATE CURRENT_TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ,
  INDEX `personid-b` (`personid`) ,
  INDEX `tag-b` (`tag`) ,
  INDEX `data-b` (`data`) ,
  INDEX `opt1` (`opt1`) ,
  INDEX `timestamp-b` (`last_updated`)
) ENGINE=MYISAM;

CREATE TABLE IF NOT EXISTS `aidUSERINPUTLOG` (
  `id` bigint(15) NOT NULL AUTO_INCREMENT,
  `transactionid` bigint(15) NOT NULL,
  `timestamp` datetime NOT NULL,
  `userid` int,
  `userinfo` varchar(255) NOT NULL,
  `personid` bigint(15) NOT NULL,
  `action` varchar(50) NOT NULL,
  `tag` varchar(50) NOT NULL,
  `value` varchar(200) NOT NULL,
  `comment` text,
  PRIMARY KEY (`id`),
  INDEX `transactionid-b` (`transactionid`),
  INDEX `timestamp-b` (`timestamp`),
  INDEX `userinfo-b` (`userinfo`),
  INDEX `userid-b` (`userid`),
  INDEX `personid-b` (`personid`),
  INDEX `action-b` (`action`),
  INDEX `tag-b` (`tag`),
  INDEX `value-b` (`value`)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS `aidCACHE` (
  `id` int(15) NOT NULL auto_increment,
  `object_name` varchar(120) NOT NULL,
  `object_key` varchar(120) NOT NULL,
  `object_value` text,
  `last_updated` datetime NOT NULL,
  PRIMARY KEY  (`id`),
  INDEX `name-b` (`object_name`),
  INDEX `key-b` (`object_key`),
  INDEX `last_updated-b` (`last_updated`)
) ENGINE=MyISAM;

-- tables for search engine

CREATE TABLE IF NOT EXISTS `aidDENSEINDEX` (
 `name_id` INT( 10 ) NOT NULL,
 `person_name` VARCHAR( 256 ) NOT NULL,
 `personids` LONGBLOB NOT NULL,
 PRIMARY KEY (`name_id`)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS `aidINVERTEDLISTS` (
 `qgram` VARCHAR( 4 ) NOT NULL,
 `inverted_list` LONGBLOB NOT NULL,
 `list_cardinality` INT( 10 ) NOT NULL,
 PRIMARY KEY (`qgram`)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS `aidAFFILIATIONS` (
  `personid` BIGINT( 16 ) UNSIGNED NOT NULL ,
  `affiliation` VARCHAR( 256 ) NOT NULL,
  `last_recid` MEDIUMINT( 8 ) UNSIGNED NOT NULL,
  `last_occurence` datetime NOT NULL,
 PRIMARY KEY (`personid`)
) ENGINE=MyISAM;

-- refextract tables:

CREATE TABLE IF NOT EXISTS `xtrJOB` (
  `id` tinyint(4) NOT NULL AUTO_INCREMENT,
  `name` varchar(30) NOT NULL,
  `last_updated` datetime NOT NULL,
  `last_recid` mediumint(8) unsigned NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM;

-- tables for bibsort module

CREATE TABLE IF NOT EXISTS bsrMETHOD (
  id mediumint(8) unsigned NOT NULL auto_increment,
  name varchar(20) NOT NULL,
  definition varchar(255) NOT NULL,
  washer varchar(255) NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY (name)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bsrMETHODNAME (
  id_bsrMETHOD mediumint(8) unsigned NOT NULL,
  ln char(5) NOT NULL default '',
  type char(3) NOT NULL default 'sn',
  value varchar(255) NOT NULL,
  PRIMARY KEY (id_bsrMETHOD, ln, type)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bsrMETHODDATA (
  id_bsrMETHOD mediumint(8) unsigned NOT NULL,
  data_dict longblob,
  data_dict_ordered longblob,
  data_list_sorted longblob,
  last_updated datetime,
  PRIMARY KEY (id_bsrMETHOD)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS bsrMETHODDATABUCKET (
  id_bsrMETHOD mediumint(8) unsigned NOT NULL,
  bucket_no tinyint(2) NOT NULL,
  bucket_data longblob,
  bucket_last_value varchar(255),
  last_updated datetime,
  PRIMARY KEY (id_bsrMETHOD, bucket_no)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS collection_bsrMETHOD (
  id_collection mediumint(9) unsigned NOT NULL,
  id_bsrMETHOD mediumint(9) unsigned NOT NULL,
  score tinyint(4) unsigned NOT NULL default '0',
  PRIMARY KEY (id_collection, id_bsrMETHOD)
) ENGINE=MyISAM;

-- tables for sequence storage
CREATE TABLE IF NOT EXISTS seqSTORE (
  id int(15) NOT NULL auto_increment,
  seq_name varchar(15),
  seq_value varchar(255),
  PRIMARY KEY (id),
  UNIQUE KEY seq_name_value (seq_name, seq_value)
) ENGINE=MyISAM;

-- tables for linkbacks:

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

CREATE TABLE IF NOT EXISTS lnkENTRYLOG (
  id_lnkENTRY int(15) unsigned NOT NULL,
  id_lnkLOG int(15) unsigned NOT NULL,
  FOREIGN KEY (id_lnkENTRY) REFERENCES lnkENTRY(id),
  FOREIGN KEY (id_lnkLOG) REFERENCES lnkLOG(id)
) ENGINE=MyISAM;

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

CREATE TABLE IF NOT EXISTS lnkADMINURL (
  id int(15) unsigned NOT NULL auto_increment,
  url varchar(100) NOT NULL,
  list varchar(30) NOT NULL,
  PRIMARY KEY (id),
  UNIQUE (url),
  INDEX (list)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS lnkADMINURLLOG (
  id_lnkADMINURL int(15) unsigned NOT NULL,
  id_lnkLOG int(15) unsigned NOT NULL,
  FOREIGN KEY (id_lnkADMINURL) REFERENCES lnkADMINURL(id),
  FOREIGN KEY (id_lnkLOG) REFERENCES lnkLOG(id)
) ENGINE=MyISAM;

-- table for API key
CREATE TABLE IF NOT EXISTS webapikey (
  id varchar(150) NOT NULL,
  secret varchar(150) NOT NULL,
  id_user int(15) NOT NULL,
  status varchar(25) NOT NULL default 'OK',
  description varchar(255) default NULL,
  PRIMARY KEY (id),
  KEY (id_user),
  KEY (status)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS `wapCACHE` (
  `object_name` varchar(120) NOT NULL,
  `object_key` varchar(120) NOT NULL,
  `object_value` longblob,
  `object_status` varchar(120),
  `last_updated` datetime NOT NULL,
  PRIMARY KEY  (`object_name`,`object_key`),
  INDEX `last_updated-b` (`last_updated`),
  INDEX `status-b` (`object_status`)
) ENGINE=MyISAM;

-- table for bibedit cache
CREATE TABLE IF NOT EXISTS `bibEDITCACHE` (
  `id_bibrec` mediumint(8) unsigned NOT NULL,
  `uid` int(15) unsigned NOT NULL,
  `data` LONGBLOB,
  `post_date` datetime NOT NULL,
  `is_active` tinyint(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (`id_bibrec`, `uid`),
  INDEX `post_date` (`post_date`)
) ENGINE=MyISAM;

-- tables for goto:
CREATE TABLE IF NOT EXISTS goto (
  label varchar(150) NOT NULL,
  plugin varchar(150) NOT NULL,
  parameters text NOT NULL,
  creation_date datetime NOT NULL,
  modification_date datetime NOT NULL,
  PRIMARY KEY (label),
  KEY (creation_date),
  KEY (modification_date)
) ENGINE=MyISAM;

-- tables for bibcheck
CREATE TABLE IF NOT EXISTS bibcheck_rules (
  name varchar(150) NOT NULL,
  last_run datetime NOT NULL default '0000-00-00',
  PRIMARY KEY (name)
) ENGINE=MyISAM;

-- tables for author list manager
CREATE TABLE IF NOT EXISTS `aulPAPERS` (
  `id` int(15) unsigned NOT NULL auto_increment,
  `id_user` int(15) unsigned NOT NULL,
  `title` varchar(255) NOT NULL,
  `collaboration` varchar(255) NOT NULL,
  `experiment_number` varchar(255) NOT NULL,
  `last_modified` int unsigned NOT NULL,
  PRIMARY KEY (`id`),
  INDEX(`id_user`)
) ENGINE=MyISAM;

CREATE TABLE IF NOT EXISTS `aulREFERENCES` (
  `item` int(15) unsigned NOT NULL,
  `reference` varchar(120) NOT NULL,
  `paper_id` int(15) unsigned NOT NULL REFERENCES `aulPAPERS(id)`,
  PRIMARY KEY (`item`, `paper_id`),
  INDEX(`item`),
  INDEX(`paper_id`)
) ENGINE=MyISAM;

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
) ENGINE=MyISAM;

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
) ENGINE=MyISAM;

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
) ENGINE=MyISAM;

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
) ENGINE=MyISAM;

-- tables for invenio_upgrader
CREATE TABLE IF NOT EXISTS upgrade (
  upgrade varchar(255) NOT NULL,
  applied DATETIME NOT NULL,
  PRIMARY KEY (upgrade)
) ENGINE=MyISAM;

-- maint-1.1 upgrade recipes:
INSERT INTO upgrade (upgrade, applied) VALUES ('invenio_release_1_1_0',NOW());
INSERT INTO upgrade (upgrade, applied) VALUES ('invenio_2012_10_31_tablesorter_location',NOW());
INSERT INTO upgrade (upgrade, applied) VALUES ('invenio_2012_11_01_lower_user_email',NOW());
INSERT INTO upgrade (upgrade, applied) VALUES ('invenio_2012_11_21_aiduserinputlog_userid_check',NOW());
INSERT INTO upgrade (upgrade, applied) VALUES ('invenio_2012_11_15_hstRECORD_marcxml_longblob',NOW());
INSERT INTO upgrade (upgrade, applied) VALUES ('invenio_2012_12_06_new_citation_dict_table',NOW());
INSERT INTO upgrade (upgrade, applied) VALUES ('invenio_2013_10_25_new_param_websubmit_function',NOW());
INSERT INTO upgrade (upgrade, applied) VALUES ('invenio_2013_09_10_new_param_websubmit_function',NOW());
INSERT INTO upgrade (upgrade, applied) VALUES ('invenio_2013_11_12_new_param_websubmit_function',NOW());

-- master upgrade recipes:
INSERT INTO upgrade (upgrade, applied) VALUES ('invenio_2012_10_29_idxINDEX_new_indexer_column',NOW());
INSERT INTO upgrade (upgrade, applied) VALUES ('invenio_2012_11_04_circulation_and_linkback_updates',NOW());
INSERT INTO upgrade (upgrade, applied) VALUES ('invenio_2012_11_07_xtrjob_last_recid',NOW());
INSERT INTO upgrade (upgrade, applied) VALUES ('invenio_2012_11_27_new_selfcite_tables',NOW());
INSERT INTO upgrade (upgrade, applied) VALUES ('invenio_2012_12_11_new_citation_errors_table',NOW());
INSERT INTO upgrade (upgrade, applied) VALUES ('invenio_2013_01_08_new_goto_table',NOW());
INSERT INTO upgrade (upgrade, applied) VALUES ('invenio_2012_11_15_bibdocfile_model',NOW());
INSERT INTO upgrade (upgrade, applied) VALUES ('invenio_2013_02_01_oaiREPOSITORY_last_updated',NOW());
INSERT INTO upgrade (upgrade, applied) VALUES ('invenio_2013_03_07_crcILLREQUEST_overdue_letter',NOW());
INSERT INTO upgrade (upgrade, applied) VALUES ('invenio_2013_01_12_bibrec_master_format',NOW());
INSERT INTO upgrade (upgrade, applied) VALUES ('invenio_2013_06_11_rnkDOWNLOADS_file_format',NOW());
INSERT INTO upgrade (upgrade, applied) VALUES ('invenio_2013_03_20_idxINDEX_synonym_kb',NOW());
INSERT INTO upgrade (upgrade, applied) VALUES ('invenio_2013_03_21_idxINDEX_stopwords',NOW());
INSERT INTO upgrade (upgrade, applied) VALUES ('invenio_2013_03_25_idxINDEX_html_markup',NOW());
INSERT INTO upgrade (upgrade, applied) VALUES ('invenio_2013_03_28_idxINDEX_tokenizer',NOW());
INSERT INTO upgrade (upgrade, applied) VALUES ('invenio_2013_03_29_idxINDEX_stopwords_update',NOW());
INSERT INTO upgrade (upgrade, applied) VALUES ('invenio_2013_08_20_bibauthority_updates',NOW());
INSERT INTO upgrade (upgrade, applied) VALUES ('invenio_2013_08_22_new_index_itemcount',NOW());
INSERT INTO upgrade (upgrade, applied) VALUES ('invenio_2013_10_18_crcLIBRARY_type',NOW());
INSERT INTO upgrade (upgrade, applied) VALUES ('invenio_2013_10_18_new_index_filetype',NOW());
INSERT INTO upgrade (upgrade, applied) VALUES ('invenio_2013_10_25_delete_recjson_cache',NOW());
INSERT INTO upgrade (upgrade, applied) VALUES ('invenio_2013_08_22_hstRECORD_affected_fields',NOW());
INSERT INTO upgrade (upgrade, applied) VALUES ('invenio_2013_09_25_virtual_indexes',NOW());
INSERT INTO upgrade (upgrade, applied) VALUES ('invenio_2013_09_30_indexer_interface',NOW());
INSERT INTO upgrade (upgrade, applied) VALUES ('invenio_2013_04_30_new_plotextractor_websubmit_function',NOW());
INSERT INTO upgrade (upgrade, applied) VALUES ('invenio_2013_02_06_new_collectionboxname_table',NOW());
INSERT INTO upgrade (upgrade, applied) VALUES ('invenio_2013_03_20_new_self_citation_dict_table',NOW());
INSERT INTO upgrade (upgrade, applied) VALUES ('invenio_2013_03_26_new_citation_log_table',NOW());
INSERT INTO upgrade (upgrade, applied) VALUES ('invenio_2013_03_28_bibindex_bibrank_type_index',NOW());
INSERT INTO upgrade (upgrade, applied) VALUES ('invenio_2013_04_11_bibformat_2nd_pass',NOW());
INSERT INTO upgrade (upgrade, applied) VALUES ('invenio_2013_06_24_new_bibsched_status_table',NOW());
INSERT INTO upgrade (upgrade, applied) VALUES ('invenio_2013_09_02_new_bibARXIVPDF',NOW());
INSERT INTO upgrade (upgrade, applied) VALUES ('invenio_2012_12_05_oaiHARVEST_arguments_blob',NOW());
INSERT INTO upgrade (upgrade, applied) VALUES ('invenio_2013_09_13_new_bibEDITCACHE',NOW());
INSERT INTO upgrade (upgrade, applied) VALUES ('invenio_2013_09_26_webauthorlist',NOW());
INSERT INTO upgrade (upgrade, applied) VALUES ('invenio_2013_10_11_bibHOLDINGPEN_longblob',NOW());
INSERT INTO upgrade (upgrade, applied) VALUES ('invenio_2013_06_20_new_bibcheck_rules_table',NOW());
INSERT INTO upgrade (upgrade, applied) VALUES ('invenio_2012_10_31_WebAuthorProfile_bibformat_dependency_update',NOW());
INSERT INTO upgrade (upgrade, applied) VALUES ('invenio_2013_03_18_aidPERSONIDDATA_last_updated',NOW());
INSERT INTO upgrade (upgrade, applied) VALUES ('invenio_2013_03_18_bibauthorid_search_engine_tables',NOW());
INSERT INTO upgrade (upgrade, applied) VALUES ('invenio_2013_03_18_wapCACHE_object_value_longblob',NOW());
INSERT INTO upgrade (upgrade, applied) VALUES ('invenio_2013_09_16_aidPERSONIDDATA_datablob',NOW());
INSERT INTO upgrade (upgrade, applied) VALUES ('invenio_2013_12_04_seqSTORE_larger_value',NOW());
INSERT INTO upgrade (upgrade, applied) VALUES ('invenio_2014_01_22_redis_sessions',NOW());
INSERT INTO upgrade (upgrade, applied) VALUES ('invenio_2014_01_24_seqSTORE_larger_value',NOW());
INSERT INTO upgrade (upgrade, applied) VALUES ('invenio_2014_01_22_queue_table_virtual_index',NOW());
INSERT INTO upgrade (upgrade, applied) VALUES ('invenio_2013_12_05_new_index_doi',NOW());
INSERT INTO upgrade (upgrade, applied) VALUES ('invenio_2014_03_13_new_index_filename',NOW());
INSERT INTO upgrade (upgrade, applied) VALUES ('invenio_2014_04_01_new_aidAFFILIATIONS',NOW());

-- end of file
