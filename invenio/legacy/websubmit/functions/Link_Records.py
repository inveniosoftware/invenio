
## This file is part of Invenio.
## Copyright (C) 2012 CERN.
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

"""
This function schedule a BibUpload append that will create a symmetric link
between two records based on the MARC field 787 OTHER RELATIONSHIP ENTRY (R)

787 OTHER RELATIONSHIP ENTRY (R)

Indicators
First Note controller
0 - Display note (in $i)
1 - Do not display note

Subfield Code(s)

$i Relationship information (R) - [CER]
$r Report number
$w Record control number (R) - [CER]

NOTE: Used to link Conference papers and Slides records ($i Conference paper/Slides - $w CDS recid)


Example:
http://cds.cern.ch/record/1372158
7870_ $$iSlides$$rLHCb-TALK-2011-087$$w1353576
We need to include in the submission form for LHCb-PROC a field for the related repnr, from which to create the 7870 field. It would be perfect if at the same time the inverse 7870 field could be inserted in the TALK record:
7870_ $$iConference paper$$rLHCb-PROC-2011-041$$w1372158
"""

import re
import tempfile
import time
import os

from os.path import exists, join

from invenio.legacy.bibrecord import record_xml_output, record_add_field
from invenio.modules.formatter.api import get_tag_from_name
from invenio.search_engine import search_pattern, get_fieldvalues
from invenio.config import CFG_TMPDIR
from invenio.bibtask import task_low_level_submission
from invenio.legacy.websubmit.config import InvenioWebSubmitFunctionError


CFG_OTHER_RELATIONSHIP_ENTRY = (get_tag_from_name('other relationship entry') or '787')[:3]
CFG_PRIMARY_REPORTNUMBER = get_tag_from_name('primary report number') or '037__a'
RE_FILENAME = re.compile("\\<pa\\>file\\:(.+)\\<\\/pa\\>", re.I)

def Link_Records(parameters, curdir, form, user_info=None):
    """
    This function create a MARC link between two records (the 1st specified in the
    edsrn file or SN, the second specified by edsrn2 file, where you can store
    the reportnumber or directly the recid.
    In "directRelationship" you should specify either the name of a file (by using
    <pa>file:filename</pa>) or direclty, what is the relationship
    of the second record to be stored in the metadata of the 1st record.
    In the file "reverseRelationship" you can similarly specify the other
    direction of the harrow.
    """
    global sysno
    edsrn = parameters["edsrn"]
    edsrn2 = parameters["edsrn2"]
    direct_relationship = parameters["directRelationship"]
    reverse_relationship = parameters["reverseRelationship"]
    keep_original_edsrn2 = parameters.get("keep_original_edsrn2", "True")
    if keep_original_edsrn2 == "True":
        keep_original_edsrn2 = True
    elif keep_original_edsrn2 == "False":
        keep_original_edsrn2 = False
    else:
        keep_original_edsrn2 = True
    recid_a = int(sysno)
    if exists(join(curdir, edsrn)):
        rn_a = open(join(curdir, edsrn)).read().strip()
    else:
        rn_a = ""
    if not rn_a:
        try:
            recid_a, rn_a = get_recid_and_reportnumber(recid=sysno)
        except ValueError, err:
            raise InvenioWebSubmitFunctionError("Error in finding the current record and its reportnumber: %s" % err)

    if exists(join(curdir, edsrn2)):
        rn_b = open(join(curdir, edsrn2)).read().strip()
    else:
        return ""
    if not rn_b:
        return ""

    if rn_b.isdigit():
        recid_b = int(rn_b)
        rn_b = ""
        recid_b, rn_b = get_recid_and_reportnumber(recid=recid_b)
    else:
        recid_b, rn_b = get_recid_and_reportnumber(reportnumber=rn_b,
                                                   keep_original_reportnumber=keep_original_edsrn2)

    g = RE_FILENAME.match(direct_relationship)
    if g:
        filename = g.group(1)
        if exists(join(curdir, filename)):
            direct_relationship = open(join(curdir, filename)).read().strip()
    if not direct_relationship:
        raise InvenioWebSubmitFunctionError("Can not retrieve direct relationship")

    g = RE_FILENAME.match(reverse_relationship)
    if g:
        filename = g.group(1)
        if exists(join(curdir, filename)):
            reverse_relationship = open(join(curdir, filename)).read().strip()
    if not reverse_relationship:
        raise InvenioWebSubmitFunctionError("Can not retrieve reverse relationship")

    marcxml = _prepare_marcxml(recid_a, rn_a, recid_b, rn_b, reverse_relationship, direct_relationship)
    fd, name = tempfile.mkstemp(dir=CFG_TMPDIR, prefix="%s_%s" % \
                              (rn_a.replace('/', '_'),
                               time.strftime("%Y-%m-%d_%H:%M:%S")), suffix=".xml")
    try:
        os.write(fd, marcxml)
    finally:
        os.close(fd)

    bibupload_id = task_low_level_submission('bibupload', 'websubmit.Link_Records', '-a', name, '-P', '3')
    open(join(curdir, 'bibupload_link_record_id'), 'w').write(str(bibupload_id))
    return ""

def get_recid_and_reportnumber(recid=None, reportnumber=None, keep_original_reportnumber=True):
    """
    Given at least a recid or a reportnumber, this function will look into
    the system for the matching record and will return a normalized
    recid and the primary reportnumber.
    @raises ValueError: in case of no record matched.
    """
    if recid:
        ## Recid specified receives priority.
        recid = int(recid)
        values = get_fieldvalues(recid, CFG_PRIMARY_REPORTNUMBER)
        if values:
            ## Let's take whatever reportnumber is stored in the matching record
            reportnumber = values[0]
            return recid, reportnumber
        else:
            raise ValueError("The record %s does not have a primary report number" % recid)
    elif reportnumber:
        ## Ok reportnumber specified, let's better try 1st with primary and then
        ## with other reportnumber
        recids = search_pattern(p='%s:"%s"' % (CFG_PRIMARY_REPORTNUMBER, reportnumber))
        if not recids:
            ## Not found as primary
            recids = search_pattern(p='reportnumber:"%s"' % reportnumber)
        if len(recids) > 1:
            raise ValueError('More than one record matches the reportnumber "%s": %s' % (reportnumber, ', '.join(recids)))
        elif len(recids) == 1:
            recid = list(recids)[0]
            if keep_original_reportnumber:
                return recid, reportnumber
            else:
                reportnumbers = get_fieldvalues(recid, CFG_PRIMARY_REPORTNUMBER)
                if not reportnumbers:
                    raise ValueError("The matched record %s does not have a primary report number" % recid)
                return recid, reportnumbers[0]
        else:
            raise ValueError("No records are matched by the provided reportnumber: %s" % reportnumber)
    raise ValueError("At least the recid or the reportnumber must be specified")


def _prepare_marcxml(recid_a, rn_a, recid_b, rn_b, what_is_a_for_b, what_is_b_for_a, display_in_a=True, display_in_b=True):
    record_a = {}
    record_b = {}
    record_add_field(record_a, "001", controlfield_value=str(recid_a))
    record_add_field(record_a, CFG_OTHER_RELATIONSHIP_ENTRY, ind1=display_in_a and "0" or "1", subfields=[('i', what_is_b_for_a), ('r', rn_b), ('w', str(recid_b))])
    record_add_field(record_b, "001", controlfield_value=str(recid_b))
    record_add_field(record_b, CFG_OTHER_RELATIONSHIP_ENTRY, ind1=display_in_b and "0" or "1", subfields=[('i', what_is_a_for_b), ('r', rn_a), ('w', str(recid_a))])
    return "<collection>\n%s\n%s</collection>" % (record_xml_output(record_a), record_xml_output(record_b))

