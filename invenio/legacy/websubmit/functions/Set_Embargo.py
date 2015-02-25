# This file is part of Invenio.
# Copyright (C) 2011, 2012, 2013, 2014, 2015 CERN.
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

"""File which contains the WebSubmit function Set_Embargo."""

import os
import time

from invenio.legacy.bibdocfile.api import BibRecDocs


def Set_Embargo(parameters, curdir, form):
    """set the embargo on all the documents of a given record.

    @param date_file: the file from which to read the embargo end date.
    @param date_format: the format in which the date in L{date_file} is
        expected to be found. (default C{%Y-%m-%d})
    @note: this function should be used after any file that need to
        be added to a record has been added, that is after any call to
        e.g. L{Move_Files_to_Storage}
    @note: This function expect C{sysno} to exist and be set to the current record.
        (that means it should be called after L{Get_Recid} or L{Create_Recid})
    """
    ## Let's retrieve the date from date_file.
    date_file = parameters['date_file']

    if not date_file or not os.path.isfile(os.path.join(curdir, date_file)):
        return

    date = open(os.path.join(curdir, date_file)).read().strip()
    if not date:
        return
    ## Let's retrieve the expected date format.
    date_format = parameters['date_format'].strip()
    if not date_format:
        date_format = '%Y-%m-%d'

    ## Date normalization.
    date = time.strftime("%Y-%m-%d", time.strptime(date, date_format))

    ## Let's prepare the firerole rule.
    firerole = """
deny until "%s"
allow all
""" % date

    ## Applying the embargo.
    for bibdoc in BibRecDocs(sysno).list_bibdocs():
        bibdoc.set_status("firerole: {0}".format(firerole))
