# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2011 CERN.
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

from invenio.bibauthorid_config import CLAIMPAPER_ADMIN_ROLE
from invenio.bibauthorid_config import CLAIMPAPER_USER_ROLE

#import invenio.bibauthorid_webapi as webapi
#import invenio.bibauthorid_config as bconfig

from invenio.bibauthorid_frontinterface import get_bibrefrec_name_string

from invenio.bibauthorid_webapi import search_person_ids_by_name
from invenio.bibauthorid_webapi import get_papers_by_person_id
from invenio.bibauthorid_dbinterface import get_person_db_names_count, get_person_names_count
from invenio.bibauthorid_dbinterface import get_existing_personids
from invenio.bibauthorid_webapi import get_person_redirect_link
from invenio.bibauthorid_webapi import is_valid_canonical_id
from invenio.bibauthorid_webapi import get_person_id_from_paper
from invenio.bibauthorid_webapi import get_person_id_from_canonical_id
from invenio.bibauthorid_dbinterface import  get_person_names_count
from invenio.bibauthorid_dbinterface import get_canonical_id_from_personid
from invenio.bibauthorid_dbinterface import get_coauthor_pids

from invenio.bibauthorid_name_utils import create_normalized_name
from invenio.bibauthorid_name_utils import split_name_parts
#from invenio.bibauthorid_config import CLAIMPAPER_CLAIM_OTHERS_PAPERS
from invenio.bibauthorid_config import AID_ENABLED
from invenio.bibauthorid_config import AID_ON_AUTHORPAGES

import bibauthorid_searchinterface as pt

def gathered_names_by_personid(pid):
    return [p[0] for p in get_person_names_count(pid)]
