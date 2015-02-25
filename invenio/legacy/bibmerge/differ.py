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

import jellyfish


def record_diff(rec1, rec2, compare_subfields, ind1='', ind2=''):
    """Compares two given records
    @param rec1: First record
    @param rec2: Second record

    @return: dictionary of differences. Each difference is of a form:
     field_id: None - if field is the same for both records
     field_id: ('r',) - if field field_id exists in rec1 but not in
         rec2
     field_id: ('a',) - if field field_id exists in rec2 but not in rec1
     field_id: ('c', new_value) - if field field_id exists in both
         records, but it's value has changed
     new_value describes the new value of a given field (which
         allows to reconstruct new record from the old one)"""
    # Very simple test to save computing power.
    #if rec1 == rec2:
    #    return {}

    result = {}
    for tag in rec1:
        result[tag] = record_field_diff_generic(rec1, rec2, tag, compare_subfields, ind1, ind2)

    for tag in rec2:
        if tag not in rec1:
            result[tag] = record_field_diff_generic(rec1, rec2, tag, compare_subfields, ind1, ind2)
    return result

def record_field_diff_generic(rec1, rec2, tag, compare_subfields, ind1='', ind2=''):
    if tag not in rec2:
        return ('r',)
    if tag not in rec1:
        return ('a',)
    return record_field_diff(rec1[tag], rec2[tag], tag, compare_subfields, ind1, ind2)

def record_field_diff(fields1, fields2, tag, compare_subfields, ind1='', ind2=''):
    """Compares given field in two records.
    returns a list containing at most one element
    If the fields are identical (that means have the same order, the
     same subfields), empty list is returned.
    If the field is removed in second record, [(field, 'r')] is
     returned
    If the field is added in second record, [(field, 'a')]
     is returned
    If the field is changed [(field, 'c', comparison_table)] is returned.
    The comparison table is a table containing pairs of indexes showing
    the relations between fields."""
    # Extract the fields.
    fields1 = [field for field in enumerate(fields1)
               if _has_indicators(field[1], ind1, ind2)]
    fields2 = [field for field in enumerate(fields2)
               if _has_indicators(field[1], ind1, ind2)]
    if fields1 == fields2:
        return None

    fields_comparison = {}

    idx1, idx2 = 0, 0
    len1, len2 = len(fields1), len(fields2)

    while idx1 < len1 and idx2 < len2:
        list_index1, field1 = fields1[idx1]
        list_index2, field2 = fields2[idx2]

        subfields_are_similar, value = compare_subfields(field1[0], field2[0])
        if subfields_are_similar:
            ind_pair = (field1[1], field1[2])
            fields_comparison.setdefault(ind_pair, []).append((list_index1, list_index2, value))
            idx1 += 1
            idx2 += 1
        elif _field_in_fields(field1, fields2[idx2+1:], compare_subfields) \
            is None:
            ind_pair = (field1[1], field1[2])
            fields_comparison.setdefault(ind_pair, []).append((list_index1, None, None))
            idx1 += 1
        else:
            ind_pair = (field2[1], field2[2])
            fields_comparison.setdefault(ind_pair, []).append((None, list_index2, None))
            idx2 += 1

    # Add the remaining elements.
    for index in range(idx1, len(fields1)):
        field1 = fields1[index][1]
        list_index1 = fields1[index][0]
        ind_pair = (field1[1], field1[2])
        fields_comparison.setdefault(ind_pair, []).append((list_index1,None,None))
    for index in range(idx2, len(fields2)):
        field2 = fields2[index][1]
        list_index2 = fields2[index][0]
        ind_pair = (field2[1], field2[2])
        fields_comparison.setdefault(ind_pair, []).append((None,list_index2,None))

    comparisons_list = []
    indicators = fields_comparison.keys()
    indicators.sort()
    for indicator in indicators:
        comparisons_list.append((indicator, fields_comparison[indicator]))

    return ('c', comparisons_list)

def _has_indicators(field, ind1, ind2):
    """Checks if the field has the indicators. Consider an empty
    indicator as a wildcard."""
    if not ind1 and not ind2:
        return True
    else:
        return field[1:3] == (ind1, ind2)

def _same_indicators(field1, field2):
    """Checks if fields have the same indicators."""
    return field1[1:3] == field2[1:3]

def _field_in_fields(field, fields, compare_subfields):
    """Checks if a field 'field' has an equivalent in the list of fields
    'fields'. Uses the 'compare_subfields' method to achieve this."""
    if compare_subfields is None:
        compare_subfields = lambda a, b: a == b

    for index, field2 in fields:
        if compare_subfields(field[0], field2[0])[0]:
            return index

    return None

def compare_strings(str1, str2):
    """Compares 2 strings with the Levenshtein distance and returns a normalized
    value between 0.0 and 1.0 (meaning totally different and exactly the same
    respectively."""
    if str1 == str2:
        return 1.0
    max_len = max(len(str1), len(str2))
    if max_len == 0:
        return 0.0
    distance = jellyfish.levenshtein_distance(str1, str2)
    return (max_len - distance) / float(max_len)

def compare_subfields(subfield1, subfield2):
    """Compare two subfields taking into account the subfield code and the
    subfield string value."""
    #compare subfield code
    if subfield1[0] != subfield2[0]:
        return 0.0
    #compare subfield values
    return compare_strings(subfield1[1], subfield2[1])

def diff_subfields(subfields1, subfields2):
    """Return a list of diffs for the subfields. A diff is a tuple of:
    (index-of-subfield1, index-of-subfield2, distance-value)."""
    # The result of the comparisons.
    subfields_comparison = []

    # Two indexes used to retain the position of the subfields to compare.
    idx1, idx2 = 0, 0
    len1, len2 = len(subfields1), len(subfields2)

    while idx1 < len1 and idx2 < len2:
        subfield1 = subfields1[idx1]
        for i in range(idx2, len2):
            subfield2 = subfields2[i]
            # Compare the two current subfields.
            value = compare_subfields(subfield1, subfield2)
            if value >= 0.5: #we have a match
                for j in range(idx2, i): #no match for subfields2 in between, if any
                    subfields_comparison.append((None, j, 0.0))
                subfields_comparison.append((idx1, i, value))
                idx2 = i+1
                break
        else: #no match for subfield1
            subfields_comparison.append((idx1, None, 0.0))
        idx1 += 1

    # Add the remaining elements.
    for index in range(idx1, len1):
        subfields_comparison.append((index, None, 0.0))
    for index in range(idx2, len2):
        subfields_comparison.append((None, index, 0.0))

    return subfields_comparison

def match_subfields(subfields1, subfields2):
    """False if subfields dont match, True if they do and also their diff is
    returned."""
    subfield_diffs = diff_subfields(subfields1, subfields2)
    listofscores = [x[2] for x in subfield_diffs]
    if len(listofscores)==0: #in case of a controlfield like '001', '003',...
        return (False, None)
    #length of listofscores should be normally != 0
    average_score = sum(listofscores) / len(listofscores)
    if average_score >= 0.5:
        return (True, subfield_diffs)
    else:
        return (False, None)

def Levenshtein_diffs(str1, str2):
    """Actions (insert, delete, substitute, none) needed to perform on the two
    strings to make them identical."""
    actions = []
    matrix = _Levenshtein_matrix(str1, str2)
    i, j = len(str2), len(str1)
    counter = 0
    lastaction = None
    while i!=0 and j!=0:
        lastvalue = matrix[i][j]
        values = [matrix[i-1][j-1], matrix[i][j-1], matrix[i-1][j]]
        indexofmin = _min_index(values)
        if indexofmin == 0:
            if lastvalue == values[indexofmin]:
                action = 'n'
            else:
                action = 's'
            i, j = i-1, j-1
        elif indexofmin == 1:
            action = 'i'
            j = j-1
        else:  # if indexofmin == 2
            action = 'd'
            i = i-1
        if action != lastaction:
            actions.append( (lastaction, counter) )
            counter = 0
            lastaction = action
        counter = counter + 1
    actions.append( (lastaction, counter) )
    if i>0:
        actions.append( ('d', i) )
    if j>0:
        actions.append( ('i', j) )
    actions.pop(0)
    actions.reverse()
    return actions

def _Levenshtein_matrix(str1, str2):
    len1, len2 = len(str1), len(str2)
    # two-dimensional array of distances
    dist = []
    # initial values
    for i in range( len2 + 1 ):
        dist.append( [i] )
    for j in range(1,  len1 + 1 ):
        dist[0].append( j )
    # calculation of minimum distance
    for i in range(1, len2 + 1 ):
        for j in range(1, len1 + 1 ):
            if str1[j-1] == str2[i-1]:
                cost = 0
            else:
                cost = 1
            # choose between deletion, insertion, substitution
            dist[i].append( min( dist[i-1][j] + 1, \
                                 dist[i][j-1] + 1, \
                                 dist[i-1][j-1] + cost ) )
    return dist

def _min_index(alist):
    min_i = 0 #index of item with minimum value
    for i in range(1, len(alist)):
        if alist[i] < alist[min_i]:
            min_i = i
    return min_i

