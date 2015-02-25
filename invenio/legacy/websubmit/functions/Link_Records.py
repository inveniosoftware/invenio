
# This file is part of Invenio.
# Copyright (C) 2012, 2014 CERN.
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

"""
This function schedule a BibUpload append that will create a symmetric link
between two records based on the MARC field 787 OTHER RELATIONSHIP ENTRY (R)
(or base on other MARC field, see parameters C{directRelationshipMARC} and
C {reverseRelationshipMARC})

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

from invenio.legacy.bibrecord import \
     record_xml_output, \
     record_add_field, \
     record_add_fields, \
     record_get_field_instances, \
     create_record
from invenio.modules.formatter import format_record
from invenio.modules.formatter.api import get_tag_from_name
from invenio.legacy.search_engine import search_pattern, get_fieldvalues
from invenio.config import CFG_TMPDIR
from invenio.legacy.bibsched.bibtask import task_low_level_submission, bibtask_allocate_sequenceid
from invenio.legacy.websubmit.config import InvenioWebSubmitFunctionError


CFG_OTHER_RELATIONSHIP_ENTRY = (get_tag_from_name('other relationship entry') or '787')[:3]
CFG_PRIMARY_REPORTNUMBER = get_tag_from_name('primary report number') or '037__a'
RE_FILENAME = re.compile("\\<pa\\>file\\:(.+)\\<\\/pa\\>", re.I)

def Link_Records(parameters, curdir, form, user_info=None):
    """
    This function create a MARC link between two records (the 1st specified in the
    edsrn file or SN, the second specified by edsrn2 file, where you can store
    the reportnumber or directly the recid.

    Parameters:

     * edsrn: the file containing the report number or recid of the
       first record (A) to be linked.

     * edsrn2: the file containing the report number(s) or recid(s) of
       the second record(s) (B) to be linked (one value per line).

     * In "directRelationship" you should specify either the name of a file (by using
       <pa>file:filename</pa>) or directly, what is the relationship
       of the second record to be stored in the metadata of the 1st record (A->B).
       Use the keyword "none" if you explicitely want to skip the recording of
       this relation (no modification of record A).

     * In the value/file "reverseRelationship" you can similarly specify the other
       direction of the arrow (B->A)
       Use the keyword "none" if you explicitely want to skip the recording of
       this relation (no modification of record(s) B).

     * keep_original_edsrn2: if edsrn2 is a report number, should we
       use it as label when linking, or shall we use instead the
       report number retrieved from the matching record?

     * directRelationshipMARC: in which MARC tag + indicators shall we
       store the relation in the first record (A). By default uses the
       value found in tag name "other relationship entry" or 7870_.
       The value can be directly provided or specifed in file (using
       <pa>file:filename</pa>)

     * reverseRelationshipMARC: in which MARC tag + indicators shall we
       store the relation in the second record (B). By default uses the
       value found in tag name "other relationship entry" or 7870_.
       The value can be directly provided or specifed in file (using
       <pa>file:filename</pa>)

     * bibuploadMode: shall the created XML be sent in --append mode
       (default) or using --correct. Possible values are:
         * append (or leave empty)
         * correct
         This setting will depend on how you have set up your
         submisson workflow.

     * silentFailures: if set to "True", do not raise an exception
       when the linking fails due to impossibility to retrieve the
       corresponding "remote" record(s) B (for eg. non-existing report
       number, report number matching several records, etc.). In these
       cases the faulty report number is ignored.

     * considerEmpty: when using bibuploadMode with 'correct', should
       missing linking information (edsrn2 values) removes the linking
       or simply not do anything? You might want to tweak this setting
       depending on how the submission is presenting MBI pages (either
       full form, or selected fields).  If False (or empty), and no
       linking information is provided, the linking is not removed
       from the original record.  If True (or any other value), and no
       linking information is provided, the linking is removed from
       the record.  The value can be directly provided or specifed in
       file (using <pa>file:filename</pa>)
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
    direct_relationship_MARC = parameters["directRelationshipMARC"]
    reverse_relationship_MARC = parameters["reverseRelationshipMARC"]
    bibupload_mode = parameters["bibuploadMode"]
    if not bibupload_mode in ('append', 'correct'):
        bibupload_mode = 'append'
    silent_failures_p = parameters.get("silentFailures", "True") == 'True'

    consider_empty_p = parameters.get("considerEmpty", "False")
    g = RE_FILENAME.match(consider_empty_p)
    if g:
        filename = g.group(1)
        if exists(join(curdir, filename)):
            consider_empty_p = open(join(curdir, filename)).read().strip()
        else:
            consider_empty_p = ''
    if consider_empty_p in ('False', ''):
        consider_empty_p = False
    else:
        consider_empty_p = True

    recid_a = int(sysno)
    if exists(join(curdir, edsrn)):
        rn_a = open(join(curdir, edsrn)).read().strip()
    else:
        rn_a = ""
    if not rn_a:
        try:
            recid_a, rn_a = get_recid_and_reportnumber(recid=sysno)
        except ValueError as err:
            raise InvenioWebSubmitFunctionError("Error in finding the current record and its reportnumber: %s" % err)

    g = RE_FILENAME.match(direct_relationship)
    if g:
        filename = g.group(1)
        if exists(join(curdir, filename)):
            direct_relationship = open(join(curdir, filename)).read().strip()
    if not direct_relationship:
        raise InvenioWebSubmitFunctionError("Can not retrieve direct relationship")
    elif direct_relationship == 'none':
        direct_relationship  = None

    g = RE_FILENAME.match(reverse_relationship)
    if g:
        filename = g.group(1)
        if exists(join(curdir, filename)):
            reverse_relationship = open(join(curdir, filename)).read().strip()
    if not reverse_relationship:
        raise InvenioWebSubmitFunctionError("Can not retrieve reverse relationship")
    elif reverse_relationship == 'none':
        reverse_relationship = None

    g = RE_FILENAME.match(direct_relationship_MARC)
    if g:
        filename = g.group(1)
        if exists(join(curdir, filename)):
            direct_relationship_MARC = open(join(curdir, filename)).read().strip()

    g = RE_FILENAME.match(reverse_relationship_MARC)
    if g:
        filename = g.group(1)
        if exists(join(curdir, filename)):
            reverse_relationship_MARC = open(join(curdir, filename)).read().strip()

    recids_and_rns_b = []
    if exists(join(curdir, edsrn2)):
        for rn_b in open(join(curdir, edsrn2)).readlines():
            rn_b = rn_b.strip()
            if not rn_b:
                continue

            if rn_b.isdigit():
                recid_b = int(rn_b)
                rn_b = ""
                try:
                    recid_b, rn_b = get_recid_and_reportnumber(recid=recid_b)
                except ValueError, err:
                    if silent_failures_p:
                        continue
                    raise
            else:
                try:
                    recid_b, rn_b = get_recid_and_reportnumber(reportnumber=rn_b,
                                                               keep_original_reportnumber=keep_original_edsrn2)
                except ValueError, err:
                    if silent_failures_p:
                        continue
                    raise
            recids_and_rns_b.append((recid_b, rn_b))

    if not recids_and_rns_b and bibupload_mode == 'append':
        return ""

    marcxml = _prepare_marcxml(recid_a, rn_a, recids_and_rns_b, reverse_relationship, direct_relationship,
                               marc_for_a=direct_relationship_MARC, marc_for_b=reverse_relationship_MARC,
                               upload_mode=bibupload_mode, consider_empty_p=consider_empty_p)
    fd, name = tempfile.mkstemp(dir=CFG_TMPDIR, prefix="%s_%s" % \
                              (rn_a.replace('/', '_'),
                               time.strftime("%Y-%m-%d_%H:%M:%S")), suffix=".xml")
    try:
        os.write(fd, marcxml)
    finally:
        os.close(fd)

    sequence_id = bibtask_allocate_sequenceid(curdir)
    bibupload_id = task_low_level_submission('bibupload', 'websubmit.Link_Records', '--' + bibupload_mode, name, '-P', '3', '-I', str(sequence_id))
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
            raise ValueError('More than one record matches the reportnumber "%s": %s' % (reportnumber, ', '.join([str(i) for i in recids])))
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

def get_unlinked_records(recid_a, marc_for_b, display_in_b, upload_mode, recids_and_rns_b):
    """
    Retrieve list of recids that were already linked to recid_a using
    this relation (marc_for_b), and that should no longer be linked
    after this update (in 'correct' mode) as they are no longer part of
    recids_and_rns_b.
    """
    unlinked_recids = []
    if upload_mode == 'correct':
        marc_tag_for_b, marc_ind1_for_b, marc_ind2_for_b = \
        _prepare_marc(marc_for_b, CFG_OTHER_RELATIONSHIP_ENTRY, display_in_b and "0" or "1")
        already_linked_recids = search_pattern(p=str(recid_a), m='e', f=marc_tag_for_b + marc_ind1_for_b + marc_ind2_for_b + 'w')
        to_be_linked_recids = [recid for recid, rn in recids_and_rns_b]
        unlinked_recids = [recid for recid in already_linked_recids if not recid in to_be_linked_recids]
    return unlinked_recids

def _prepare_marcxml(recid_a, rn_a, recids_and_rns_b, what_is_a_for_b, what_is_b_for_a, display_in_a=True, display_in_b=True, marc_for_a=None, marc_for_b=None, upload_mode='append', consider_empty_p=False):
    output = '<collection>'
    record_a = {}
    record_b = {}
    if what_is_b_for_a is not None:
        marc_tag_for_a, marc_ind1_for_a, marc_ind2_for_a = \
          _prepare_marc(marc_for_a, CFG_OTHER_RELATIONSHIP_ENTRY, display_in_a and "0" or "1")
        record_add_field(record_a, "001", controlfield_value=str(recid_a))
        if upload_mode == 'correct' and not recids_and_rns_b and consider_empty_p:
            # Add empty field in order to account for cases where all
            # linkings are removed by the submitter
            record_add_field(record_a, marc_tag_for_a, ind1=marc_ind1_for_a, ind2=marc_ind2_for_a)
        for recid_b, rn_b in recids_and_rns_b:
            record_add_field(record_a, marc_tag_for_a, ind1=marc_ind1_for_a, ind2=marc_ind2_for_a,
                             subfields=[('i', what_is_b_for_a), ('r', rn_b), ('w', str(recid_b))])
        output += record_xml_output(record_a)

    if what_is_a_for_b is not None:
        marc_tag_for_b, marc_ind1_for_b, marc_ind2_for_b = \
          _prepare_marc(marc_for_b, CFG_OTHER_RELATIONSHIP_ENTRY, display_in_b and "0" or "1")
        for recid_b, rn_b in recids_and_rns_b:
            record_b = {}
            record_add_field(record_b, "001", controlfield_value=str(recid_b))
            if upload_mode == 'correct':
                original_linking_fields = _get_record_linking_fields(recid_b, recid_a, marc_tag_for_b, marc_ind1_for_b, marc_ind2_for_b)
                record_add_fields(record_b, marc_tag_for_b, original_linking_fields)
            record_add_field(record_b, marc_tag_for_b, ind1=marc_ind1_for_b, ind2=marc_ind2_for_b,
                             subfields=[('i', what_is_a_for_b), ('r', rn_a), ('w', str(recid_a))])
            output += record_xml_output(record_b)
        # Remove linking in remote records where adequate
        if consider_empty_p:
            unlinked_recids = get_unlinked_records(recid_a, marc_for_b, display_in_b, upload_mode, recids_and_rns_b)
            for recid_b in unlinked_recids:
                record_b = {}
                record_add_field(record_b, "001", controlfield_value=str(recid_b))
                original_linking_fields = _get_record_linking_fields(recid_b, recid_a, marc_tag_for_b, marc_ind1_for_b, marc_ind2_for_b)
                if not original_linking_fields:
                    # Add empty field in order to account for cases where all
                    # linkings are removed by the submitter
                    record_add_field(record_b, marc_tag_for_b, ind1=marc_ind1_for_b, ind2=marc_ind2_for_b)
                record_add_fields(record_b, marc_tag_for_b, original_linking_fields)
                output += record_xml_output(record_b)
    output += '</collection>'
    return output

def _get_record_linking_fields(recid_b, recid_a, tag, ind1, ind2):
    """
    Returns the fields (defined by tag, ind1, ind2) in record (given
    by recid_b) that do not link to another given record (recid_a).
    """
    fields = []
    rec = create_record(format_record(recid_b, "xm"))[0]
    for field_instance in record_get_field_instances(rec, tag=tag, ind1=ind1, ind2=ind2):
        if not ('w', str(recid_a)) in field_instance[0]:
            fields.append(field_instance)
    return fields

def _prepare_marc(marc_txt, default_tag, default_ind1=" ", default_ind2=" "):
    """Returns (tag, ind1, ind2) tuple by parsing input marc_txt and
    falling back to default value if needed"""
    marc_tag = default_tag
    marc_ind1 = default_ind1
    marc_ind2 = default_ind2

    if marc_txt:
        if len(marc_txt) > 2:
            marc_tag = marc_txt[:3]
            if len(marc_txt) > 3:
                marc_ind1 = marc_txt[3]
                if len(marc_txt) > 4:
                    marc_ind2 = marc_txt[4]

    return (marc_tag, marc_ind1, marc_ind2)
