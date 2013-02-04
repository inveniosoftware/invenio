## This file is part of Invenio.
## Copyright (C) 2010, 2011, 2012, 2013 CERN.
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


def get_external_word_similarity_ranker():
    for line in open('%s/bibrank/wrd.cfg' % CFG_ETCDIR):
        for ranker in ('solr', 'xapian'):
            if 'word_similarity_%s' % ranker in line:
                return ranker
    return False
