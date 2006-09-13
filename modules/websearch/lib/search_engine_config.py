## $Id$
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006 CERN.
##
## CDS Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.  
##
## You should have received a copy of the GNU General Public License
## along with CDS Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""CDS Invenio Search Engine config parameters."""

__revision__ = \
    "$Id$"

## import config variables defined from config.wml:
from invenio.config import cfg_max_recID, \
     cfg_instant_browse, \
     cfg_author_et_al_threshold, \
     cfg_search_cache_size, \
     cfg_nb_records_to_sort, \
     cfg_call_bibformat, \
     cfg_use_aleph_sysnos, \
     cfg_fields_convert, \
     cfg_simplesearch_pattern_box_width, \
     cfg_advancedsearch_pattern_box_width, \
     cfg_narrow_search_show_grandsons, \
     cfg_oaiidtag, \
     cfg_create_similarly_named_authors_link_box, \
     cfg_google_box, \
     cfg_google_box_servers

## do we want experimental features? (0=no, 1=yes)
CFG_EXPERIMENTAL_FEATURES = 0
