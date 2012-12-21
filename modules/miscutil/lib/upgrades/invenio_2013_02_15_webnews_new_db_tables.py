# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2012 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

from invenio.dbquery import run_sql

depends_on = ['invenio_release_1_1_0']

def info():
    return "New database tables for the WebNews module"

def do_upgrade():
    query_story = \
"""DROP TABLE IF EXISTS `nwsSTORY`;
CREATE TABLE `nwsSTORY` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `title` varchar(256) NOT NULL,
  `body` text NOT NULL,
  `created` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
);"""
    run_sql(query_story)

    query_tag = \
"""DROP TABLE IF EXISTS `nwsTAG`;
CREATE TABLE `nwsTAG` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `tag` varchar(64) NOT NULL,
  PRIMARY KEY (`id`)
);"""
    run_sql(query_tag)

    query_tooltip = \
"""DROP TABLE IF EXISTS `nwsTOOLTIP`;
CREATE TABLE `nwsTOOLTIP` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `id_story` int(11) NOT NULL,
  `body` varchar(512) NOT NULL,
  `target_element` varchar(256) NOT NULL DEFAULT '',
  `target_page` varchar(256) NOT NULL DEFAULT '',
  PRIMARY KEY (`id`),
  KEY `id_story` (`id_story`),
  CONSTRAINT `nwsTOOLTIP_ibfk_1` FOREIGN KEY (`id_story`) REFERENCES `nwsSTORY` (`id`)
);"""
    run_sql(query_tooltip)

    query_story_tag = \
"""DROP TABLE IF EXISTS `nwsSTORY_nwsTAG`;
CREATE TABLE `nwsSTORY_nwsTAG` (
  `id_story` int(11) NOT NULL,
  `id_tag` int(11) NOT NULL,
  PRIMARY KEY (`id_story`,`id_tag`),
  KEY `id_story` (`id_story`),
  KEY `id_tag` (`id_tag`),
  CONSTRAINT `nwsSTORY_nwsTAG_ibfk_1` FOREIGN KEY (`id_story`) REFERENCES `nwsSTORY` (`id`),
  CONSTRAINT `nwsSTORY_nwsTAG_ibfk_2` FOREIGN KEY (`id_tag`) REFERENCES `nwsTAG` (`id`)
);"""
    run_sql(query_story_tag)

def estimate():
    return 1

def pre_upgrade():
    pass

def post_upgrade():
    pass
