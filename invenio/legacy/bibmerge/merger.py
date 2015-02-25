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

# pylint: disable=C0103

from invenio.legacy.bibrecord import record_has_field, \
                              record_get_field_instances, \
                              record_delete_field, \
                              record_add_fields

from invenio.legacy.bibmerge.differ import record_field_diff, match_subfields, \
                                    diff_subfields

from copy import deepcopy

def merge_record(rec1, rec2, merge_conflicting_fields=False):
    """Merges all non-conflicting fields from 'rec2' to 'rec1'
    @param rec1: First record (a record dictionary structure)
    @param rec2: Second record (a record dictionary structure)
    """
    for fnum in rec2:
        if fnum[:2] != "00": #if it's not a controlfield
            merge_field_group(rec1, rec2, fnum, merge_conflicting_fields=merge_conflicting_fields)

def merge_field_group(rec1, rec2, fnum, ind1='', ind2='', merge_conflicting_fields=False):
    """Merges non-conflicting fields from 'rec2' to 'rec1' for a specific tag.
    the second record.
    @param rec1: First record (a record dictionary structure)
    @param rec2: Second record (a record dictionary structure)
    @param fnum: a 3 characters long string indicating field tag number
    @param ind1: a 1 character long string
    @param ind2: a 1 character long string
    @param merge_conflicting_fields: whether to merge conflicting fields or not
    """
    ### Check if merging goes for all indicators and set a boolean
    merging_all_indicators = not ind1 and not ind2

    ### check if there is no field in rec2 to be merged in rec1
    if not record_has_field(rec2, fnum):
        return

    ### get fields of rec2
    if merging_all_indicators:
        fields2 = record_get_field_instances(rec2, fnum, '%', '%')
    else:
        fields2 = record_get_field_instances(rec2, fnum, ind1, ind2)
    if len(fields2)==0:
        return

    ### check if field in rec1 doesn't even exist
    if not record_has_field(rec1, fnum):
        record_add_fields(rec1, fnum, fields2)
        return

    ### compare the fields, get diffs for given indicators
    alldiffs = record_field_diff(rec1[fnum], rec2[fnum], fnum, match_subfields, ind1, ind2)

    ### check if fields are the same
    if alldiffs is None:
        return #nothing to merge

    ### find the diffing for the fields of the given indicators

    alldiffs = alldiffs[1] #keep only the list of diffs by indicators (without the 'c')

    if merging_all_indicators:
        #combine the diffs for each indicator to one list
        diff = _combine_diffs(alldiffs)
    else: #diffing for one indicator
        for diff in alldiffs:  #look for indicator pair in diff result
            if diff[0] == (ind1, ind2):
                break
        else:
            raise Exception, "Indicators not in diff result."
        diff = diff[1] #keep only the list of diffs (without the indicator tuple)

    ### proceed to merging fields in a new field list
    fields1, fields2 = rec1[fnum], rec2[fnum]
    new_fields = []
    if merge_conflicting_fields == False: #merge non-conflicting fields
        for m in diff: #for every match of fields in the diff
            if m[0] is not None: #if rec1 has a field in the diff, keep it
                new_fields.append( deepcopy(fields1[m[0]]) )
            else: #else take the field from rec2
                new_fields.append( deepcopy(fields2[m[1]]) )
    else: #merge all fields
        for m in diff: #for every match of fields in the diff
            if m[1] is not None: #if rec2 has a field, add it
                new_fields.append( deepcopy(fields2[m[1]]) )
                if m[0] is not None and fields1[m[0]][0] != fields2[m[1]][0]:
                    #if the fields are not the same then add the field of rec1
                    new_fields.append( deepcopy(fields1[m[0]]) )
            else:
                new_fields.append( deepcopy(fields1[m[0]]) )

    ### delete existing fields
    record_delete_field(rec1, fnum, ind1, ind2)
    ## find where the new_fields should be inserted in rec1 (insert_index)
    if merging_all_indicators:
        insert_index = 0
    else:
        insert_index = None
        ind_pair = (ind1, ind2)
        first_last_dict = _first_and_last_index_for_each_indicator( rec1.get(fnum, []) )
        #find the indicator pair which is just before the one which will be inserted
        indicators = first_last_dict.keys()
        indicators.sort()
        ind_pair_before = None
        for pair in indicators:
            if pair > ind_pair:
                break
            else:
                ind_pair_before = pair
        if ind_pair_before is None: #if no smaller indicator pair exists
            insert_index = 0 #insertion will take place at the beginning
        else:  #else insert after the last field index of the previous indicator pair
            insert_index = first_last_dict[ind_pair_before][1] + 1

    ### add the new (merged) fields in correct 'in_field_index' position
    record_add_fields(rec1, fnum, new_fields, insert_index)
    return

def _combine_diffs(alldiffs):
    """Takes all diffs of a field-tag which are separated by indicators and
    combine them in one list in correct index order."""
    diff = []
    for d in alldiffs:
        diff.extend( d[1] )
    return diff

def _first_and_last_index_for_each_indicator(fields):
    """return a dictionary with indicator pair tuples as keys and a pair as
    value that contains the first and the last in_field_index of the fields that
    have the specific indicators. Useful to find where to insert new fields."""
    result = {}
    for index, field in enumerate(fields):
        indicators = (field[1], field[2])
        if indicators not in result: #create first-last pair for indicator pair
            result[indicators] = [index, index]
        else: #if there is a first-last pair already, update the 'last' index
            result[indicators][1] = index
    return result

def add_field(rec1, rec2, fnum, findex1, findex2):
    """Adds the field of rec2 into rec1 in a position that depends on the
    diffing of rec1 with rec2.
    @param rec1: First record (a record dictionary structure)
    @param rec2: Second record (a record dictionary structure)
    @param fnum: a 3 characters long string indicating field tag number
    @param findex1: the rec1 field position in the group of fields it belongs
    @param findex2: the rec2 field position in the group of fields it belongs
    """
    field_to_add = rec2[fnum][findex2]
    ### if findex1 indicates an existing field in rec1, insert the field of rec2
    ### before the field of rec1
    if findex1 is not None:
        record_add_fields(rec1, fnum, [field_to_add], findex1)
        return

    ### check if field tag does not exist in record1
    if not record_has_field(rec1, fnum):
        record_add_fields(rec1, fnum, [field_to_add]) #insert at the beginning
        return

    ### if findex1 is None and the fieldtag already exists
    #get diffs for all indicators of the field.
    alldiffs = record_field_diff(rec1[fnum], rec2[fnum], fnum, match_subfields)
    alldiffs = alldiffs[1] #keep only the list of diffs by indicators (without the 'c')
    diff = _combine_diffs(alldiffs) #combine results in one list

    #find the position of the field after which the insertion should take place
    findex1 = -1
    for m in diff:
        if m[1] == findex2:
            break
        if m[0] is not None:
            findex1 = m[0]
    #finally add the field (one position after)
    record_add_fields(rec1, fnum, [field_to_add], findex1+1)

def replace_field(rec1, rec2, fnum, findex1, findex2):
    """Replaces the contents of a field of rec1 with those of rec2.
    @param rec1: First record (a record dictionary structure)
    @param rec2: Second record (a record dictionary structure)
    @param fnum: a 3 characters long string indicating field tag number
    @param findex1: the rec1 field position in the group of fields it belongs
    @param findex2: the rec2 field position in the group of fields it belongs
    """
    #if there is no field in rec1 to replace, just add a new one
    if findex1 is None:
        add_field(rec1, rec2, fnum, findex1, findex2)
        return

    #replace list of subfields from rec2 to rec1
    for i in range( len(rec1[fnum][findex1][0]) ):
        rec1[fnum][findex1][0].pop()
    rec1[fnum][findex1][0].extend(rec2[fnum][findex2][0])

def merge_field(rec1, rec2, fnum, findex1, findex2):
    """Merges the contents of a field of rec1 with those of rec2, inserting
    them in the place of the field of rec1.
    @param rec1: First record (a record dictionary structure)
    @param rec2: Second record (a record dictionary structure)
    @param fnum: a 3 characters long string indicating field tag number
    @param findex1: the rec1 field position in the group of fields it belongs
    @param findex2: the rec2 field position in the group of fields it belongs
    """
    #if there is no field in rec1 to merge to, just add a new one
    if findex1 is None:
        add_field(rec1, rec2, fnum, findex1, findex2)
        return

    field1 = rec1[fnum][findex1]
    sflist1 = field1[0]
    sflist2 = rec2[fnum][findex2][0]
    # diff the subfields
    diffs = diff_subfields(sflist1, sflist2)
    #merge subfields of field1 with those of field2
    new_sflist = []
    #for every match in the diff append the subfields of both fields
    for m in diffs:
        if m[1] is not None:
            new_sflist.append( sflist2[m[1]] ) #append the subfield
        if m[2] != 1.0 and m[0] is not None:
            new_sflist.append( sflist1[m[0]] )

    #replace list of subfields of rec1 with the new one
    for i in range( len(sflist1) ):
        sflist1.pop()
    sflist1.extend(new_sflist)


def delete_field(rec, fnum, findex):
    """Delete a specific field.
    @param rec: a record dictionary structure
    @param fnum: a 3 characters long string indicating field tag number
    @param findex: the rec field position in the group of fields it belongs
    """
    record_delete_field(rec, fnum, field_position_local=findex)

def delete_subfield(rec, fnum, findex, sfindex):
    """Delete a specific subfield.
    @param rec: a record dictionary structure
    @param fnum: a 3 characters long string indicating field tag number
    @param findex: the rec field position in the group of fields it belongs
    @param sfindex: the index position of the subfield in the field
    """
    field = rec[fnum][findex]
    subfields = field[0]
    if len(subfields) > 1:
        del subfields[sfindex]

def replace_subfield(rec1, rec2, fnum, findex1, findex2, sfindex1, sfindex2):
    """Replaces a subfield of rec1 with a subfield of rec2.
    @param rec1: First record (a record dictionary structure)
    @param rec2: Second record (a record dictionary structure)
    @param fnum: a 3 characters long string indicating field tag number
    @param findex1: the rec1 field position in the group of fields it belongs
    @param findex2: the rec2 field position in the group of fields it belongs
    @param sfindex1: the index position of the subfield in the field of rec1
    @param sfindex2: the index position of the subfield in the field of rec2
    """
    subfields1 = rec1[fnum][findex1][0]
    subfields2 = rec2[fnum][findex2][0]
    subfields1[sfindex1] = subfields2[sfindex2]

def add_subfield(rec1, rec2, fnum, findex1, findex2, sfindex1, sfindex2):
    """Adds a subfield of rec2 in a field of rec1, before or after sfindex1.
    @param rec1: First record (a record dictionary structure)
    @param rec2: Second record (a record dictionary structure)
    @param fnum: a 3 characters long string indicating field tag number
    @param findex1: the rec1 field position in the group of fields it belongs
    @param findex2: the rec2 field position in the group of fields it belongs
    @param sfindex1: the index position of the subfield in the field of rec1
    @param sfindex2: the index position of the subfield in the field of rec2
    """
    subfield_to_insert = rec2[fnum][findex2][0][sfindex2]
    #insert at the sfindex1 position
    subfields1 = rec1[fnum][findex1][0]
    subfields1[sfindex1:sfindex1] = [ subfield_to_insert ]

def copy_R2_to_R1(rec1, rec2):
    """Copies contents of R2 to R1 apart from the controlfields."""
    tmprec = deepcopy(rec1)
    for fnum in tmprec:
        if fnum[:2] != '00': #if it's not a control field delete it from rec1
            del rec1[fnum]
    for fnum in rec2:
        if fnum[:2] != '00': #if it's not a control field add it to rec2
            rec1[fnum] = rec2[fnum]
