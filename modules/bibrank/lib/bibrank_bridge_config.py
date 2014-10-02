## This file is part of Invenio.
## Copyright (C) 2010, 2011 CERN.
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

from invenio.config import CFG_ETCDIR
from invenio.bibformat_dblayer import get_tag_from_name
from invenio.errorlib import raise_exception


CFG_BIBRANK_WRD_CFG_PATH = '%s/bibrank/wrd.cfg' % CFG_ETCDIR


def alert_admin(name):
    raise_exception(ValueError, 'No marc tag for %s defined' % name, alert_admin=True)


# abstract:
marc_tag_abstract = get_tag_from_name('abstract')
if marc_tag_abstract:
    CFG_MARC_ABSTRACT = marc_tag_abstract
else:
    CFG_MARC_ABSTRACT = '520__a'
    alert_admin('abstract')


# author name:
marc_tag_author = get_tag_from_name('first author name')
if marc_tag_author:
    CFG_MARC_AUTHOR_NAME = marc_tag_author
else:
    CFG_MARC_AUTHOR_NAME = '100__a'
    alert_admin('first author name')


# additional author name:
marc_tag_contributor_name = get_tag_from_name('additional author name')
if marc_tag_contributor_name:
    CFG_MARC_ADDITIONAL_AUTHOR_NAME = marc_tag_contributor_name
else:
    CFG_MARC_ADDITIONAL_AUTHOR_NAME = '700__a'
    alert_admin('additional author name')


# keyword:
marc_tag_keyword = get_tag_from_name('%keyword')
if marc_tag_keyword:
    CFG_MARC_KEYWORD= marc_tag_keyword
else:
    CFG_MARC_KEYWORD = '6531_a'
    alert_admin('keyword')


# title:
marc_tag_title = get_tag_from_name('title')
if marc_tag_title:
    CFG_MARC_TITLE = marc_tag_title
else:
    CFG_MARC_TITLE = '245__a'
    alert_admin('title')
