-- $Id$
-- Create tables for the CDS Software.

-- This file is part of the CERN Document Server Software (CDSware).
-- Copyright (C) 2002, 2003, 2004, 2005 CERN.
--
-- The CDSware is free software; you can redistribute it and/or
-- modify it under the terms of the GNU General Public License as
-- published by the Free Software Foundation; either version 2 of the
-- License, or (at your option) any later version.
--
-- The CDSware is distributed in the hope that it will be useful, but
-- WITHOUT ANY WARRANTY; without even the implied warranty of
-- MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
-- General Public License for more details.  
--
-- You should have received a copy of the GNU General Public License
-- along with CDSware; if not, write to the Free Software Foundation, Inc.,
-- 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

-- tables for bibliographic records:

CREATE TABLE IF NOT EXISTS bibrec (
  id mediumint(8) unsigned NOT NULL auto_increment,
  creation_date datetime NOT NULL default '0000-00-00',
  modification_date datetime NOT NULL default '0000-00-00',
  PRIMARY KEY  (id)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib00x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib01x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib02x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib03x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib04x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib05x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib06x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib07x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib08x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib09x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib10x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib11x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib12x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib13x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib14x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib15x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib16x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib17x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib18x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib19x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib20x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib21x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib22x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib23x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib24x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib25x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib26x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib27x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib28x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib29x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib30x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib31x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib32x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib33x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib34x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib35x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib36x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib37x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib38x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib39x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib40x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib41x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib42x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib43x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib44x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib45x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib46x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib47x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib48x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib49x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib50x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib51x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib52x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib53x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib54x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib55x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib56x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib57x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib58x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib59x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib60x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib61x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib62x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib63x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib64x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib65x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib66x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib67x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib68x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib69x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib70x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib71x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib72x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib73x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib74x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib75x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib76x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib77x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib78x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib79x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib80x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib81x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib82x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib83x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib84x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib85x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib86x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib87x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib88x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib89x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib90x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib91x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib92x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib93x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib94x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib95x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib96x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib97x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib98x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bib99x (
  id mediumint(8) unsigned NOT NULL auto_increment,
  tag varchar(6) NOT NULL default '',
  value text NOT NULL,
  PRIMARY KEY  (id),
  KEY kt (tag),
  KEY kv (value(35))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib00x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib01x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib02x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib03x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib04x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib05x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib06x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib07x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib08x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib09x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib10x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib11x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib12x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib13x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib14x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib15x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib16x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib17x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib18x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib19x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib20x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib21x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib22x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib23x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib24x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib25x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib26x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib27x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib28x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib29x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib30x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib31x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib32x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib33x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib34x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib35x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib36x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib37x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib38x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib39x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib40x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib41x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib42x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib43x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib44x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib45x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib46x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib47x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib48x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib49x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib50x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib51x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib52x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib53x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib54x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib55x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib56x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib57x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib58x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib59x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib60x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib61x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib62x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib63x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib64x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib65x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib66x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib67x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib68x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib69x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib70x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib71x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib72x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib73x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib74x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib75x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib76x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib77x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib78x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib79x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib80x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib81x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib82x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib83x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib84x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib85x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib86x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib87x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib88x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib89x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib90x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib91x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib92x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib93x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib94x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib95x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib96x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib97x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib98x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bib99x (
  id_bibrec mediumint(8) unsigned NOT NULL default '0',
  id_bibxxx mediumint(8) unsigned NOT NULL default '0',
  field_number smallint(5) unsigned default NULL,
  KEY id_bibxxx (id_bibxxx),
  KEY id_bibrec (id_bibrec)
) TYPE=MyISAM;

-- tables for bibliographic records formatted:

CREATE TABLE IF NOT EXISTS bibfmt (
  id mediumint(8) unsigned NOT NULL auto_increment,
  id_bibrec int(8) unsigned NOT NULL default '0',
  format varchar(10) NOT NULL default '',
  last_updated datetime NOT NULL default '0000-00-00',
  value longblob,
  PRIMARY KEY  (id),
  KEY id_bibrec (id_bibrec),
  KEY format (format)
) TYPE=MyISAM;

-- tables for index files:

CREATE TABLE IF NOT EXISTS idxINDEX (
  id mediumint(9) unsigned NOT NULL,
  name varchar(50) NOT NULL default '',
  description varchar(255) NOT NULL default '',
  last_updated datetime NOT NULL default '0000-00-00 00:00:00',
  PRIMARY KEY  (id),
  UNIQUE KEY name (name)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS idxINDEXNAME (
  id_idxINDEX mediumint(9) unsigned NOT NULL,
  ln char(2) NOT NULL default '',
  type char(3) NOT NULL default 'sn',
  value varchar(255) NOT NULL,
  PRIMARY KEY  (id_idxINDEX,ln,type)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS idxINDEX_field (
  id_idxINDEX mediumint(9) unsigned NOT NULL,
  id_field mediumint(9) unsigned NOT NULL,
  regexp_punctuation varchar(255) NOT NULL default "[\.\,\:\;\?\!\"]",
  regexp_alphanumeric_separators varchar(255) NOT NULL default "[\!\"\#\$\%\&\'\(\)\*\+\,\-\.\/\:\;\<\=\>\?\@\[\\\]\^\_\`\{\|\}\~]",
  PRIMARY KEY  (id_idxINDEX,id_field)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS idxWORD01F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term varchar(50) default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  UNIQUE KEY term (term)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS idxWORD01R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  PRIMARY KEY (id_bibrec,type)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS idxWORD02F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term varchar(50) default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  UNIQUE KEY term (term)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS idxWORD02R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  PRIMARY KEY (id_bibrec,type)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS idxWORD03F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term varchar(50) default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  UNIQUE KEY term (term)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS idxWORD03R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  PRIMARY KEY (id_bibrec,type)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS idxWORD04F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term varchar(50) default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  UNIQUE KEY term (term)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS idxWORD04R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  PRIMARY KEY (id_bibrec,type)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS idxWORD05F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term varchar(50) default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  UNIQUE KEY term (term)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS idxWORD05R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  PRIMARY KEY (id_bibrec,type)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS idxWORD06F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term varchar(50) default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  UNIQUE KEY term (term)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS idxWORD06R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  PRIMARY KEY (id_bibrec,type)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS idxWORD07F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term varchar(50) default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  UNIQUE KEY term (term)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS idxWORD07R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  PRIMARY KEY (id_bibrec,type)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS idxWORD08F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term varchar(50) default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  UNIQUE KEY term (term)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS idxWORD08R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  PRIMARY KEY (id_bibrec,type)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS idxWORD09F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term varchar(50) default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  UNIQUE KEY term (term)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS idxWORD09R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  PRIMARY KEY (id_bibrec,type)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS idxWORD10F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term varchar(50) default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  UNIQUE KEY term (term)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS idxWORD10R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  PRIMARY KEY (id_bibrec,type)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPHRASE01F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term varchar(50) default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  UNIQUE KEY term (term)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPHRASE01R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  PRIMARY KEY (id_bibrec,type)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPHRASE02F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term varchar(50) default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  UNIQUE KEY term (term)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPHRASE02R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  PRIMARY KEY (id_bibrec,type)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPHRASE03F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term varchar(50) default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  UNIQUE KEY term (term)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPHRASE03R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  PRIMARY KEY (id_bibrec,type)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPHRASE04F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term varchar(50) default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  UNIQUE KEY term (term)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPHRASE04R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  PRIMARY KEY (id_bibrec,type)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPHRASE05F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term varchar(50) default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  UNIQUE KEY term (term)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPHRASE05R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  PRIMARY KEY (id_bibrec,type)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPHRASE06F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term varchar(50) default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  UNIQUE KEY term (term)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPHRASE06R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  PRIMARY KEY (id_bibrec,type)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPHRASE07F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term varchar(50) default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  UNIQUE KEY term (term)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPHRASE07R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  PRIMARY KEY (id_bibrec,type)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPHRASE08F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term varchar(50) default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  UNIQUE KEY term (term)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPHRASE08R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  PRIMARY KEY (id_bibrec,type)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPHRASE09F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term varchar(50) default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  UNIQUE KEY term (term)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPHRASE09R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  PRIMARY KEY (id_bibrec,type)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPHRASE10F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term varchar(50) default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  UNIQUE KEY term (term)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS idxPHRASE10R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  PRIMARY KEY (id_bibrec,type)
) TYPE=MyISAM;

-- tables for ranking:

CREATE TABLE IF NOT EXISTS rnkMETHOD (
  id mediumint(9) unsigned NOT NULL auto_increment,
  name varchar(20) NOT NULL default '',
  last_updated datetime NOT NULL default '0000-00-00 00:00:00',
  PRIMARY KEY (id),
  UNIQUE KEY name (name)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS rnkMETHODNAME (
  id_rnkMETHOD mediumint(9) unsigned NOT NULL,
  ln char(2) NOT NULL default '',
  type char(3) NOT NULL default 'sn',
  value varchar(255) NOT NULL,
  PRIMARY KEY  (id_rnkMETHOD,ln,type)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS rnkMETHODDATA (
  id_rnkMETHOD mediumint(9) unsigned NOT NULL,
  relevance_data longblob,
  PRIMARY KEY  (id_rnkMETHOD)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS collection_rnkMETHOD (
  id_collection mediumint(9) unsigned NOT NULL,
  id_rnkMETHOD mediumint(9) unsigned NOT NULL,
  score tinyint(4) unsigned NOT NULL default '0',
  PRIMARY KEY  (id_collection,id_rnkMETHOD)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS rnkWORD01F (
  id mediumint(9) unsigned NOT NULL auto_increment,
  term varchar(50) default NULL,
  hitlist longblob,
  PRIMARY KEY  (id),
  UNIQUE KEY term (term)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS rnkWORD01R (
  id_bibrec mediumint(9) unsigned NOT NULL,
  termlist longblob,
  type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
  PRIMARY KEY  (id_bibrec,type)
) TYPE=MyISAM;

-- tables for collections and collection tree:

CREATE TABLE IF NOT EXISTS collection (
  id mediumint(9) unsigned NOT NULL auto_increment,
  name varchar(255) NOT NULL,
  dbquery text,
  nbrecs int(10) unsigned default '0',
  reclist longblob,
  restricted varchar(255) default NULL,
  PRIMARY KEY  (id),
  UNIQUE KEY name (name),
  KEY dbquery (dbquery(50))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS collectionname (
  id_collection mediumint(9) unsigned NOT NULL,
  ln char(2) NOT NULL default '',
  type char(3) NOT NULL default 'sn',
  value varchar(255) NOT NULL,
  PRIMARY KEY  (id_collection,ln,type)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS collection_collection (
  id_dad mediumint(9) unsigned NOT NULL,
  id_son mediumint(9) unsigned NOT NULL,
  type char(1) NOT NULL default 'r',
  score tinyint(4) unsigned NOT NULL default '0',
  PRIMARY KEY (id_dad,id_son)
) TYPE=MyISAM;

-- tables for OAI sets:

CREATE TABLE IF NOT EXISTS oaiSET (
  id mediumint(9) unsigned NOT NULL auto_increment,
  setName varchar(255) NOT NULL default '',
  setSpec varchar(255) NOT NULL default '',
  setDescription text,
  setDefinition text NOT NULL default '',
  setRecList longblob,
  PRIMARY KEY  (id),
  UNIQUE KEY setSpec (setSpec)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS oaiHARVEST (
  id mediumint(9) unsigned NOT NULL auto_increment,
  baseURL varchar(255) NOT NULL default '',
  metadataPrefix varchar(255) NOT NULL default 'oai_dc',
  runtime datetime NOT NULL,
  sleeptime varchar(20),
  arguments text,
  comment text,
  PRIMARY KEY  (id)
) TYPE=MyISAM;

-- tables for portal elements:

CREATE TABLE IF NOT EXISTS collection_portalbox (
  id_collection mediumint(9) unsigned NOT NULL,
  id_portalbox mediumint(9) unsigned NOT NULL,
  ln char(2) NOT NULL default '',
  position char(3) NOT NULL default 'top',
  score tinyint(4) unsigned NOT NULL default '0',
  PRIMARY KEY  (id_collection,id_portalbox,ln)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS portalbox (
  id mediumint(9) unsigned NOT NULL auto_increment,
  title text NOT NULL,
  body text NOT NULL,
  UNIQUE KEY id (id)
) TYPE=MyISAM;

-- tables for search examples:

CREATE TABLE IF NOT EXISTS collection_example (
  id_collection mediumint(9) unsigned NOT NULL,
  id_example mediumint(9) unsigned NOT NULL,
  score tinyint(4) unsigned NOT NULL default '0',
  PRIMARY KEY  (id_collection,id_example)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS example (
  id mediumint(9) unsigned NOT NULL auto_increment,
  type text NOT NULL default '',
  body text NOT NULL,
  PRIMARY KEY  (id)
) TYPE=MyISAM;

-- tables for collection formats:

CREATE TABLE IF NOT EXISTS collection_format (
  id_collection mediumint(9) unsigned NOT NULL,
  id_format mediumint(9) unsigned NOT NULL,
  score tinyint(4) unsigned NOT NULL default '0',
  PRIMARY KEY  (id_collection,id_format)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS format (
  id mediumint(9) unsigned NOT NULL auto_increment,
  name varchar(255) NOT NULL,
  code varchar(6) NOT NULL,
  PRIMARY KEY  (id),
  UNIQUE KEY code (code)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS formatname (
  id_format mediumint(9) unsigned NOT NULL,
  ln char(2) NOT NULL default '',
  type char(3) NOT NULL default 'sn',
  value varchar(255) NOT NULL,
  PRIMARY KEY  (id_format,ln,type)
) TYPE=MyISAM;

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
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS field (
  id mediumint(9) unsigned NOT NULL auto_increment,
  name varchar(255) NOT NULL,
  code varchar(255) NOT NULL,
  PRIMARY KEY  (id),
  UNIQUE KEY code (code)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS fieldname (
  id_field mediumint(9) unsigned NOT NULL,
  ln char(2) NOT NULL default '',
  type char(3) NOT NULL default 'sn',
  value varchar(255) NOT NULL,
  PRIMARY KEY  (id_field,ln,type)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS fieldvalue (
  id mediumint(9) unsigned NOT NULL auto_increment,
  name varchar(255) NOT NULL,
  value text NOT NULL,
  PRIMARY KEY  (id)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS field_tag (
  id_field mediumint(9) unsigned NOT NULL,
  id_tag mediumint(9) unsigned NOT NULL,
  score tinyint(4) unsigned NOT NULL default '0',
  PRIMARY KEY  (id_field,id_tag)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS tag (
  id mediumint(9) unsigned NOT NULL auto_increment,
  name varchar(255) NOT NULL,
  value char(6) NOT NULL,
  PRIMARY KEY  (id)
) TYPE=MyISAM;

-- tables for file management

CREATE TABLE IF NOT EXISTS bibdoc (
  id mediumint(9) unsigned NOT NULL auto_increment,
  status varchar(50) NOT NULL default '',
  docname varchar(250) NOT NULL default 'file',
  creation_date datetime NOT NULL default '0000-00-00',
  modification_date datetime NOT NULL default '0000-00-00',
  PRIMARY KEY  (id)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibrec_bibdoc (
  id_bibrec mediumint(9) unsigned NOT NULL default '0',
  id_bibdoc mediumint(9) unsigned NOT NULL default '0',
  type varchar(255),
  KEY  (id_bibrec),
  KEY  (id_bibdoc)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS bibdoc_bibdoc (
  id_bibdoc1 mediumint(9) unsigned NOT NULL,
  id_bibdoc2 mediumint(9) unsigned NOT NULL,
  type varchar(255),
  KEY  (id_bibdoc1),
  KEY  (id_bibdoc2)
) TYPE=MyISAM;

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
) TYPE=MyISAM;

-- table for sessions and users:

CREATE TABLE IF NOT EXISTS session (
  session_key varchar(32) NOT NULL default '',
  session_expiry int(11) unsigned NOT NULL default '0',
  session_object blob,
  uid int(15) unsigned NOT NULL,
  UNIQUE KEY session_key (session_key)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS user (
  id int(15) unsigned NOT NULL auto_increment,
  email varchar(255) NOT NULL default '',
  password varchar(20) default NULL,
  note varchar(255) default NULL,
  settings varchar(255) default NULL,
  UNIQUE KEY id (id),
  KEY email (email)
) TYPE=MyISAM;

-- tables for access control engine

CREATE TABLE IF NOT EXISTS accROLE (
  id int(15) unsigned NOT NULL auto_increment, 
  name varchar(32), 
  description varchar(255), 
  PRIMARY KEY (id),
  UNIQUE KEY name (name)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS user_accROLE (
  id_user int(15) unsigned NOT NULL,
  id_accROLE int(15) unsigned NOT NULL,
  PRIMARY KEY (id_user, id_accROLE)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS accACTION (
  id int(15) unsigned NOT NULL auto_increment,
  name varchar(32),
  description varchar(255),
  allowedkeywords varchar(255),
  optional ENUM ('yes', 'no') NOT NULL default 'no',
  PRIMARY KEY (id), 
  UNIQUE KEY name (name)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS accARGUMENT (
  id int(15) unsigned NOT NULL auto_increment,
  keyword varchar (32),
  value varchar(64),
  PRIMARY KEY (id),
  KEY KEYVAL (keyword, value)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS accROLE_accACTION_accARGUMENT (
  id_accROLE int(15),
  id_accACTION int(15),
  id_accARGUMENT int(15),
  argumentlistid mediumint(8),
  KEY id_accROLE     (id_accROLE),
  KEY id_accACTION   (id_accACTION),
  KEY id_accARGUMENT (id_accARGUMENT)
) TYPE=MyISAM;

-- tables for personal features (baskets, alerts, searches):

CREATE TABLE IF NOT EXISTS user_query (
  id_user int(15) unsigned NOT NULL default '0',
  id_query int(15) unsigned NOT NULL default '0',
  hostname varchar(50) default 'unknown host',
  date datetime default NULL,
  KEY id_user (id_user,id_query)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS query (
  id int(15) unsigned NOT NULL auto_increment,
  type char(1) NOT NULL default 'r',
  urlargs text NOT NULL,
  PRIMARY KEY  (id),
  KEY urlargs (urlargs(100))
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS user_basket (
  id_user int(15) unsigned NOT NULL default '0',
  id_basket int(15) unsigned NOT NULL default '0',
  date_modification date NOT NULL default '0000-00-00',
  PRIMARY KEY  (id_user,id_basket)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS basket (
  id int(15) unsigned NOT NULL auto_increment,
  name varchar(50) NOT NULL default '',
  public char(1) default 'n',
  PRIMARY KEY  (id),
  KEY name (name)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS basket_record (
  id_basket int(15) unsigned NOT NULL default '0',
  id_record int(15) unsigned NOT NULL default '0',
  nb_order int(15) unsigned NOT NULL auto_increment,
  PRIMARY KEY  (id_basket,id_record),
  KEY nb_order (nb_order)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS record (
  id int(15) unsigned NOT NULL auto_increment,
  id_bibrec varchar(15) NOT NULL default '',
  aleph text,
  html text,
  PRIMARY KEY  (id_bibrec),
  UNIQUE KEY id (id)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS user_query_basket (
  id_user int(15) unsigned NOT NULL default '0',
  id_query int(15) unsigned NOT NULL default '0',
  id_basket int(15) unsigned NOT NULL default '0',
  frequency varchar(5) NOT NULL default '',
  date_creation date default NULL,
  date_lastrun date default '0000-00-00',
  alert_name varchar(30) NOT NULL,
  notification char(1) NOT NULL default 'y',
  PRIMARY KEY  (id_user,id_query,frequency,id_basket),
  KEY alert_name (alert_name)
) TYPE=MyISAM;

-- tables for FlexElink:

CREATE TABLE IF NOT EXISTS flxFORMATS (
  name varchar(255) NOT NULL default '',
  value text,
  doc text,
  serialized longtext,
  PRIMARY KEY  (name)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS flxKBS (
  kb_name varchar(255) NOT NULL default '',
  kb_table varchar(255) NOT NULL default '',
  doc text,
  PRIMARY KEY  (kb_name)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS flxKBDBCOLLID2COLL (
  vkey varchar(255) NOT NULL default '',
  value text,
  PRIMARY KEY  (vkey)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS flxKBEJOURNALS (
  vkey varchar(255) NOT NULL default '',
  value text,
  PRIMARY KEY  (vkey)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS flxLINKTYPES (
  linktype varchar(255) NOT NULL default '',
  check_exists enum('Y','N') NOT NULL default 'N',
  solvingtype enum('INT','EXT') NOT NULL default 'EXT',
  base_file varchar(255) NOT NULL default '',
  base_url varchar(255) NOT NULL default '',
  PRIMARY KEY  (linktype)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS flxLINKTYPECONDITIONS (
  linktype varchar(255) NOT NULL default '',
  eval_order int(11) NOT NULL default '0',
  el_condition text NOT NULL,
  el_action text NOT NULL,
  solvingtype enum('INT','EXT') NOT NULL default 'EXT',
  base_file varchar(255) NOT NULL default '',
  base_url varchar(255) NOT NULL default '',
  PRIMARY KEY  (linktype,eval_order)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS flxLINKTYPECONDITIONSACTIONS (
  linktype varchar(255) NOT NULL default '',
  eval_order int(11) NOT NULL default '0',
  apply_order int(11) NOT NULL default '0',
  el_code text,
  PRIMARY KEY  (linktype,eval_order,apply_order)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS flxLINKTYPECONDITIONSFILEFORMATS (
  linktype varchar(255) NOT NULL default '',
  eval_order int(11) NOT NULL default '0',
  fname varchar(30) NOT NULL default '',
  PRIMARY KEY  (linktype,eval_order,fname)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS flxFILEFORMATS (
  name varchar(30) NOT NULL default '',
  text varchar(255) default '',
  extensions text,
  PRIMARY KEY  (name)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS flxLINKTYPEPARAMS (
  linktype varchar(255) NOT NULL default '',
  pname varchar(78) NOT NULL default '',
  ord tinyint(4) NOT NULL default '0',
  PRIMARY KEY  (linktype,pname),
  UNIQUE KEY IDX_LINKTYPE_PARAMS_ORD (linktype,ord)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS flxXMLMARCEXTRULES (
  type varchar(8) NOT NULL default '',
  varname varchar(50) NOT NULL default '',
  att_id varchar(150) default NULL,
  att_i1 varchar(150) default NULL,
  att_i2 varchar(150) default NULL,
  mvalues enum('S','N') NOT NULL default 'S',
  ftype enum("DATAFIELD", "CONTROLFIELD") not null,
  PRIMARY KEY  (type,varname)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS flxXMLMARCEXTRULESUBFIELDS (
  type varchar(8) NOT NULL default '',
  varname varchar(50) NOT NULL default '',
  sfname varchar(50) NOT NULL default '',
  att_label varchar(150) default NULL,
  PRIMARY KEY  (type,varname,sfname)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS flxBEHAVIORCONDITIONSACTIONS (
  otype varchar(40) NOT NULL default '',
  eval_order int(11) NOT NULL default '0',
  apply_order int(11) NOT NULL default '0',
  locator text,
  el_code text,
  PRIMARY KEY  (otype,eval_order,apply_order)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS flxBEHAVIORCONDITIONS (
  otype varchar(40) NOT NULL default '',
  eval_order int(11) NOT NULL default '0',
  el_condition text NOT NULL,
  PRIMARY KEY  (otype,eval_order)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS flxBEHAVIORS (
  name varchar(40) NOT NULL default '',
  type enum('NORMAL','IENRICH') NOT NULL default 'NORMAL',
  doc text,
  PRIMARY KEY  (name)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS flxUDFS (
  fname varchar(100) NOT NULL default '',
  code text NOT NULL,
  rtype enum('STRING','BOOL') NOT NULL default 'STRING',
  doc text,
  PRIMARY KEY  (fname)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS flxUDFPARAMS (
  fname varchar(100) NOT NULL default '',
  pname varchar(100) NOT NULL default '',
  ord tinyint(4) NOT NULL default '0',
  PRIMARY KEY  (fname,pname),
  UNIQUE KEY IDX_UDFS_PARAMS_ORD (fname,ord)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS flxUSERS (
  id int(11) NOT NULL default '0',
  PRIMARY KEY  (id)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS flxREFORMAT (
  id int(10) unsigned NOT NULL auto_increment,
  user varchar(50) NOT NULL,
  date DATETIME NOT NULL,
  reg_select text,
  otypes varchar(40) not null,
  state varchar(20),
  PRIMARY KEY  (id)
) TYPE=MyISAM;

-- tables for webSubmit:

CREATE TABLE IF NOT EXISTS sbmACTION (
  lactname text,
  sactname char(3) NOT NULL default '',
  dir text,
  cd date default NULL,
  md date default NULL,
  actionbutton text,
  statustext text,
  PRIMARY KEY  (sactname)
) TYPE=MyISAM PACK_KEYS=1;

CREATE TABLE IF NOT EXISTS sbmALLFUNCDESCR (
  function varchar(40) NOT NULL default '',
  description tinytext,
  PRIMARY KEY  (function)
) TYPE=MyISAM PACK_KEYS=1;

CREATE TABLE IF NOT EXISTS sbmAPPROVAL (
  doctype varchar(10) NOT NULL default '',
  categ varchar(50) NOT NULL default '',
  rn varchar(50) NOT NULL default '',
  status varchar(10) NOT NULL default '',
  dFirstReq datetime NOT NULL default '0000-00-00 00:00:00',
  dLastReq datetime NOT NULL default '0000-00-00 00:00:00',
  dAction datetime NOT NULL default '0000-00-00 00:00:00',
  access varchar(20) NOT NULL default '0',
  PRIMARY KEY  (rn)
) TYPE=MyISAM PACK_KEYS=1;

CREATE TABLE IF NOT EXISTS sbmCOLLECTION (
  id int(11) NOT NULL auto_increment,
  name varchar(100) NOT NULL default '',
  PRIMARY KEY  (id)
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS sbmCOLLECTION_sbmCOLLECTION (
  id_father int(11) NOT NULL default '0',
  id_son int(11) NOT NULL default '0',
  catalogue_order int(11) NOT NULL default '0'
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS sbmCOLLECTION_sbmDOCTYPE (
  id_father int(11) NOT NULL default '0',
  id_son char(10) NOT NULL default '0',
  catalogue_order int(11) NOT NULL default '0'
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS sbmCATEGORIES (
  doctype varchar(10) NOT NULL default '',
  sname varchar(75) NOT NULL default '',
  lname varchar(75) NOT NULL default '',
  KEY sname (sname)
) TYPE=MyISAM PACK_KEYS=1;

CREATE TABLE IF NOT EXISTS sbmCHECKS (
  chname varchar(15) NOT NULL default '',
  chdesc text,
  cd date default NULL,
  md date default NULL,
  chefi1 text,
  chefi2 text,
  PRIMARY KEY  (chname)
) TYPE=MyISAM PACK_KEYS=1;

CREATE TABLE IF NOT EXISTS sbmDOCTYPE (
  ldocname text,
  sdocname varchar(10) default NULL,
  cd date default NULL,
  md date default NULL,
  description text
) TYPE=MyISAM PACK_KEYS=1;

CREATE TABLE IF NOT EXISTS sbmFIELD (
  subname varchar(10) default NULL,
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
) TYPE=MyISAM PACK_KEYS=1;

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
) TYPE=MyISAM PACK_KEYS=1;

CREATE TABLE IF NOT EXISTS sbmFORMATEXTENSION (
  FILE_FORMAT text NOT NULL,
  FILE_EXTENSION text NOT NULL
) TYPE=MyISAM PACK_KEYS=1;

CREATE TABLE IF NOT EXISTS sbmFUNCTIONS (
  action varchar(10) NOT NULL default '',
  doctype varchar(10) NOT NULL default '',
  function varchar(40) NOT NULL default '',
  score int(11) NOT NULL default '0',
  step tinyint(4) NOT NULL default '1'
) TYPE=MyISAM PACK_KEYS=1;

CREATE TABLE IF NOT EXISTS sbmFUNDESC (
  function varchar(40) NOT NULL default '',
  param varchar(40) default NULL
) TYPE=MyISAM PACK_KEYS=1;

CREATE TABLE IF NOT EXISTS sbmGFILERESULT (
  FORMAT text NOT NULL,
  RESULT text NOT NULL
) TYPE=MyISAM PACK_KEYS=1;

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
) TYPE=MyISAM PACK_KEYS=1;

CREATE TABLE IF NOT EXISTS sbmPARAMETERS (
  doctype varchar(10) NOT NULL default '',
  name varchar(20) NOT NULL default '',
  value varchar(200) NOT NULL default '',
  PRIMARY KEY  (doctype,name)
) TYPE=MyISAM;

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
) TYPE=MyISAM PACK_KEYS=1;

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
) TYPE=MyISAM PACK_KEYS=1;

CREATE TABLE IF NOT EXISTS sbmPUBLICATIONDATA (
  doctype varchar(10) NOT NULL default '',
  editoboard varchar(250) NOT NULL default '',
  base varchar(10) NOT NULL default '',
  logicalbase varchar(10) NOT NULL default '',
  spokesperson varchar(50) NOT NULL default '',
  PRIMARY KEY  (doctype)
) TYPE=MyISAM PACK_KEYS=1;

CREATE TABLE IF NOT EXISTS sbmREFEREES (
  doctype varchar(10) NOT NULL default '',
  categ varchar(10) NOT NULL default '',
  name varchar(50) NOT NULL default '',
  address varchar(50) NOT NULL default '',
  rid int(11) NOT NULL auto_increment,
  PRIMARY KEY  (rid)
) TYPE=MyISAM PACK_KEYS=1;

CREATE TABLE IF NOT EXISTS sbmSUBMISSIONS (
  email varchar(50) NOT NULL default '',
  doctype varchar(10) NOT NULL default '',
  action varchar(10) NOT NULL default '',
  status varchar(10) NOT NULL default '',
  id varchar(30) NOT NULL default '',
  reference varchar(40) NOT NULL default '',
  cd datetime NOT NULL default '0000-00-00 00:00:00',
  md datetime NOT NULL default '0000-00-00 00:00:00'
) TYPE=MyISAM;

CREATE TABLE IF NOT EXISTS sbmCOOKIES (
  id int(15) unsigned NOT NULL auto_increment,
  name varchar(100) NOT NULL,
  value text,
  uid int(15) NOT NULL,
  PRIMARY KEY  (id)
) TYPE=MyISAM;

-- Scheduler tables

CREATE TABLE IF NOT EXISTS schTASK (
  id int(15) unsigned NOT NULL auto_increment,
  proc varchar(20) NOT NULL,
  host varchar(255) NOT NULL,
  user varchar(50) NOT NULL,
  runtime datetime NOT NULL,
  sleeptime varchar(20),
  arguments longtext,
  status varchar(50),
  progress varchar(255),
  PRIMARY KEY  (id)
) TYPE=MyISAM;


-- end of file
