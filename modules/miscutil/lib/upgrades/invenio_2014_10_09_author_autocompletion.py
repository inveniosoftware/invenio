# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""Upgrade recipe for new column tag.recjson_value."""

import os

from invenio.dbquery import run_sql
from invenio.config import CFG_PREFIX

depends_on = ['invenio_release_1_1_0']


def info():
    """Upgrade recipe information."""
    return "Set up autocompletion for DEMOTHE authors"


def do_upgrade():
    """Upgrade recipe procedure."""
    os.system("cd %(prefix)s/var/www/js && \
               wget https://cdnjs.cloudflare.com/ajax/libs/handlebars.js/1.3.0/handlebars.min.js && \
               wget https://twitter.github.com/typeahead.js/releases/0.10.5/typeahead.bundle.min.js && \
               wget https://raw.githubusercontent.com/es-shims/es5-shim/v4.0.3/es5-shim.min.js && \
               wget https://raw.githubusercontent.com/es-shims/es5-shim/v4.0.3/es5-shim.map"
              % {'prefix': CFG_PREFIX})

    # Remove "one line per author" info on author textbox
    run_sql("""UPDATE sbmFIELD
                set fitext='<br /><br /><table width="100%"><tr><td valign="top"><span style="color: red;">*</span>Author of the Thesis:<br />'
                where fidesc="DEMOTHE_AU";""")

    # Add the response logic to the DEMOTHE_AU element
    run_sql("""REPLACE sbmFIELDDESC VALUES ('DEMOTHE_AU',NULL,'100__a','R',NULL,6,60,NULL,NULL,'from invenio.websubmit_engine import get_authors_autocompletion\r\n\r\nrecid = action == "MBI" and sysno or None\r\nauthor_sources = ["bibauthority"]\r\nextra_options = {\r\n    "allow_custom_authors": True,\r\n    "highlight_principal_author": True,\r\n}\r\nextra_fields = {\r\n    "contribution": False,\r\n}\r\n\r\ntext = get_authors_autocompletion(\r\n    element,\r\n    recid,\r\n    curdir,\r\n    author_sources,\r\n    extra_options,\r\n    extra_fields\r\n)','2008-03-02','2014-06-30','',NULL,0);""")

    # Create the process_author_json_function
    run_sql("INSERT INTO sbmFUNDESC VALUES ('process_authors_json','authors_json');")

    # Add it to the DEMOTHE workflow
    run_sql("INSERT INTO sbmPARAMETERS VALUES ('DEMOTHE','authors_json','DEMOTHE_AU');")

    # Add proccess_author_json into the submission function sequence for DEMOTHESIS
    run_sql("INSERT INTO sbmFUNCTIONS VALUES ('SBI','DEMOTHE','process_authors_json',50,1);")
    run_sql("UPDATE sbmFUNCTIONS set score=100 where action='SBI' and doctype='DEMOTHE' and function='Move_to_Done';")
    run_sql("UPDATE sbmFUNCTIONS set score=90 where action='SBI' and doctype='DEMOTHE' and function='Mail_Submitter';")
    run_sql("UPDATE sbmFUNCTIONS set score=80 where action='SBI' and doctype='DEMOTHE' and function='Print_Success';")
    run_sql("UPDATE sbmFUNCTIONS set score=70 where action='SBI' and doctype='DEMOTHE' and function='Insert_Record';")
    run_sql("UPDATE sbmFUNCTIONS set score=60 where action='SBI' and doctype='DEMOTHE' and function='Make_Record';")

    # Add proccess_author_json into the modification function sequence for DEMOTHESIS
    run_sql("INSERT INTO sbmFUNCTIONS VALUES ('MBI','DEMOTHE','process_authors_json',40,2);")
    run_sql("UPDATE sbmFUNCTIONS set score=90 where action='MBI' and doctype='DEMOTHE' and function='Move_to_Done';")
    run_sql("UPDATE sbmFUNCTIONS set score=80 where action='MBI' and doctype='DEMOTHE' and function='Send_Modify_Mail';")
    run_sql("UPDATE sbmFUNCTIONS set score=70 where action='MBI' and doctype='DEMOTHE' and function='Print_Success_MBI';")
    run_sql("UPDATE sbmFUNCTIONS set score=60 where action='MBI' and doctype='DEMOTHE' and function='Insert_Modify_Record';")
    run_sql("UPDATE sbmFUNCTIONS set score=50 where action='MBI' and doctype='DEMOTHE' and function='Make_Modify_Record';")


def estimate():
    """Upgrade recipe time estimate."""
    return 1
