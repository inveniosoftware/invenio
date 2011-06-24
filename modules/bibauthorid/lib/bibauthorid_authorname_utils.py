# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2011 CERN.
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

'''
bibauthorid_authornames_utils
Helper for accessing the author names data structure
'''

import bibauthorid_utils
from copy import deepcopy

from bibauthorid_utils import clean_name_string
from bibauthorid_utils import split_name_parts

import bibauthorid_structs as dat
import bibauthorid_config as bconfig


def get_bibrefs_by_authornames_id(authornames_id):
    '''
    Finds actual ids of the author name as it appears in bib10x or bib70x

    @param authornames_id: id in aidAUTHORNAMES
    @return: A list of sets.
        - The first set in the list contains all ids in bib10x
        - The second set in the list contains all ids in bib70x
    @rtype: list of sets
    '''

    bibrefs = ''
    bibref_str = [row['bibrefs'] for row in dat.AUTHOR_NAMES
                  if row['id'] == authornames_id]

    if len(bibref_str) > 0:
        bibrefs = bibref_str.split(",")

    b100 = set()
    b700 = set()

    for bibref in bibrefs:
        tag, refid = bibref.split(':')
        if tag == "100":
            b100.add(int(refid))
        elif tag == "700":
            b700.add(int(refid))
        else:
            bconfig.LOGGER.error("Wrong bibref Tag...how did you do that?")

    return [b100, b700]


def name_matching(orig_name, target_name):
    """
    Checks the compatibility of the given names.

    @param orig_name: The original name String
    @type orig_name: string
    @param target_name: The target name string
    @type target_name: string

    @return: true or false in respect to the compatibility of the given names
    @rtype: boolean
    """
    orig = bibauthorid_utils.split_name_parts(orig_name)
    targ = bibauthorid_utils.split_name_parts(target_name)

    if (len(orig[1]) == 0) or (len(targ[1]) == 0):
        return True

    else:
        initials_set = set(orig[1])
        names_set = set(orig[2])
        comp_initials_set = set(targ[1])
        comp_names_set = set(targ[2])

        names_intersection = names_set.intersection(comp_names_set)
        initials_intersection = initials_set.intersection(comp_initials_set)

        if len(initials_intersection) == 0:
            if len(names_intersection) != 0:
                bconfig.LOGGER.error("length of names intersection != 0..."
                                     "This should never happen!")

        if ((len(names_intersection) == 0) and (len(comp_names_set) > 0)
            and (len(names_set) > 0)):
            return False

        if orig[1][0] == targ[1][0]:
            return True

    return False


def search_matching_names(authorname_string, match_function=name_matching,
                          consider_surname_only=True):
    """
    search for matching names give a matching function.
    @warning: searching for matching name with consider_surname_only=false
        will be painfully slow! You've been warned.

    @warning: for mental sanity purposes the surnames not ending with a comma
        are being ignored;
        if you're searching for a surname without comma or names, the comma is
        being added automatically to the end of the string.

    @param authorname_string: The author name string
    @type authorname_string: string
    @param match_function: The function to use for the name matching
    @type match_function: function descriptor
    @param consider_surname_only: Decides if only names with the same
        surname shall be considered or _all_ other names.
    @type consider_surname_only: boolean

    @return: an array containing a tuple
    @rtype: list of tuples

    @note: example:
        search_matching_names('einstein, albert')
        Out[7]: [[(962L, 'Einstein, Albert'), ['Einstein', ['A'], ['Albert']]],
                [(1128L, 'Einstein, A.'), ['Einstein', ['A'], []]]]
    """
    possible_names = []
    names = []

    if authorname_string.count(',') == 0:
        authorname_string += ','

    authorname = bibauthorid_utils.split_name_parts(authorname_string)

    if consider_surname_only:
        names = [row for row in dat.AUTHOR_NAMES
                     if row['name'].startswith(authorname[0])]
    else:
        names = [row for row in dat.AUTHOR_NAMES]

    for name in names:
        if match_function(authorname_string, name['name']):
            possible_names.append([(name['id'], name['name']),
                           bibauthorid_utils.split_name_parts(name['name'])])
    return possible_names


def get_name_id(name_string):
    """
    @return: the id associated to a given string in the authornames table.
        Returns -1 if the string is not found.
    @return: int
    """
    name_id = -1
    name = [row['id'] for row in dat.AUTHOR_NAMES
               if row['name'] == name_string]
    try:
        name_id = name[0]
    except (IndexError, ValueError):
        name_id = -1

    return name_id


def get_name_string(authorname_id):
    '''
    Get name representation for an ID in authornames table
    @return: the name string associated with a particular authorid in the
        authornames table.
        If the ID is not found returns an empty string.
    @rtype: string
    '''
    name_string = ""
    name = [row['name'] for row in dat.AUTHOR_NAMES
            if row['id'] == authorname_id]

    if len(name) > 0:
        name_string = name[0]

    return name_string


def get_db_name_string(authorname_id):
    '''
    Get name representation for an ID in authornames table
    @return: the name string associated with a particular authorid in the
        authornames table.
        If the ID is not found returns an empty string.
    @rtype: string
    '''
    name_string = ""
    name = [row['db_name'] for row in dat.AUTHOR_NAMES
            if row['id'] == authorname_id]

    if len(name) > 0:
        name_string = name[0]

    return name_string


def get_name_and_db_name_strings(authorname_id):
    '''
    Get name representation for an ID in authornames table
    @return: the name string and the db name string associated with a
        particular authornameid in the authornames table.
        If the ID is not found returns empty values for the dict keys.
    @rtype: dict
    '''
    names_dict = {"name": "",
                  "db_name": ""}
    name = [row for row in dat.AUTHOR_NAMES
            if row['id'] == authorname_id]

    if len(name) > 0:
        names_dict["name"] = name[0]['name']
        names_dict["db_name"] = name[0]['db_name']

    return names_dict


def get_name_bibrefs(authorname_id):
    """
    Finds the bibrefID from authorname_id.

    @param authorname_id: ID of the author name to look up the bibliographic
        reference for
    @type authorname_id: int

    @return: the bibrefs associated with a particular authorid in the
        authornames table. If the ID is not found, an empty string
        shall be returned.
    @rtype: string
    """
    bibref_string = ""
    bibrefs = [row['bibrefs'] for row in dat.AUTHOR_NAMES
               if row['id'] == authorname_id]
    if len(bibrefs) > 0:
        bibref_string = bibrefs[0]

    return bibref_string


def update_doclist(bibrec_id, authorname_id="", bibref=""):
    """
    Update doclist table given bibrec_id and processed author. (inserts a new
    document in the doclist table)

    @return: True if a new bibrecord has been added, false if this
        bibrecord was previously processed
    @rtype: boolean
    """
    records = [row for row in dat.DOC_LIST
               if row['bibrecid'] == bibrec_id]

    if len(records) > 0:
#            @note maybe it's better to have a comma-separated list in the
#                'authorname_id' column. That would keep the DB size
#                lower. First steps for the implementation introduced; update
#                procedure necessary. Descision might be harder.
#                Performance tests might help.
        for record in records:
            refrec = (authorname_id, bibref)

            if ((authorname_id) and
                (authorname_id not in record['authornameids']) and
                (refrec not in record['authornameid_bibrefrec'])):
                record['authornameids'] += [authorname_id]
                record['authornameid_bibrefrec'] += [refrec]
            elif ((authorname_id) and
                (authorname_id in record['authornameids']) and
                (refrec not in record['authornameid_bibrefrec'])):
                record['authornameid_bibrefrec'] += [refrec]
            else:
                bconfig.LOGGER.warn("The author has already been processed on."
                                    " the record. That's OK. Skipping entry.")
                return False
    else:
        if authorname_id:
            refrec = (authorname_id, bibref)
            dat.DOC_LIST.append({'bibrecid': bibrec_id,
                                 'authornameids': [authorname_id],
                                 'authornameid_bibrefrec': [refrec]})
        else:
            dat.DOC_LIST.append({'bibrecid': bibrec_id,
                                 'authornameids': [],
                                 'authornameid_bibrefrec': []})

    return True


def soft_compare_names(origin_name, target_name):
    '''
    Soft comparison of names, to use in search engine an similar
    Base results:
    If surname is equal in [0.6,1.0]
    If surname similar in [0.4,0.8]
    If surname differs in [0.0,0.4]
    all depending on average compatibility of names and initials.
    '''
    jaro_fctn = None

    try:
        from Levenshtein import jaro_winkler
        jaro_fctn = jaro_winkler
    except ImportError:
        jaro_fctn = jaro_winkler_str_similarity
    score = 0.0
    oname = deepcopy(origin_name)
    tname = deepcopy(target_name)
    orig_name = split_name_parts(oname.lower())
    targ_name = split_name_parts(tname.lower())
    orig_name[0] = clean_name_string(orig_name[0],
                                     replacement="",
                                     keep_whitespace=False)
    targ_name[0] = clean_name_string(targ_name[0],
                                     replacement="",
                                     keep_whitespace=False)
    if orig_name[0] == targ_name[0]:
        score += 0.6
    else:
        if ((jaro_fctn(orig_name[0].lower(), targ_name[0].lower()) < .95)
            or min(len(orig_name[0]), len(targ_name[0])) <= 4):
            score += 0.0
        else:
            score += 0.4

    if orig_name[1] and targ_name[1]:
        max_initials = max(len(orig_name[1]), len(targ_name[1]))
        matching_i = 0
        if len(orig_name[1]) >= 1 and len(targ_name[1]) >= 1:
            for i in orig_name[1]:
                if i in targ_name[1]:
                    matching_i += 1
        max_names = max(len(orig_name[2]), len(targ_name[2]))
        matching_n = 0
        if len(orig_name[2]) >= 1 and len(targ_name[2]) >= 1:
            cleaned_targ_name = [clean_name_string(i, replacement="", keep_whitespace=False) for i in targ_name[2]]
            for i in orig_name[2]:
                if clean_name_string(i, replacement="", keep_whitespace=False) in cleaned_targ_name:
                    matching_n += 1

        name_score = (matching_i + matching_n) * 0.4 / (max_names + max_initials)
        score += name_score
    return score


def compare_names(origin_name, target_name):
    """
    Compute an index of confidence that would like to indicate whether two
    names might represent the same person.The computation is based on
    similarities of name structure, in particular:
        Initials:
            We assign an high score if all the initials matches are in the
            right order, much lower if they are in the wrong order
        Names:
            We assign a lower score for mismatching names and higher score for
            fully matching names
    If there is nothing to compare we are forced to assume a high score.

    Example for splitting names:
        In : bibauthorid.split_name_parts("Ellis, John R")
        Out: ['Ellis', ['J', 'R'], ['John']]

        Ellis, R. Keith        => [ [Ellis], [R, K], [Keith] ]
        Ellis, Richard Keith   => [ [Ellis], [R, K], [Richard, Keith] ]

    Since the initials are computed whether on the real initials present in the
    name string and using the full name, if there is no initials match we are 1
    00% confident that:
        1. we have no names/initials at all, or
        2. we have completely different names; hence if there is no initial
            match we skip this step.

    @param orig_name: The first author's last name, first name(s) and initial
    @type orig_name: list of strings and lists of strings
    @param targ_name: The second author's last name, first name(s) and initial
    @type targ_name: list of strings and lists of strings

    @return: a value that describes the likelihood of the names being the same
    @rtype: float
    """

    jaro_fctn = None

    try:
        from Levenshtein import jaro_winkler
        jaro_fctn = jaro_winkler
    except ImportError:
        jaro_fctn = jaro_winkler_str_similarity

    oname = deepcopy(origin_name)
    tname = deepcopy(target_name)

    orig_name = split_name_parts(oname.lower())
    targ_name = split_name_parts(tname.lower())

    bconfig.LOGGER.info("|--> Comparing Names: \"%s\" and \"%s\"" %
                      (origin_name, target_name))

    lastname_modifier = 0.0

    if not (orig_name[0] == targ_name[0]):
        # last names are not equal before cleaning them. Assign entry penalty.
        lastname_modifier = 0.15

    orig_name[0] = clean_name_string(orig_name[0],
                                     replacement="",
                                     keep_whitespace=False)
    targ_name[0] = clean_name_string(targ_name[0],
                                     replacement="",
                                     keep_whitespace=False)

    if not (orig_name[0] == targ_name[0]):
        if ((jaro_fctn(orig_name[0].lower(), targ_name[0].lower()) < .95)
            or min(len(orig_name[0]), len(targ_name[0])) <= 4):
            bconfig.LOGGER.warn(("Unequal lastnames(%s vs. %s)."
                               + "Skipping Comparison")
                               % (orig_name[0], targ_name[0]))
            return 0.0
        else:
            bconfig.LOGGER.log(25, "Last names are not equal; "
                          + "but similar enough to continue the comparison")
            # Let it go through...however, reduce the final result a little.
            lastname_modifier = 0.24
    else:
        # last names are equal after cleaning them. Reduce penalty.
        if lastname_modifier == 0.15:
            lastname_modifier = 0.02

    if orig_name[2] and targ_name[2]:
        if len(orig_name[2]) > 1 or len(targ_name[2]) > 1:
            variation_ps = []
            oname_variations = create_name_tuples(orig_name[2])
            tname_variations = create_name_tuples(targ_name[2])

            for oname_variation in oname_variations:
                for tname_variation in tname_variations:
                    oname_var = split_name_parts("%s, %s"
                                                 % (orig_name[0],
                                                    oname_variation))
                    tname_var = split_name_parts("%s, %s"
                                                 % (targ_name[0],
                                                    tname_variation))
                    variation_ps.append(_perform_matching(oname_var,
                                                          tname_var))

            return max(variation_ps) - lastname_modifier

    return _perform_matching(orig_name, targ_name) - lastname_modifier


def _perform_matching(orig_name, targ_name):
    '''

    @param orig_name:
    @type orig_name:
    @param targ_name:
    @type targ_name:
    '''
    tname = deepcopy(targ_name)
    oname = deepcopy(orig_name)

    potential_name_matches = min(len(oname[2]), len(tname[2]))
    names_p_weight = 0.0
    initials_p_weight = _compare_initials(oname, tname)

    if initials_p_weight > 0.0:
        names_p_weight = _compare_first_names(oname, tname)

    names_w = .5
    ini_w = .5

    if (names_p_weight > 0.6) and (potential_name_matches > 0):
        names_w = .7
        ini_w = .3

    if (initials_p_weight == 1.0) and (len(oname[1]) != len(tname[1])):
        initials_p_weight -= .1

    if (names_p_weight == 1.0) and ((len(oname[2]) != len(tname[2]))
        or not len(oname[2])) and (potential_name_matches < 2):
        names_p_weight -= .1

    if (initials_p_weight == 1.0) and (names_p_weight <= 0):
        names_w = 0.
        ini_w = 0.

    res = names_w * names_p_weight + ini_w * initials_p_weight

#    print "|--> Comparing Names: %s  and  %s" % (oname, tname)
    bconfig.LOGGER.debug(("|---> iWeight (%s) * ip (%s) + nWeight " +
                        "(%s) * nP (%s) = %s") % (ini_w, initials_p_weight,
                                            names_w, names_p_weight, res))

    return (names_w * names_p_weight + ini_w * initials_p_weight)


def _compare_initials(orig_name, targ_name):
    '''
    Compares Author's initials and returns the assigned score.

    @param orig_name: The first author's last name, first name(s) and initial
    @type orig_name: list of strings and lists of strings
    @param targ_name: The second author's last name, first name(s) and initial
    @type targ_name: list of strings and lists of strings

    @return: a value describing the likelihood of the initials being the same
    @rtype: float
    '''
    # determine minimal number of initials and declare the
    # count of max. possible matches
    tname = deepcopy(targ_name)
    oname = deepcopy(orig_name)

    max_possible_matches = min(len(oname[1]), len(tname[1]))
    initial_weight_denominator = (float(1 + max_possible_matches) /
                                  2.0) * max_possible_matches
    initials_p_weight = 0.0

    if max_possible_matches > 0:
        for index, item in enumerate(oname[1]):
#            print "|---> Trying Initial: ", I
            if index < max_possible_matches:
                try:
                    targ_index = tname[1].index(item)

                    if index == targ_index:
                        initials_p_weight += (
                            float(index + 1) / initial_weight_denominator)
                    else:
                        initials_p_weight += 1. / (5 * max_possible_matches *
                                                   abs(index - targ_index))
                    tname[1][targ_index] = ''
                except (IndexError, ValueError, ZeroDivisionError):
#                    initials_p_weight = 0.1
                    break
    else:
        initials_p_weight = 0.0

    return initials_p_weight


def _compare_first_names(orig_name, targ_name):
    '''
    Compares Author's first names and returns the assigned score.

    @param orig_name: The first author's last name, first name(s) and initial
    @type orig_name: list of strings and lists of strings
    @param targ_name: The second author's last name, first name(s) and initial
    @type targ_name: list of strings and lists of strings

    @return: a value that describes the likelihood of the names being the same
    @rtype: float
    '''
    # determine minimal number of names and declare the
    # count of max. possible matches

    string_similarity = None

    try:
        from Levenshtein import jaro_winkler
        string_similarity = jaro_winkler
    except ImportError:
        string_similarity = jaro_winkler_str_similarity

    tname = deepcopy(targ_name)
    oname = deepcopy(orig_name)

    names_p_weight = 0.0
    max_possible_matches = float(min(len(oname[2]), len(tname[2])))
    name_weight_denominator = ((1.0 + max_possible_matches)
                               / 2.0 * max_possible_matches)
    equal_set = set(oname[2]).intersection(set(tname[2]))
    equal_names = [i for i in oname[2] if i in equal_set]

    if max_possible_matches < 1.:
        return 1.0

    if len(equal_names) == max_possible_matches:
        for index, item in enumerate(equal_names):
            if index <= max_possible_matches:
                try:
                    targ_index = tname[2].index(item)
                    initial_index = oname[1].index(item[0].upper())

                    if (index == targ_index) or (initial_index == targ_index):
                        names_p_weight += (float(index + 1) /
                                           float(name_weight_denominator))
                    else:
                        names_p_weight += 1. / (2 * max_possible_matches *
                                              abs(index - targ_index))
                    tname[2][targ_index] = ''
                except (IndexError, ValueError, ZeroDivisionError):
                    break

    else:
        fuzzy_matches = 0
        wrong_position_modifier = 0

#        for name1 in oname[2]:
#            for name2 in tname[2]:
#                similarity = string_similarity(name1, name2)
#                if similarity > 0.91:
#                    fuzzy_matches += 1
#                    if oname[2].index(name1) != tname[2].index(name2):
#                        wrong_position_modifier += 0.05
        for name1 in oname[2]:
            for name2 in tname[2]:
                fuzzy_matches += string_similarity(name1, name2)
                if oname[2].index(name1) != tname[2].index(name2):
                    wrong_position_modifier += 0.05

        if fuzzy_matches > 0:
            num_comparisons = len(oname[2]) * len(tname[2])
            names_p_weight = (fuzzy_matches / num_comparisons -
                              wrong_position_modifier)
        else:
            names_p_weight = -0.3

    return names_p_weight


def create_name_tuples(names):
    '''
    Find name combinations, i.e. permutations of the names in different
    positions of the name

    @param names: a list of names
    @type names: list of string

    @return: the combinations of the names given
    @rtype: list of lists of strings
    '''
    length = float(len(names))
    max_tuples = int((length / 2) * (length - 1))
    current_tuple = 1
    pos = 0
    off = 1
    variants = [" ".join(names)]

    for i in range(max_tuples):
        variant = "%s %s %s" % (' '.join(names[0:pos]),
                            ''.join(names[pos:off + 1]).capitalize(),
                            ' '.join(names[off + 1::]))
        variants.append(variant.strip())
        pos += 1
        off += 1

        if off >= length:
            pos = i * 0
            off = current_tuple + 1
            current_tuple += 1

    return variants


def jaro_str_distance(str1, str2):
    """
    The Jaro string similarity algorithm as described in
    'Jaro, M.A. (1989): "Advances in record linkage methodology as applied
    to the 1985 census of Tampa Florida'

    @param str1: The first string
    @type str1: string
    @param str2: The second string
    @type str2: string

    @return: approximate string comparison measure (between 0.0 and 1.0)
    @rtype: float
    """

    if (not str1) or (not str2):
        return 0.0
    elif str1 == str2:
        return 1.0

    jaro_marker = chr(1)

    len1 = len(str1)
    len2 = len(str2)

    halflen = max(len1, len2) / 2 + 1

    assignments1 = ''
    assignments2 = ''

    workstr1 = str1
    workstr2 = str2

    common1 = common2 = 0

    # Analyze the first string
    for i in xrange(len1):
        start = max(0, i - halflen)
        end = min(i + halflen + 1, len2)
        index = workstr2.find(str1[i], start, end)

        if index > -1:  # Found common character
            common1 += 1
            assignments1 = assignments1 + str1[i]
            workstr2 = workstr2[:index] + jaro_marker + workstr2[index + 1:]

    # Analyze the second string
    for i in xrange(len2):
        start = max(0, i - halflen)
        end = min(i + halflen + 1, len1)
        index = workstr1.find(str2[i], start, end)

        if (index > -1):  # Found common character
            common2 += 1
            assignments2 = assignments2 + str2[i]
            workstr1 = workstr1[:index] + jaro_marker + workstr1[index + 1:]

        common = float(common1 + common2) / 2.0

    if (common == 0):
        return 0.0

    transpositions = 0

    for i in xrange(len(assignments1)):
        if (assignments1[i] != assignments2[i]):
            transpositions += 1

    transpositions /= 2.0

    common = float(common)
    len1 = float(len1)
    len2 = float(len2)
    jaro_constant = 1.0 / 3.0
    jaro_transpositions = (common1 - transpositions) / common1
    jaro_common_to_len_ratio = common1 / len1 + common1 / len2

    dist = jaro_constant * (jaro_common_to_len_ratio + jaro_transpositions)

    return dist


def _winkler_modifier(str1, str2, in_weight):
    """
    Applies the winkler modifier to a score obtained by the Jaro string
    similarity measure. This is described in Winkler, W.E. (1999) "The state
    of record linkage and current research problems".

    If the first characters of the two strings (up to first 4) are identical,
    the similarity weight will be increased.

    @param str1: The first string
    @type str1: string
    @param str2: The second string
    @type str2: string
    @param in_weight: Similarity score obtained by the Jaro algorithm
    @type in_weight: float

    @return: approximate string comparison measure (between 0.0 and 1.0)
    @rtype: float
    """
    if (not str1) or (not str2):
        return 0.0
    elif str1 == str2:
        return 1.0

    # Compute how many characters are common at beginning
    minlen = min(len(str1), len(str2))
    common_chars_num = 0

    for common_chars_num in xrange(1, minlen + 1):
        if str1[:common_chars_num] != str2[:common_chars_num]:
            break

    common_chars_num -= 1

    if (common_chars_num > 4):
        common_chars_num = 4

    winkler_weight = in_weight + common_chars_num * 0.1 * (1.0 - in_weight)

    final_result = 0.0

    if winkler_weight >= 0.0 and winkler_weight <= 1.0:
        final_result = winkler_weight
    elif winkler_weight > 1.0:
        final_result = 1.0

    return final_result


def jaro_winkler_str_similarity(str1, str2):
    """
    For backwards compatibility, call Jaro followed by Winkler modification.

    @param str1: The first string
    @type str1: string
    @param str2: The second string
    @type str2: string

    @return: approximate string comparison measure (between 0.0 and 1.0)
    @rtype: float
    """
    jaro_weight = jaro_str_distance(str1, str2)

    return _winkler_modifier(str1, str2, jaro_weight)


def names_are_equal_composites(name1, name2):
    '''
    Checks if names are equal composites; e.g. "guangsheng" vs. "guang sheng"

    @param name1: Name string of the first name (w/ last name)
    @type name1: string
    @param name2: Name string of the second name (w/ last name)
    @type name2: string

    @return: Are the names equal composites?
    @rtype: boolean
    '''
    if not isinstance(name1, list):
        name1 = split_name_parts(name1)

    if not isinstance(name2, list):
        name2 = split_name_parts(name2)

    is_equal_composite = False
    oname_variations = create_name_tuples(name1[2])
    tname_variations = create_name_tuples(name2[2])

    for oname_variation in oname_variations:
        for tname_variation in tname_variations:
            oname = clean_name_string(oname_variation.lower(), "", False, True)
            tname = clean_name_string(tname_variation.lower(), "", False, True)

            if oname == tname:
                is_equal_composite = True
                break

    return is_equal_composite


def names_are_equal_gender(name1, name2, gendernames):
    '''
    Checks on gender equality of two names baes on a word list

    @param name1: Name string of the first name (w/ last name)
    @type name1: string
    @param name2: Name string of the second name (w/ last name)
    @type name2: string
    @param gendernames: dictionary of male/female names
    @type gendernames: dict

    @return: Are names gender-equal?
    @rtype: boolean
    '''
    if not isinstance(name1, list):
        name1 = split_name_parts(name1)

    if not isinstance(name2, list):
        name2 = split_name_parts(name2)

    print_debug = False
    names_are_equal_gender_b = True
    ogender = None
    tgender = None
    oname = name1[2][0].lower()
    tname = name2[2][0].lower()
    oname = clean_name_string(oname, "", False, True)
    tname = clean_name_string(tname, "", False, True)

    if oname in gendernames['boys']:
        ogender = 'Male'
    elif oname in gendernames['girls']:
        ogender = 'Female'

    if tname in gendernames['boys']:
        tgender = 'Male'
    elif tname in gendernames['girls']:
        tgender = 'Female'

    if print_debug:
        print '     Gender check: ', oname, ' is a ', ogender
        print '     Gender check: ', tname, ' is a ', tgender

    if ogender and tgender:
        if ogender != tgender:
            if print_debug:
                print '    Gender differs, force split!'

            names_are_equal_gender_b = False

    return names_are_equal_gender_b


def names_are_synonymous(name1, name2, name_variations):
    '''
    Checks if two names are synonymous; e.g. "Robert" vs. "Bob"

    @param name1: Name string of the first name (w/ last name)
    @type name1: string
    @param name2: Name string of the second name (w/ last name)
    @type name2: string
    @param name_variations: name variations list
    @type name_variations: list of lists

    @return: are names synonymous
    @rtype: boolean
    '''
    if not isinstance(name1, list):
        name1 = split_name_parts(name1)

    if not isinstance(name2, list):
        name2 = split_name_parts(name2)

    print_debug = False
    names_are_synonymous_b = False
    max_matches = min(len(name1[2]), len(name2[2]))
    matches = []

    for i in xrange(max_matches):
        matches.append(False)

    for nvar in name_variations:
        for i in xrange(max_matches):
            oname = name1[2][i].lower()
            tname = name2[2][i].lower()
            oname = clean_name_string(oname, "", False, True)
            tname = clean_name_string(tname, "", False, True)

            if oname in nvar and tname in nvar:
                if print_debug:
                    print '      ', oname, ' and ', tname, ' are synonyms! Not splitting!'

                matches[i] = True

        if sum(matches) == max_matches:
            names_are_synonymous_b = True
            break

    return names_are_synonymous_b


def names_are_substrings(name1, name2):
    '''
    Checks if two names are substrings of each other; e.g. "Christoph" vs. "Ch"
    Only checks for the beginning of the names. 

    @param name1: Name string of the first name (w/ last name)
    @type name1: string
    @param name2: Name string of the second name (w/ last name)
    @type name2: string

    @return: are names synonymous
    @rtype: boolean
    '''
    if not isinstance(name1, list):
        name1 = split_name_parts(name1)

    if not isinstance(name2, list):
        name2 = split_name_parts(name2)

    onames = name1[2]
    tnames = name2[2]
#    oname = "".join(onames).lower()
#    tname = "".join(tnames).lower()
    oname = clean_name_string("".join(onames).lower(), "", False, True)
    tname = clean_name_string("".join(tnames).lower(), "", False, True)
    names_are_substrings_b = False

    if (oname.startswith(tname)
        or tname.startswith(oname)):
        names_are_substrings_b = True

    return names_are_substrings_b


def names_minimum_levenshtein_distance(name1, name2):
    '''
    Determines the minimum distance D between two names.
    Comparison is base on the minimum number of first names.
    Examples:
    D("guang", "guang sheng") = 0
    D("guang", "guangsheng") = 5
    D("guang sheng", "guangsheng") = 5
    D("guang sheng", "guang shing") = 1
    D("guang ming", "guang fin") = 2

    @precondition: Names have been checked for composition equality.
    @param name1: Name string of the first name (w/ last name)
    @type name1: string
    @param name2: Name string of the second name (w/ last name)
    @type name2: string

    @return: the minimum Levenshtein distance between two names
    @rtype: int
    '''
    try:
        from Levenshtein import distance
    except ImportError:
        bconfig.LOGGER.exception("Levenshtein Module not available!")
        return - 1

    if not isinstance(name1, list):
        name1 = split_name_parts(name1)

    if not isinstance(name2, list):
        name2 = split_name_parts(name2)

    onames = name1[2]
    tnames = name2[2]
#    min_names_count = min(len(onames), len(tnames))
#
#    if min_names_count <= 0:
#        return -1
#
#    oname = "".join(onames[:min_names_count]).lower()
#    tname = "".join(tnames[:min_names_count]).lower()
    oname = clean_name_string("".join(onames).lower(), "", False, True)
    tname = clean_name_string("".join(tnames).lower(), "", False, True)

    return distance(oname, tname)
