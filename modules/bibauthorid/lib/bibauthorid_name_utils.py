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
bibauthorid_name_utils
    Bibauthorid utilities used by many parts of the framework
'''

import re
import bibauthorid_config as bconfig
from bibauthorid_string_utils import string_partition
from copy import deepcopy

try:
    from invenio.config import CFG_ETCDIR
    NO_CFG_ETCDIR = False
except ImportError:
    NO_CFG_ETCDIR = True

try:
    from editdist import distance
except ImportError:
    try:
        from Levenshtein import distance
    except ImportError:
        bconfig.LOGGER.exception("Levenshtein Module not available!")
        if bconfig.AUTHORNAMES_UTILS_DEBUG:
            print "Levenshtein Module not available!"
        def distance(s1, s2):
            d = {}
            lenstr1 = len(s1)
            lenstr2 = len(s2)
            for i in xrange(-1, lenstr1 + 1):
                d[(i, -1)] = i + 1
            for j in xrange(-1, lenstr2 + 1):
                d[(-1, j)] = j + 1

            for i in xrange(0, lenstr1):
                for j in xrange(0, lenstr2):
                    if s1[i] == s2[j]:
                        cost = 0
                    else:
                        cost = 1
                    d[(i, j)] = min(
                                   d[(i - 1, j)] + 1, # deletion
                                   d[(i, j - 1)] + 1, # insertion
                                   d[(i - 1, j - 1)] + cost, # substitution
                                  )
                    if i > 1 and j > 1 and s1[i] == s2[j - 1] and s1[i - 1] == s2[j]:
                        d[(i, j)] = min (d[(i, j)], d[i - 2, j - 2] + cost) # transposition
            return d[lenstr1 - 1, lenstr2 - 1]


#Gender names and names variation files are loaded updon module import to increase performances

def split_name_parts(name_string, delete_name_additions=True,
                     override_surname_sep='', return_all_lower=False):
    '''
    Splits name_string in three arrays of strings :
        surname, initials (without trailing dot), names
    RETURNS an array containing a string and two arrays of strings.
    delete_name_additions defines if extensions
        e.g. Jr., (Ed.) or (spokesperson)
        will be ignored

    @param name_string: the name to be spli
    @type name: string
    @param delete_name_additions: determines whether to delete name additions
    @type delete_name_additions: boolean
    @param override_surname_sep: Define alternative surname separator
    @type override_surname_sep: string
    @param reverse_name_surname: if true names come first

    @return: list of [surname string, initials list, names list]
        e.g. split_name_parts("Ellis, John R.")
        --> ['Ellis', ['J', 'R'], ['John'], [0]]
        --> ['Ellis', ['K', 'J', 'R'], ['John', 'Rob'], [1,2]]
    @rtype: list of lists
    '''
    if not override_surname_sep:
        surname_separators = bconfig.SURNAMES_SEPARATOR_CHARACTER_LIST
    else:
        surname_separators = ','

    name_separators = bconfig.NAMES_SEPARATOR_CHARACTER_LIST

    if name_separators == "-1":
        name_separators = ',;.=\-\(\)'

    if delete_name_additions:
        name_additions = re.findall('\([.]*[^\)]*\)', name_string)
        for name_addition in name_additions:
            name_string = name_string.replace(name_addition, '')

    surname = ""
    rest_of_name = ""
    found_sep = ''
    name_string = name_string.strip()

    for sep in surname_separators:
        if name_string.count(sep) >= 1:
            found_sep = sep
            surname, rest_of_name = string_partition(name_string, sep)[0::2]
            surname = surname.strip().capitalize()
            break

    if not found_sep:
        if name_string.count(" ") > 0:
            rest_of_name, surname = string_partition(name_string, ' ', direc='r')[0::2]
            surname = surname.strip().capitalize()
        else:
            return [name_string.strip().capitalize(), [], [], []]

    if rest_of_name.count(","):
        rest_of_name = string_partition(rest_of_name, ",")[0]

    substitution_regexp = re.compile('[%s]' % (name_separators))
    initials_names_list = substitution_regexp.sub(' ', rest_of_name).split()
    names = []
    initials = []
    positions = []
    pos_counter = 0
    for i in initials_names_list:
        if len(i) == 1:
            initials.append(i.capitalize())
            pos_counter += 1
        else:
            names.append(i.strip().capitalize())
            initials.append(i[0].capitalize())
            positions.append(pos_counter)
            pos_counter += 1

    retval = [surname, initials, names, positions]

    if return_all_lower:
        retval = [surname.lower(), [i.lower() for i in initials], [n.lower() for n in names], positions]

    return retval

def create_canonical_name(name):
    canonical_name = create_unified_name(name, reverse=True)
    artifact_removal = re.compile("[^a-zA-Z0-9]")
    whitespace_removal = re.compile("[ ]{1,10}")
    canonical_name = artifact_removal.sub(" ", canonical_name)
    canonical_name = whitespace_removal.sub(" ", canonical_name)
    canonical_name = canonical_name.strip().replace(" ", ".")
    return canonical_name


def create_normalized_name(splitted_name):
    '''
    Creates a normalized name from a given name array. A normalized name
    looks like "Lastname, Firstnames and Initials"

    @param splitted_name: name array from split_name_parts
    @type splitted_name: list in form [string, list, list]

    @return: normalized name
    @rtype: string
    '''
    name = splitted_name[0] + ','

    if not splitted_name[1] and not splitted_name[2]:
        return name

    for i in range(len(splitted_name[1])):
        try:
            fname = splitted_name[2][splitted_name[3].index(i)]
            name = name + ' ' + fname
        except (IndexError, ValueError):
            name = name + ' ' + splitted_name[1][i] + '.'
    return name


def create_unified_name(name, reverse=False):
    '''
    Creates unified name. E.g. Ellis, John Richard T. (Jr.)
    will become Ellis, J. R. T.

    @param name: The name to be unified
    @type name: string

    @param reverse: if true, names come first

    @return: The unified name
    @rtype: string

    '''
    split_name = split_name_parts(name)

    if reverse:
        unified_name = ''
        for i in split_name[1]:
            unified_name += "%s. " % (i)
        unified_name += "%s" % (split_name[0])
    else:
        unified_name = "%s, " % (split_name[0])
        for i in split_name[1]:
            unified_name += "%s. " % (i)

    if unified_name.count("ollabo"):
        unified_name = unified_name.replace("ollaborations", "ollaboration")
        unified_name = unified_name.replace("The ", "")
        unified_name = unified_name.replace("the ", "")
        unified_name = unified_name.replace("For ", "")
        unified_name = unified_name.replace("for ", "")


    return unified_name


def clean_name_string(namestring, replacement=" ", keep_whitespace=True,
                      trim_whitespaces=False):
    '''
    remove specific artifacts from the names in order to be able to
    compare them. E.g. 't Hooft, G. and t'Hooft, G.

    @param namestring: the string to be cleaned
    @type namestring: string
    '''
#    artifact_removal = re.compile("['`\-\[\]\_\"]")
    artifact_removal = None

    if trim_whitespaces:
        namestring.strip()

    if keep_whitespace:
        artifact_removal = re.compile("[^a-zA-Z0-9,.\s]")
    else:
        artifact_removal = re.compile("[^a-zA-Z0-9,.]")

    whitespace_removal = re.compile("[\s]{2,100}")
    tmp = artifact_removal.sub(replacement, namestring)

#    print namestring, "->", whitespace_removal.sub(" ", tmp).strip()

    return whitespace_removal.sub(" ", tmp).strip()


def soft_compare_names(origin_name, target_name):
    '''
    Soft comparison of names, to use in search engine an similar
    Base results:
    If surname is equal in [0.6,1.0]
    If surname similar in [0.4,0.8]
    If surname differs in [0.0,0.4]
    all depending on average compatibility of names and initials.
    '''
    jaro_fctn = distance

#    try:
#        from Levenshtein import jaro_winkler
#        jaro_fctn = jaro_winkler
#    except ImportError:
#        jaro_fctn = jaro_winkler_str_similarity

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

#def jaro_str_distance(str1, str2):
#    """
#    The Jaro string similarity algorithm as described in
#    'Jaro, M.A. (1989): "Advances in record linkage methodology as applied
#    to the 1985 census of Tampa Florida'
#
#    @param str1: The first string
#    @type str1: string
#    @param str2: The second string
#    @type str2: string
#
#    @return: approximate string comparison measure (between 0.0 and 1.0)
#    @rtype: float
#    """
#
#    if (not str1) or (not str2):
#        return 0.0
#    elif str1 == str2:
#        return 1.0
#
#    jaro_marker = chr(1)
#
#    len1 = len(str1)
#    len2 = len(str2)
#
#    halflen = max(len1, len2) / 2 + 1
#
#    assignments1 = ''
#    assignments2 = ''
#
#    workstr1 = str1
#    workstr2 = str2
#
#    common1 = common2 = 0
#
#    # Analyze the first string
#    for i in xrange(len1):
#        start = max(0, i - halflen)
#        end = min(i + halflen + 1, len2)
#        index = workstr2.find(str1[i], start, end)
#
#        if index > -1:  # Found common character
#            common1 += 1
#            assignments1 = assignments1 + str1[i]
#            workstr2 = workstr2[:index] + jaro_marker + workstr2[index + 1:]
#
#    # Analyze the second string
#    for i in xrange(len2):
#        start = max(0, i - halflen)
#        end = min(i + halflen + 1, len1)
#        index = workstr1.find(str2[i], start, end)
#
#        if (index > -1):  # Found common character
#            common2 += 1
#            assignments2 = assignments2 + str2[i]
#            workstr1 = workstr1[:index] + jaro_marker + workstr1[index + 1:]
#
#        common = float(common1 + common2) / 2.0
#
#    if (common == 0):
#        return 0.0
#
#    transpositions = 0
#
#    for i in xrange(len(assignments1)):
#        if (assignments1[i] != assignments2[i]):
#            transpositions += 1
#
#    transpositions /= 2.0
#
#    common = float(common)
#    len1 = float(len1)
#    len2 = float(len2)
#    jaro_constant = 1.0 / 3.0
#    jaro_transpositions = (common1 - transpositions) / common1
#    jaro_common_to_len_ratio = common1 / len1 + common1 / len2
#
#    dist = jaro_constant * (jaro_common_to_len_ratio + jaro_transpositions)
#
#    return dist
#
#
#def _winkler_modifier(str1, str2, in_weight):
#    """
#    Applies the winkler modifier to a score obtained by the Jaro string
#    similarity measure. This is described in Winkler, W.E. (1999) "The state
#    of record linkage and current research problems".
#
#    If the first characters of the two strings (up to first 4) are identical,
#    the similarity weight will be increased.
#
#    @param str1: The first string
#    @type str1: string
#    @param str2: The second string
#    @type str2: string
#    @param in_weight: Similarity score obtained by the Jaro algorithm
#    @type in_weight: float
#
#    @return: approximate string comparison measure (between 0.0 and 1.0)
#    @rtype: float
#    """
#    if (not str1) or (not str2):
#        return 0.0
#    elif str1 == str2:
#        return 1.0
#
#    # Compute how many characters are common at beginning
#    minlen = min(len(str1), len(str2))
#    common_chars_num = 0
#
#    for common_chars_num in xrange(1, minlen + 1):
#        if str1[:common_chars_num] != str2[:common_chars_num]:
#            break
#
#    common_chars_num -= 1
#
#    if (common_chars_num > 4):
#        common_chars_num = 4
#
#    winkler_weight = in_weight + common_chars_num * 0.1 * (1.0 - in_weight)
#
#    final_result = 0.0
#
#    if winkler_weight >= 0.0 and winkler_weight <= 1.0:
#        final_result = winkler_weight
#    elif winkler_weight > 1.0:
#        final_result = 1.0
#
#    return final_result
#
#
#def jaro_winkler_str_similarity(str1, str2):
#    """
#    For backwards compatibility, call Jaro followed by Winkler modification.
#
#    @param str1: The first string
#    @type str1: string
#    @param str2: The second string
#    @type str2: string
#
#    @return: approximate string comparison measure (between 0.0 and 1.0)
#    @rtype: float
#    """
#    jaro_weight = jaro_str_distance(str1, str2)
#
#    return _winkler_modifier(str1, str2, jaro_weight)


#def _perform_matching(orig_name, targ_name):
#    '''
#
#    @param orig_name:
#    @type orig_name:
#    @param targ_name:
#    @type targ_name:
#    '''
#    tname = deepcopy(targ_name)
#    oname = deepcopy(orig_name)
#
#    potential_name_matches = min(len(oname[2]), len(tname[2]))
#    names_p_weight = 0.0
#    initials_p_weight = _compare_initials(oname, tname)
#
#    if initials_p_weight > 0.0:
#        names_p_weight = _compare_first_names(oname, tname)
#
#    names_w = .5
#    ini_w = .5
#
#    if (names_p_weight > 0.6) and (potential_name_matches > 0):
#        names_w = .7
#        ini_w = .3
#
#    if (initials_p_weight == 1.0) and (len(oname[1]) != len(tname[1])):
#        initials_p_weight -= .1
#
#    if (names_p_weight == 1.0) and ((len(oname[2]) != len(tname[2]))
#        or not len(oname[2])) and (potential_name_matches < 2):
#        names_p_weight -= .1
#
#    if (initials_p_weight == 1.0) and (names_p_weight <= 0):
#        names_w = 0.
#        ini_w = 0.
#
#    res = names_w * names_p_weight + ini_w * initials_p_weight
#
##    print "|--> Comparing Names: %s  and  %s" % (oname, tname)
#    bconfig.LOGGER.debug(("|---> iWeight (%s) * ip (%s) + nWeight " +
#                        "(%s) * nP (%s) = %s") % (ini_w, initials_p_weight,
#                                            names_w, names_p_weight, res))
#
#    return (names_w * names_p_weight + ini_w * initials_p_weight)


#def _compare_initials(orig_name, targ_name):
#    '''
#    Compares Author's initials and returns the assigned score.
#
#    @param orig_name: The first author's last name, first name(s) and initial
#    @type orig_name: list of strings and lists of strings
#    @param targ_name: The second author's last name, first name(s) and initial
#    @type targ_name: list of strings and lists of strings
#
#    @return: a value describing the likelihood of the initials being the same
#    @rtype: float
#    '''
#    # determine minimal number of initials and declare the
#    # count of max. possible matches
#    tname = deepcopy(targ_name)
#    oname = deepcopy(orig_name)
#
#    max_possible_matches = min(len(oname[1]), len(tname[1]))
#    initial_weight_denominator = (float(1 + max_possible_matches) /
#                                  2.0) * max_possible_matches
#    initials_p_weight = 0.0
#
#    if max_possible_matches > 0:
#        for index, item in enumerate(oname[1]):
##            print "|---> Trying Initial: ", I
#            if index < max_possible_matches:
#                try:
#                    targ_index = tname[1].index(item)
#
#                    if index == targ_index:
#                        initials_p_weight += (
#                            float(index + 1) / initial_weight_denominator)
#                    else:
#                        initials_p_weight += 1. / (5 * max_possible_matches *
#                                                   abs(index - targ_index))
#                    tname[1][targ_index] = ''
#                except (IndexError, ValueError, ZeroDivisionError):
##                    initials_p_weight = 0.1
#                    break
#    else:
#        initials_p_weight = 0.0
#
#    return initials_p_weight


#def _compare_first_names(orig_name, targ_name):
#    '''
#    Compares Author's first names and returns the assigned score.
#
#    @param orig_name: The first author's last name, first name(s) and initial
#    @type orig_name: list of strings and lists of strings
#    @param targ_name: The second author's last name, first name(s) and initial
#    @type targ_name: list of strings and lists of strings
#
#    @return: a value that describes the likelihood of the names being the same
#    @rtype: float
#    '''
#    # determine minimal number of names and declare the
#    # count of max. possible matches
#
#    string_similarity = None
#
#    try:
#        from Levenshtein import jaro_winkler
#        string_similarity = jaro_winkler
#    except ImportError:
#        string_similarity = jaro_winkler_str_similarity
#
#    tname = deepcopy(targ_name)
#    oname = deepcopy(orig_name)
#
#    names_p_weight = 0.0
#    max_possible_matches = float(min(len(oname[2]), len(tname[2])))
#    name_weight_denominator = ((1.0 + max_possible_matches)
#                               / 2.0 * max_possible_matches)
#    equal_set = set(oname[2]).intersection(set(tname[2]))
#    equal_names = [i for i in oname[2] if i in equal_set]
#
#    if max_possible_matches < 1.:
#        return 1.0
#
#    if len(equal_names) == max_possible_matches:
#        for index, item in enumerate(equal_names):
#            if index <= max_possible_matches:
#                try:
#                    targ_index = tname[2].index(item)
#                    initial_index = oname[1].index(item[0].upper())
#
#                    if (index == targ_index) or (initial_index == targ_index):
#                        names_p_weight += (float(index + 1) /
#                                           float(name_weight_denominator))
#                    else:
#                        names_p_weight += 1. / (2 * max_possible_matches *
#                                              abs(index - targ_index))
#                    tname[2][targ_index] = ''
#                except (IndexError, ValueError, ZeroDivisionError):
#                    break
#
#    else:
#        fuzzy_matches = 0
#        wrong_position_modifier = 0
#
##        for name1 in oname[2]:
##            for name2 in tname[2]:
##                similarity = string_similarity(name1, name2)
##                if similarity > 0.91:
##                    fuzzy_matches += 1
##                    if oname[2].index(name1) != tname[2].index(name2):
##                        wrong_position_modifier += 0.05
#        for name1 in oname[2]:
#            for name2 in tname[2]:
#                fuzzy_matches += string_similarity(name1, name2)
#                if oname[2].index(name1) != tname[2].index(name2):
#                    wrong_position_modifier += 0.05
#
#        if fuzzy_matches > 0:
#            num_comparisons = len(oname[2]) * len(tname[2])
#            names_p_weight = (fuzzy_matches / num_comparisons -
#                              wrong_position_modifier)
#        else:
#            names_p_weight = -0.3
#
#    return names_p_weight


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


def full_names_are_equal_composites(name1, name2):
    '''
    Checks if names are equal composites; e.g. "guangsheng" vs. "guang sheng"

    @param name1: Full Name string of the first name (w/ last name)
    @type name1: string
    @param name2: Full Name string of the second name (w/ last name)
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
    Checks if names have the same gender
    @param gendernames: dictionary male/female names
    '''
    g1 = [name1 in gendernames['boys'], name1 in gendernames['girls']]
    g2 = [name2 in gendernames['boys'], name2 in gendernames['girls']]

    if (g1[0] == g2[0] == True) and (g1[1] == False or g2[1] == False):
        return True
    if (g1[1] == g2[1] == True) and (g1[0] == False or g2[0] == False):
        return True
    return False

def full_names_are_equal_gender(name1, name2, gendernames):
    '''
    Checks on gender equality of two first names baes on a word list

    @param name1: Full Name string of the first name (w/ last name)
    @type name1: string
    @param name2: Full Name string of the second name (w/ last name)
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

    names_are_equal_gender_b = True
    ogender = None
    tgender = None
#    oname = name1[2][0].lower()
#    tname = name2[2][0].lower()
#    oname = clean_name_string(oname, "", False, True)
#    tname = clean_name_string(tname, "", False, True)

    onames = [clean_name_string(n.lower(), "", False, True) for n in name1[2]]
    tnames = [clean_name_string(n.lower(), "", False, True) for n in name2[2]]

    for oname in onames:
        if oname in gendernames['boys']:
            if ogender != 'Conflict':
                if ogender != 'Female':
                    ogender = 'Male'
                else:
                    ogender = 'Conflict'
        elif oname in gendernames['girls']:
            if ogender != 'Conflict':
                if ogender != 'Male':
                    ogender = 'Female'
                else:
                    ogender = 'Conflict'

    for tname in tnames:
        if tname in gendernames['boys']:
            if tgender != 'Conflict':
                if tgender != 'Female':
                    tgender = 'Male'
                else:
                    tgender = 'Conflict'
        elif tname in gendernames['girls']:
            if tgender != 'Conflict':
                if tgender != 'Male':
                    tgender = 'Female'
                else:
                    tgender = 'Conflict'


    if ogender and tgender:
        if ogender != tgender or ogender == 'Conflict' or tgender == 'Conflict':

            names_are_equal_gender_b = False

    return names_are_equal_gender_b


def names_are_synonymous(name1, name2, name_variations):
    '''
    Checks if names are synonims
    @param name_variations: name variations list
    @type name_variations: list of lists
    '''

    a = [name1 in nvar and name2 in nvar for nvar in name_variations]
    if True in a:
        return True
    return False

def full_names_are_synonymous(name1, name2, name_variations):
    '''
    Checks if two names are synonymous; e.g. "Robert" vs. "Bob"

    @param name1: Full Name string of the first name (w/ last name)
    @type name1: string
    @param name2: Full Name string of the second name (w/ last name)
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

            if (oname in nvar and tname in nvar) or oname == tname:
                if print_debug:
                    print '      ', oname, ' and ', tname, ' are synonyms!'

                matches[i] = True

        if sum(matches) == max_matches:
            names_are_synonymous_b = True
            break

    return names_are_synonymous_b


def names_are_substrings(name1, name2):
    '''
    Checks if the names are subtrings of each other, left to right
    @return: bool
    '''
    return name1.startswith(name2) or name2.startswith(name1)

def full_names_are_substrings(name1, name2):
    '''
    Checks if two names are substrings of each other; e.g. "Christoph" vs. "Ch"
    Only checks for the beginning of the names.

    @param name1: Full Name string of the first name (w/ last name)
    @type name1: string
    @param name2: Full Name string of the second name (w/ last name)
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

    names_are_substrings_b = False
    for o in onames:
        oname = clean_name_string(o.lower(), "", False, True)
        for t in tnames:
            tname = clean_name_string(t.lower(), "", False, True)
            if (oname.startswith(tname)
                or tname.startswith(oname)):
                names_are_substrings_b = True

    return names_are_substrings_b

def _load_gender_firstnames_dict(files=''):
    if not NO_CFG_ETCDIR and not files:
        files = {'boy':  CFG_ETCDIR + '/bibauthorid/name_authority_files/male_firstnames.txt',
                 'girl': CFG_ETCDIR + '/bibauthorid/name_authority_files/female_firstnames.txt'}
    elif NO_CFG_ETCDIR and not files:
        files = {'boy':  '../etc/name_authority_files/male_firstnames.txt',
                 'girl': '../etc/name_authority_files/female_firstnames.txt'}

    boyf = open(files['boy'], 'r')
    boyn = set([x.strip().lower() for x in boyf.readlines()])
    boyf.close()
    girlf = open(files['girl'], 'r')
    girln = set([x.strip().lower() for x in girlf.readlines()])
    girlf.close()
    return {'boys':list(boyn - girln), 'girls':list(girln - boyn)}


def _load_firstname_variations(filename=''):
    #will load an array of arrays: [['rick','richard','dick'],['john','jhonny']]
    if not NO_CFG_ETCDIR and not filename:
        filename = CFG_ETCDIR + '/bibauthorid/name_authority_files/name_variants.txt'
    elif NO_CFG_ETCDIR and not filename:
        filename = '../etc/name_authority_files/name_variants.txt'

    retval = []
    r = re.compile("\n")
    fp = open(filename)

    for l in fp.readlines():
        lr = r.sub("", l)
        retval.append([clean_name_string(name.lower(), "", False, True)
                       for name in lr.split(";") if name])

    fp.close()

    return retval

def compare_names(origin_name, target_name, initials_penalty=False):
    '''
    Compare two names.
    '''
    AUTHORNAMES_UTILS_DEBUG = bconfig.AUTHORNAMES_UTILS_DEBUG
    MAX_ALLOWED_SURNAME_DISTANCE = 2
    if AUTHORNAMES_UTILS_DEBUG:
        print "\nComparing: " , origin_name, ' ', target_name
    gendernames = GLOBAL_gendernames
    name_variations = GLOBAL_name_variations
    no = split_name_parts(origin_name, True, "", True)
    nt = split_name_parts(target_name, True, "", True)

    if AUTHORNAMES_UTILS_DEBUG:
        print "|- splitted no: ", no
        print "|- splitted nt: ", nt

    score = 0.0

    surname_dist = distance(no[0], nt[0])
    if AUTHORNAMES_UTILS_DEBUG:
        print "|- surname distance: ", surname_dist

    if surname_dist > 0:
        artifact_removal = re.compile("[^a-zA-Z0-9]")
        fn1 = artifact_removal.sub("", no[0])
        fn2 = artifact_removal.sub("", nt[0])

        if fn1 == fn2:
            score = 1.0
        else:
            score = max(0.0, 0.5 - (float(surname_dist) / float(MAX_ALLOWED_SURNAME_DISTANCE)))
    else:
        score = 1.0
    if AUTHORNAMES_UTILS_DEBUG:
        print '||- surname score: ', score

    initials_only = ((min(len(no[2]), len(nt[2]))) == 0)
    only_initials_available = False
    if len(no[2]) == len(nt[2]) and initials_only:
        only_initials_available = True

    if AUTHORNAMES_UTILS_DEBUG:
        print '|- initials only: ', initials_only
        print '|- only initials available: ', only_initials_available

    names_are_equal_composites = False
    if not initials_only:
        names_are_equal_composites = full_names_are_equal_composites(origin_name, target_name)
    if AUTHORNAMES_UTILS_DEBUG:
        print "|- equal composites: ", names_are_equal_composites

    max_n_initials = max(len(no[1]), len(nt[1]))
    initials_intersection = set(no[1]).intersection(set(nt[1]))
    n_initials_intersection = len(initials_intersection)
    initials_union = set(no[1]).union(set(nt[1]))
    n_initials_union = len(initials_union)


    initials_distance = distance("".join(no[1]), "".join(nt[1]))
    if n_initials_union > 0:
        initials_c = float(n_initials_intersection) / float(n_initials_union)
    else:
        initials_c = 1

    if len(no[1]) > len(nt[1]):
        alo = no[1]
        alt = nt[1]
    else:
        alo = nt[1]
        alt = no[1]
    lo = len(alo)
    lt = len(alt)
    if max_n_initials > 0:
        initials_screwup = sum([i + 1 for i, k in enumerate(reversed(alo))
                            if lo - 1 - i < lt and k != alt[lo - 1 - i] ]) / \
                            float(float(max_n_initials * (max_n_initials + 1)) / 2)
        initials_distance = initials_distance / max_n_initials
    else:
        initials_screwup = 0
        initials_distance = 0

    score = score - (0.75 * initials_screwup + 0.10 * (1 - initials_c)\
            + 0.15 * initials_distance) * (score)
    if AUTHORNAMES_UTILS_DEBUG:
        print "|- initials sets: ", no[1], " ", nt[1]
        print "|- initials distance: ", initials_distance
        print "|- initials c: ", initials_c
        print "|- initials screwup: ", initials_screwup
        print "||- initials score: ", score

    composits_eq = full_names_are_equal_composites(no, nt)
    if len(no[2]) > 0 and len(nt[2]) > 0:
        gender_eq = full_names_are_equal_gender(no, nt, gendernames)
    else:
        gender_eq = True
    vars_eq = full_names_are_synonymous(no, nt, name_variations)
    substr_eq = full_names_are_substrings(no, nt)

    if not initials_only:
        if len(no[2]) > len(nt[2]):
            nalo = no[2]
            nalt = nt[2]
        else:
            nalo = nt[2]
            nalt = no[2]
        nlo = len(nalo)
        nlt = len(nalt)
        names_screwup_list = [(distance(k, nalt[nlo - 1 - i]), max(len(k), len(nalt[nlo - 1 - i])))
                             for i, k in enumerate(reversed(nalo)) \
                             if nlo - 1 - i < nlt]
        max_names_screwup = max([float(i[0]) / i[1] for i in names_screwup_list])
        avg_names_screwup = sum([float(i[0]) / i[1] for i in names_screwup_list])\
                            / len(names_screwup_list)

    else:
        max_names_screwup = 0
        avg_names_screwup = 0

    score = score - score * 0.75 * max_names_screwup - score * 0.25 * avg_names_screwup
    if AUTHORNAMES_UTILS_DEBUG:
        print "|- max names screwup: ", max_names_screwup
        print "|- avg screwup: ", avg_names_screwup
        print "||- names score: ", score
        print "|- names composites: ", composits_eq
        print "|- same gender: ", gender_eq
        print "|- synonims: ", vars_eq
        print "|- substrings: ", substr_eq

    if vars_eq:
        synmap = [[i, j, names_are_synonymous(i, j, name_variations)] for i in no[2] for j in nt[2]]
        synmap = [i for i in synmap if i[2] == True]
        if AUTHORNAMES_UTILS_DEBUG:
            print "|-- synmap: ", synmap
        for i in synmap:
            if no[2].index(i[0]) == nt[2].index(i[1]):
                score = score + (1 - score) * 0.5
            else:
                score = score + (1 - score) * 0.15
    else:
        if AUTHORNAMES_UTILS_DEBUG:
            print "|-- synmap: empty"
    if AUTHORNAMES_UTILS_DEBUG:
        print "|-- synmap score: ", score

    if substr_eq and not initials_only:
        ssmap = [[i, j, names_are_substrings(i, j)] for i in no[2] for j in nt[2]]
        ssmap = [i for i in ssmap if i[2] == True]
        if AUTHORNAMES_UTILS_DEBUG:
            print "|-- substr map: ", ssmap
        for i in ssmap:
            if no[2].index(i[0]) == nt[2].index(i[1]):
                score = score + (1 - score) * 0.2
            else:
                score = score + (1 - score) * 0.05
    else:
        if AUTHORNAMES_UTILS_DEBUG:
            print "|-- substr map: empty"

    if AUTHORNAMES_UTILS_DEBUG:
        print "|-- substring score: ", score

    if composits_eq and not initials_only:
        if AUTHORNAMES_UTILS_DEBUG:
            print "|-- composite names"
        score = score + (1 - score) * 0.2
    else:
        if AUTHORNAMES_UTILS_DEBUG:
            print "|-- not composite names"
    if AUTHORNAMES_UTILS_DEBUG:
        print "|-- composite score: ", score

    if not gender_eq:
        score = score / 3.
        if AUTHORNAMES_UTILS_DEBUG:
            print "|-- apply gender penalty"
    else:
        if AUTHORNAMES_UTILS_DEBUG:
            print "|--   no  gender penalty"

    if AUTHORNAMES_UTILS_DEBUG:
        print "|-- gender score: ", score

    if surname_dist > MAX_ALLOWED_SURNAME_DISTANCE:
        score = 0.0
        if AUTHORNAMES_UTILS_DEBUG:
            print "|- surname trim: ", score
    else:
        if AUTHORNAMES_UTILS_DEBUG:
            print "|- no surname trim: ", score

    if initials_only and (not only_initials_available or initials_penalty):
        score = score * .9
        if AUTHORNAMES_UTILS_DEBUG:
            print "|- initials only penalty: ", score, initials_only, only_initials_available
    else:
        if AUTHORNAMES_UTILS_DEBUG:
            print "|- no initials only penalty", initials_only, only_initials_available

    if AUTHORNAMES_UTILS_DEBUG:
        print "||- final score:  ", score


    return score


def generate_last_name_cluster_str(name):
    '''
    Use this function to find the last name cluster
    this name should be associated with.
    '''
    family = split_name_parts(name.decode('utf-8'))[0]
    artifact_removal = re.compile("[^a-zA-Z0-9]")
    return artifact_removal.sub("", family).lower()


GLOBAL_gendernames = _load_gender_firstnames_dict()
GLOBAL_name_variations = _load_firstname_variations()

