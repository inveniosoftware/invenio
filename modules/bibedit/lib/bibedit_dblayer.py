## $Id$
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008 CERN.
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
"""bibedit DB layer"""

__revision__ = "$Id$"

from invenio.dbquery import run_sql

def get_name_tag(tag):
    """This function returns a textual name of tag."""
    result = run_sql("SELECT name FROM tag WHERE value='%s'" % tag)

    if len(result) != 0:
        return result[0][0]

    else:
        return tag

def get_tag_name(name):
    """This function return a tag from the name of this tag."""
    result = run_sql("SELECT value FROM tag WHERE name LIKE '%s'" % name)

    if len(result) != 0:
        return result[0][0]

    else:
        return name

def split_tag_to_marc(tag, ind1='', ind2='', subcode=''):
    """This function make a marc tag with tag, ind1, ind2 and subcode."""
    tag = get_tag_name(tag)

    if len(tag) > 3:
        tag = tag[:3]

    if ind1 == ' ' or ind1 == '':
        ind1 = '_'

    if ind2 == ' ' or ind2 == '':
        ind2 = '_'

    if subcode == ' ' or subcode == '':
        subcode = '_'

    return "%s%s%s%s" % (tag, ind1, ind2, subcode)

def marc_to_split_tag(tag):
    """The inverse of split_tag_to_marc function."""
    tag = get_tag_name(tag)
    ind1 = ' '
    ind2 = ' '
    subcode = ''
    len_tag = len(tag)

    if len_tag > 3:

        ind1 = tag[3]
        if ind1 == '_' or ind1 == '':
            ind1 = ' '

        if len_tag > 4:

            ind2 = tag[4]
            if ind2 == '_' or ind2 == '':
                ind2 = ' '

            if len_tag > 5:
                subcode = tag[5]

    tag = tag[:3]

    return (tag, ind1, ind2, subcode)

def get_bibupload_task_opts(task_ids):
    """Returns a list with all options for a given list of task IDs."""
    res = []
    for task_id in task_ids:
        res.append(run_sql("SELECT arguments FROM schTASK WHERE id=%s" %
                           task_id))
    return res

def get_marcxml_of_record_revision(recid, job_date):
    """
    Return MARCXML string of revision corresponding to given recid
    and job date.
    """
    return run_sql("""SELECT marcxml FROM hstRECORD
                       WHERE id_bibrec=%s AND job_date=%s""",
                   (recid, job_date))

def get_record_revisions(recid):
    """Return dates for all known revisions of the given record."""
    return run_sql("""SELECT id_bibrec,
                             DATE_FORMAT(job_date, '%%Y%%m%%d%%H%%i%%s')
                        FROM hstRECORD WHERE id_bibrec=%s
                    ORDER BY job_date DESC""",
                   (str(recid),))