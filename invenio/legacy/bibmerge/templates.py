# This file is part of Invenio.
# Copyright (C) 2009, 2010, 2011 CERN.
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

from __future__ import print_function

# pylint: disable=C0103

"""Invenio BibMerge Templates."""

__revision__ = "$Id$"

import string
from invenio.legacy.bibrecord import *
from invenio.legacy.bibmerge.differ import *

class Template:

    """BibMerge Templates Class."""

    def controlpanel(self, recid=None):
        """ Create the control panel."""
        if recid == None:
            recid = ''

        panel = """
<div id="bibMergePanel">

  <div id="bibMergeMessage">
  </div>

  <div class="bibMergeMenuSection" id="bibMergeMenuSectionSelectRecords">
    <div class="bibMergeMenuSectionHeader">
      <img class="bibMergeImgCompressMenuSelection" src="/img/bullet_toggle_minus.png" />
      Select records
    </div>
    <table>
      <col width="62px"></col>
      <col width="110px"></col>
      <tr>
      <td>Record1:</td>
      <td> <input type="text" class="bibMergeRecNumInput" id="bibMergeRecInput1"></input> </td>
      </tr>
      <tr>
      <td>Record2:</td>
      <td> <input type="text" class="bibMergeRecNumInput" id="bibMergeRecInput2"></input> </td>
      </tr>
      <tr>
      <td style="text-align:center;"> <button type="button" id="bibMergeCompare">Compare</button> </td>
      </tr>
    </table>
  </div>

  <div class="bibMergeMenuSection" id="bibMergeMenuSectionCandidates">
    <div class="bibMergeMenuSectionHeader">
      <img class="bibMergeImgCompressMenuSelection" src="/img/bullet_toggle_minus.png" />
      Candidates
    </div>
    <table>
      <col width="32px"></col>
      <col width="70px"></col>
      <col width="30px"></col>
      <col width="40px"></col>
      <tr>
      <td colspan="4"> <a id="bibMergeSelectSearch" href="#">Search</a> / <a id="bibMergeSelectDedupe" href="#">Dedupe</a> / <a id="bibMergeSelectRevisions" href="#">Revisions</a> </td>
      </tr>
      <tr id="bibMergeSearchRow">
      <td colspan="3"> <input type="text" id="bibMergeSearchInput"></input> </td>
      <td> <a href="#" class="bibMergeImgClickable" id="bibMergeBtnSearch" title="search candidate records">
           <img src="/img/search.png" /> </a>
      </td>
      </tr>
      <tr id="bibMergeSelectListRow">
      <td colspan="4">
        <select id="bibMergeSelectList" size="4">
        </select></td>
      </tr>
      <tr>
      <td style="text-align:center;"> <button type="button" id="bibMergeGetPrev">&lt</button> </td>
      <td id="bibMergeResultIndex" style="text-align:center;">-/-</td>
      <td style="text-align:center;"> <button type="button" id="bibMergeGetNext">&gt</button> </td>
      <td> </td>
      </tr>
    </table>
  </div>

  <div class="bibMergeMenuSection" id="bibMergeMenuSectionActions">
    <div class="bibMergeMenuSectionHeader">
      <img class="bibMergeImgCompressMenuSelection" src="/img/bullet_toggle_minus.png" />
      Actions
    </div>
    <table>
      <col width="20px"></col>
      <col width="152px"></col>
      <tr>
      <td> <a id="bibMergeRecCopy" class="bibMergeImgClickable" href="#" title="Copy R2 to R1"><img src="/img/move.png" /></a> </td>
      <td>Copy record</td>
      </tr>
      <tr>
      <td> <a id="bibMergeRecMerge" class="bibMergeImgClickable" href="#" title="Merge R1 with R2"><img src="/img/merge.png" /></a>
      </td>
      <td>Merge</td>
      </tr>
      <tr>
      <td> <a id="bibMergeRecMergeNC" class="bibMergeImgClickable" href="#" title="Merge R1 with R2 but only non-conflicting fields"><img src="/img/mergeNC.png" /></a> </td>
      <td>Merge non-conflicting</td>
      </tr>
      <tr>
      <td colspan="2"> <a id="bibMergeLinkToBibEdit1" href="#" title="Record editor for master record">Edit master record</a> </td>
      </tr>
      <tr>
      <td colspan="2"> <a id="bibMergeLinkToBibEdit2" href="#" title="Record editor for slave record">Edit slave record</a> </td>
      </tr>
    </table>
  </div>

  <div class="bibMergeMenuSection" id="bibMergeMenuSectionSubmission">
    <div class="bibMergeMenuSectionHeader">
      <img class="bibMergeImgCompressMenuSelection" src="/img/bullet_toggle_minus.png" />
      Submission
    </div>
    <table>
      <col width="72px"></col>
      <col width="10px"></col>
      <col width="90px"></col>
      <tr>
      <td> <button type="button" id="bibMergeBtnCancel">Cancel</button> </td>
      <td colspan="2">  </td>
      </tr>
      <tr>
      <td colspan="3"><br /></td>
      </tr>
      <tr>
      <td> <button type="button" id="bibMergeBtnSubmit">Submit</button> </td>
      <td> <input type="checkbox" id="bibMergeDupeCheckbox"></input> </td>
      <td>delete slave record as duplicate</td>
      </tr>
    </table>
  </div>

</div>"""
        return panel

    def BM_html_all_diff(self, rec1, rec2):
        return BM_html_field_group_div_all(rec1, rec2)

    def BM_html_field_group(self, rec1, rec2, fieldtag, show_diffs=False):
        """ Given two records and a fieldtag(which may or may not include
         indicators), returns the html output for the whole field(eg.700) group"""
        ftag = fieldtag[:3]
        if ftag not in rec1 and ftag not in rec2: #if empty field group
            return ""

        fdiff = record_field_diff_generic(rec1, rec2, ftag, match_subfields)
        result = ""
        if fdiff ==  None: #fields of this field tag are the same
            indicators = get_indicators(rec1[ftag])
            for ind_pair in indicators:
                result += BM_html_field_group_div(ftag, ind_pair[0], ind_pair[1], rec1, rec2, show_diffs, None)
        else:
            if fdiff[0] == 'a': #missing field in rec1
                indicators = get_indicators(rec2[ftag])
                for ind_pair in indicators:
                    result += BM_html_field_group_div(ftag, ind_pair[0], ind_pair[1], None, rec2, show_diffs, [])
            elif fdiff[0] == 'r': #missing field in rec2
                indicators = get_indicators(rec1[ftag])
                for ind_pair in indicators:
                    result += BM_html_field_group_div(ftag, ind_pair[0], ind_pair[1], rec1, None, show_diffs, [])
            else: #diff[0]=='c' #tag exists in both records but with differences
                for diff in fdiff[1]:
                    result += BM_html_field_group_div(ftag, diff[0][0], diff[0][1], rec1, rec2, show_diffs, diff[1])
        return result

    def BM_html_subfield_row_diffed(self, rec1, rec2, fieldtag, findex1, findex2, sfindex1, sfindex2):
        sftag = rec1[fieldtag][findex1][0][sfindex1][0]
        value1 = rec1[fieldtag][findex1][0][sfindex1][1]
        value2 = rec2[fieldtag][findex2][0][sfindex2][1]
        if value1 == value2:
            score = 1.0
        else:
            score = 0.0
        return BM_html_subfield(fieldtag, sftag, value1, value2, score, findex1, sfindex1, findex2, sfindex2, True)


####### Main content html #####################################################
def BM_html_field_group_div_all(rec1, rec2, show_diffs=False):
    """Produce html code for all the fields. (a <div> for  every field group)"""
    diff_results = record_diff(rec1, rec2, match_subfields)
    fieldtags = diff_results.keys()
    fieldtags.sort()
    result = ""
    for ftag in fieldtags:
        ftag = ftag.encode('utf8')
        if ftag[0:2] == "00": #starts with '00', is controlfield
            result += BM_html_controlfield(ftag, rec1, rec2)
        else:
            fdiff = diff_results[ftag]
            if fdiff ==  None: #fields of this field tag are the same
                indicators = get_indicators(rec1[ftag])
                for ind_pair in indicators:
                    result += BM_html_field_group_div(ftag, ind_pair[0], ind_pair[1], rec1, rec2, show_diffs, None)
            else:
                if fdiff[0] == 'a': #missing field in rec1
                    indicators = get_indicators(rec2[ftag])
                    for ind_pair in indicators:
                        result += BM_html_field_group_div(ftag, ind_pair[0], ind_pair[1], None, rec2, show_diffs, [])
                elif fdiff[0] == 'r': #missing field in rec2
                    indicators = get_indicators(rec1[ftag])
                    for ind_pair in indicators:
                        result += BM_html_field_group_div(ftag, ind_pair[0], ind_pair[1], rec1, None, show_diffs, [])
                else: #diff[0]=='c' #tag exists in both records but with differences
                    for diff in fdiff[1]:
                        result += BM_html_field_group_div(ftag, diff[0][0], diff[0][1], rec1, rec2, show_diffs, diff[1])
    return result


def BM_html_controlfield(tagnum, rec1, rec2):
    """Produce html code for a control field. A group field <div> is returned"""

    result = """
<div id="bibMergeFGroup-%s" class="bibMergeFieldGroupDiv">
  <div class="bibMergeFieldGroupHeaderDiv">
    <a href="#" class="bibMergeHeaderFieldnum">%s</a>
  </div>
  <table class="bibMergeFieldTable">
    <col span="1" class="bibMergeColSubfieldTag"/>
    <col span="1" class="bibMergeColContent bibMergeColContentLeft"/>
    <col span="1" class="bibMergeColActions"/>
    <col span="1" class="bibMergeColContent bibMergeColContentRight"/>
    <tbody>""" % (tagnum, tagnum)

    value1 = value2 = ""
    if record_has_field(rec1, tagnum):
        value1 = rec1[tagnum][0][3]
    if record_has_field(rec2, tagnum):
        value2 = rec2[tagnum][0][3]

    result += """
    <tr>
      <td></td>
      <td><div>%s</div></td>
      <td></td>
      <td><div>%s</div></td>
    </tr>""" % (value1, value2)

    result += """
    </tbody>
  </table>
</div>"""
    return result

def BM_html_field_group_div(tagnum, ind1, ind2, rec1, rec2, show_diffs, fdiff_list=None):
    """The html code for a group of fields. A <div> that contains a table is
    returned."""

    # add indicators next to field tag
    ftag = "%s%s%s" % (tagnum, ind1, ind2)
    ftag = string.replace(ftag, " ", "_")

    result = """
<div id="bibMergeFGroup-%s" class="bibMergeFieldGroupDiv">
  <div class="bibMergeFieldGroupHeaderDiv">
    <a href="#" class="bibMergeHeaderFieldnum">%s</a> <a class="bibMergeFieldGroupRefresh" href="#" title="refresh fields"><img src="/img/refresh.png" /></a> <a class="bibMergeFieldGroupMerge" href="#" title="merge fields"><img src="/img/merge.png" /></a> <a class="bibMergeFieldGroupMergeNC" href="#" title="merge non-conflicting fields"><img src="/img/mergeNC.png" /></a>
  </div>
  <table class="bibMergeFieldTable">
    <col span="1" class="bibMergeColSubfieldTag"/>
    <col span="1" class="bibMergeColContent bibMergeColContentLeft"/>
    <col span="1" class="bibMergeColActions"/>
    <col span="1" class="bibMergeColContent bibMergeColContentRight"/>
    <col span="1" class="bibMergeColDiff"/>
    <tbody>""" % (ftag, ftag)

    # if fields are the same in both records
    if fdiff_list==None:
        flist = rec1[tagnum] #only one field list is needed since they are the same
        indexes = get_indexes_of_fields(rec1, tagnum, ind1, ind2)
        for index in indexes:
            result += BM_html_field_header(ftag, flist, index, flist, index, show_diffs)
    # if the field is missing from one of the records
    elif rec1==None:
        flist = rec2[tagnum]
        indexes = get_indexes_of_fields(rec2, tagnum, ind1, ind2)
        for index in indexes:
            result += BM_html_field_header(ftag, None, None, flist, index, show_diffs)
    elif rec2==None:
        flist = rec1[tagnum]
        indexes = get_indexes_of_fields(rec1, tagnum, ind1, ind2)
        for index in indexes:
            result += BM_html_field_header(ftag, flist, index, None, None, show_diffs)
    # if there are differences between the fields of the records
    else:
        flist1 = rec1[tagnum]
        flist2 = rec2[tagnum]
        for fdiff in fdiff_list:
            result += BM_html_field_header(ftag, flist1, fdiff[0], flist2, fdiff[1], show_diffs, fdiff[2])
    result += """
    </tbody>
  </table>
</div>"""
    return result

def BM_html_field_header(ftag, flist1, findex1, flist2, findex2, show_diffs, sfdiff_list=None):
    """A table row that marks the beginning of a field is returned."""

    result ="""
    <tr>
      <td></td>
      <td %(id1)s class="bibMergeColHeaderLeft">
        <span style="float:left;">%(tagname)s</span>
        <a class="bibMergeFieldMerge" href="#" title="merge subfields"> <img src="/img/merge-small.png" /> </a>
        <a class="bibMergeFieldDelete" href="#" title="delete field"> <img src="/img/delete-big.png" /> </a> </td>
      <td></td>
      <td %(id2)s class="bibMergeColHeaderRight">
        <a class="bibMergeFieldAdd" href="#" title="add field"> <img src="/img/add.png" /> </a>
        <a class="bibMergeFieldReplace" href="#" title="replace field"> <img src="/img/replace.png" /> </a>
        <span style="float:right;">%(tagname)s</span> </td>
      <td></td>
    </tr>
    """ % {"tagname": ftag, 'id1': BM_field_id(1, ftag, findex1), 'id2': BM_field_id(2, ftag, findex2)}

    if findex1==None:
        sflist2 = flist2[findex2][0]
        sfindex = 0
        for sf in sflist2:
            sftag, sfvalue = sf
            result += BM_html_subfield(ftag, sftag, None, sfvalue, 0.0, None, None, findex2, sfindex, show_diffs)
            sfindex += 1
    elif findex2==None:
        sflist1 = flist1[findex1][0]
        sfindex = 0
        for sf in sflist1:
            sftag, sfvalue = sf
            result += BM_html_subfield(ftag, sftag, sfvalue, None, 0.0, findex1, sfindex, None, None, show_diffs)
            sfindex += 1
    else:
        sflist1 = flist1[findex1][0]
        sflist2 = flist2[findex2][0]
        if sfdiff_list != None: #fields are different
            for diff in sfdiff_list:
                sfindex1, sfindex2, score = diff
                sftag = sfvalue1 = sfvalue2 = ""
                if sfindex1!=None:
                    sftag = sflist1[sfindex1][0]
                    sfvalue1 = sflist1[sfindex1][1]
                if sfindex2!=None:
                    sftag = sflist2[sfindex2][0]
                    sfvalue2 = sflist2[sfindex2][1]
                result += BM_html_subfield(ftag, sftag, sfvalue1, sfvalue2, score, findex1, sfindex1, findex2, sfindex2, show_diffs)
        else: #fields are the same
            for i, sf in enumerate(sflist1):
                result += BM_html_subfield(ftag, sf[0], sf[1], sf[1], 1.0, findex1, i, findex2, i, show_diffs)
    return result

def BM_html_subfield(ftag, sftag, value1, value2, score, findex1, sfindex1, findex2, sfindex2, show_diffs=False):
    """A table row that shows a subfield diffing pair is returned."""
    if value1==None:
        similarity_class = "bibMergeCellSimilarityRed"
        value1=""
        #id1 = 'class="bibMergeEmptySubfield"'
        id1 = BM_subfield_id(1, ftag, findex1, sftag, sfindex1)
        id2 = BM_subfield_id(2, ftag, findex2, sftag, sfindex2)
    elif value2==None:
        similarity_class = "bibMergeCellSimilarityRed"
        value2=""
        id1 = BM_subfield_id(1, ftag, findex1, sftag, sfindex1)
        id2 = BM_subfield_id(2, ftag, findex2, sftag, sfindex2)
        #id2 = 'class="bibMergeEmptySubfield"'
    else:
        if show_diffs==True:
            value1, value2 = BM_html_add_diff_spans(value1, value2)
        if score < 1.0:
            similarity_class = "bibMergeCellSimilarityRed"
        else:
            similarity_class = "bibMergeCellSimilarityGreen"
        id1 = BM_subfield_id(1, ftag, findex1, sftag, sfindex1)
        id2 = BM_subfield_id(2, ftag, findex2, sftag, sfindex2)
    return """
    <tr>
      <td class="%s">$%s</td>
      <td><div>%s</div></td>
      <td><a class="bibMergeSubfieldDelete" href="#" title="delete subfield"> <img src="/img/delete-small.png" /> </a><a class="bibMergeSubfieldReplace" href="#" title="move subfield"> <img src="/img/move.png" /> </a><a class="bibMergeSubfieldAdd" href="#" title="add subfield"> <img src="/img/add-small.png" /> </a></td>
      <td><div>%s</div></td>
      <td><a class="bibMergeFieldGroupDiff" href="#" title="show differences"><img src="/img/diff.png" /></a></td>
    </tr>""" % (similarity_class, sftag, value1, value2)

def BM_field_id(record_position, ftag, findex): #record_position = 1 | 2
    """The id attribute of a subfield is produced."""
    return 'id="R%s-%s-%s"' % (record_position, ftag, findex)
def BM_subfield_id(record_position, ftag, findex, sftag, sfindex): #record_position = 1 | 2
    """The id attribute of a subfield is produced."""
    return 'id="R%s-%s-%s-%s-%s"' % (record_position, ftag, findex, sftag, sfindex)

def BM_html_add_diff_spans(value1, value2):
    """Adds the same values that it is passed, but with added <span> elements
    according to their differences."""
    value1 = value1.decode('utf8')
    value2 = value2.decode('utf8')

    newvalue1 = u""
    newvalue2 = u""
    index1 = 0
    index2 = 0
    idtag = 0
    for diff in Levenshtein_diffs(value1, value2):
        print(diff)
        chars = diff[1]
        if diff[0]=='n':
            newvalue1 += u"""<span class="bibMergeDiffSpanSame" id="diff%s">%s</span>""" % (idtag, value1[index1: index1+chars])
            newvalue2 += u"""<span class="bibMergeDiffSpanSame" id="diff%s">%s</span>""" % (idtag, value2[index2: index2+chars])
            index1 += chars
            index2 += chars
        elif diff[0]=='i':
            newvalue1 += u"""<span class="bibMergeDiffSpanIns" id="diff%s">%s</span>""" % (idtag, value1[index1: index1+chars])
            index1 += chars
        elif diff[0]=='d':
            newvalue2 += u"""<span class="bibMergeDiffSpanDel" id="diff%s">%s</span>""" % (idtag, value2[index2: index2+chars])
            index2 += chars
        else: #diff[0]=='s'
            newvalue1 += u"""<span class="bibMergeDiffSpanSub" id="diff%s">%s</span>""" % (idtag, value1[index1: index1+chars])
            newvalue2 += u"""<span class="bibMergeDiffSpanSub" id="diff%s">%s</span>""" % (idtag, value2[index2: index2+chars])
            index1 += chars
            index2 += chars
        idtag += 1
    return newvalue1.encode('utf8'), newvalue2.encode('utf8')


def get_indexes_of_fields(rec, tag, ind1, ind2):
    indexes = []
    if record_has_field(rec, tag):
        for index, field in enumerate(rec[tag]):
            if field[1]==ind1 and field[2]==ind2:
                indexes.append(index)
    return indexes

def get_fields_and_indicators(rec):
    result = {}
    for tag, flist in rec.items():
        result[tag] = get_indicators(flist)
    return result

def get_indicators(flist):
    indicators = []
    for field in flist:
        ind = "%s%s" % field[1:3] #a string of the two indicator characters
        append_unique(indicators, ind)
    return indicators

def append_unique(listobj, item):
    if item not in listobj:
        listobj.append(item)

def extend_set(list1, list2):
    for item in list2:
        if item not in list1:
            list1.append(item)

def all_fields_and_indicators(rec1, rec2):
    """The keys of the dictionary returned are field tags and the values are
    lists of the existing indicator pairs of rec1 and rec2 for the respective
    field tag."""
    tag_ind1 = get_fields_and_indicators(rec1)
    tag_ind2 = get_fields_and_indicators(rec2)
    for tag, ind_list in tag_ind1.items():
        if tag in tag_ind2:
            extend_set(ind_list, tag_ind2[tag])
            ind_list.sort()
            del tag_ind2[tag]
    for tag, ind_list in tag_ind2.items():
        ind_list.sort()
        tag_ind1[tag] = ind_list
    return tag_ind1

