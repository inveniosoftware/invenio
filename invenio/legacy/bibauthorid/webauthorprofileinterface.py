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

from invenio.legacy.bibauthorid.config import CLAIMPAPER_ADMIN_ROLE #emitting #pylint: disable-msg=W0611
from invenio.legacy.bibauthorid.config import CLAIMPAPER_USER_ROLE #emitting #pylint: disable-msg=W0611

#import invenio.legacy.bibauthorid.webapi as webapi
#import invenio.legacy.bibauthorid.config as bconfig

from invenio.legacy.bibauthorid.frontinterface import get_bibrefrec_name_string #emitting #pylint: disable-msg=W0611

from invenio.legacy.bibauthorid.webapi import search_person_ids_by_name #emitting #pylint: disable-msg=W0611
from invenio.legacy.bibauthorid.webapi import get_papers_by_person_id #emitting #pylint: disable-msg=W0611
from invenio.legacy.bibauthorid.dbinterface import get_person_db_names_count #emitting #pylint: disable-msg=W0611
from invenio.legacy.bibauthorid.dbinterface import get_existing_personids #emitting #pylint: disable-msg=W0611
from invenio.legacy.bibauthorid.webapi import get_person_redirect_link #emitting #pylint: disable-msg=W0611
from invenio.legacy.bibauthorid.webapi import is_valid_canonical_id #emitting #pylint: disable-msg=W0611
from invenio.legacy.bibauthorid.webapi import get_person_id_from_paper #emitting #pylint: disable-msg=W0611
from invenio.legacy.bibauthorid.webapi import get_person_id_from_canonical_id #emitting #pylint: disable-msg=W0611
from invenio.legacy.bibauthorid.dbinterface import  get_person_names_count #emitting #pylint: disable-msg=W0611
from invenio.legacy.bibauthorid.dbinterface import get_canonical_id_from_personid #emitting #pylint: disable-msg=W0611
from invenio.legacy.bibauthorid.dbinterface import get_coauthor_pids #emitting #pylint: disable-msg=W0611

from invenio.legacy.bibauthorid.name_utils import create_normalized_name #emitting #pylint: disable-msg=W0611
from invenio.legacy.bibauthorid.name_utils import split_name_parts #emitting #pylint: disable-msg=W0611
#from invenio.legacy.bibauthorid.config import CLAIMPAPER_CLAIM_OTHERS_PAPERS
from invenio.legacy.bibauthorid.config import AID_ENABLED #emitting #pylint: disable-msg=W0611
from invenio.legacy.bibauthorid.config import AID_ON_AUTHORPAGES #emitting #pylint: disable-msg=W0611

from invenio.legacy.bibauthorid import searchinterface as pt #emitting #pylint: disable-msg=W0611

def gathered_names_by_personid(pid):
    return [p[0] for p in get_person_names_count(pid)]
