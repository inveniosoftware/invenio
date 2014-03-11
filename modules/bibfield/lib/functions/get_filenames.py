# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2004, 2005, 2006, 2007, 2008, 2010,
##               2011, 2013, 2014 CERN.
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

from invenio.bibdocfile import BibRecDocs


def get_filenames(recid):
    """
        Returns names of the files associated with specific record
        and their derivatives. Takes as a parameter the recid of a
        record.

        Example:
        input: recID 999 (record with files ['thesis.ps.gz', 'random.pdf'])
        output: ['thesis.ps.gz', 'thesis.ps', 'thesis',
                 'random.pdf', 'random']
        @param recid: recid of a record
    """
    docs = BibRecDocs(recid)
    names = [_get_filenames(d.name + d.format)
                for d in docs.list_latest_files()]
    return reduce(lambda x,y: x+y, names)


def _get_filenames(full_filename):
    parts = full_filename.split(".")
    names = [parts[0]]
    for p in parts[1:]:
        names.append(names[-1] + "." + p)
    return list(set(names))
