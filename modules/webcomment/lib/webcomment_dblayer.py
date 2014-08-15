# -*- coding: utf-8 -*-

## This file is part of Invenio.
## Copyright (C) 2014 CERN.
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

""" WebComment database layer """

__revision__ = "$Id$"

from invenio.dbquery import run_sql
from invenio.bibdocfile import BibRecDocs


def get_comment_to_bibdoc_relations(recID):
    """
    Retrieve all comment to to bibdoc relations for the given record.

    and bibdocfiles they refer to.
    :param recID: Id of the record
    :return: correlations between comments and bibdocfiles
    """
    query = """
        SELECT  id_record,
                id_bibdoc,
                id_comment,
                version
        FROM    cmtRECORDCOMMENT_bibdoc
        WHERE   id_record = %s
    """

    comments_to_bibdoc = run_sql(query, (recID,), with_dict=True)
    brd = BibRecDocs(recID)
    bds = brd.list_bibdocs()
    res = []
    for bd in bds:
            for comments in comments_to_bibdoc:
                if comments['id_bibdoc'] == bd.id:
                    res.append({
                        'version': comments['version'],
                        'id_bibdoc': bd.id,
                        'docname': brd.get_docname(bd.id),
                        'id_comment': comments['id_comment']
                    })
    return res


def set_comment_to_bibdoc_relation(redID, cmtID, bibdocfileID, version):
    """
    Set a comment to bibdoc relation.

    :param redID: Id of the record
    :param cmtID: Id of the comment
    :param bibdocfileID: Id of the bibdocfile
    """
    query = """
        INSERT INTO cmtRECORDCOMMENT_bibdoc
                    (id_record,
                     id_comment,
                     id_bibdoc,
                     version)
        VALUES      (%s,
                     %s,
                     %s,
                     %s)
    """
    res = run_sql(query, (redID, cmtID, bibdocfileID, version))
    return res
