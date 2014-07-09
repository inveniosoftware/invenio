# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2011, 2012, 2013, 2014 CERN.
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

import os
import re
import pkg_resources
from copy import deepcopy
from math import sqrt

from . import config as bconfig
from .string_utils import string_partition
from .general_utils import name_comparison_print

from invenio.utils.text import translate_to_ascii
from jellyfish import levenshtein_distance as distance

artifact_removal = re.compile("[^a-zA-Z0-9]")

CFG_AUTHORIDS_NAME_AUTHORITY_DIR = pkg_resources.resource_filename(
            'invenio.modules.authorids', 'name_authority_files')

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
            # Fix for dashes
            surname = re.sub('-([a-z])', lambda n:'-' + n.group(1).upper(), surname)
            break

    if not found_sep:
        if name_string.count(" ") > 0:
            rest_of_name, surname = string_partition(name_string, ' ', direc='r')[0::2]
            surname = surname.strip().capitalize()
            # Fix for dashes
            surname = re.sub('-([a-z])', lambda n:'-' + n.group(1).upper(), surname)
        else:
            surname = name_string
            surname = surname.strip().capitalize()
            # Fix for dashes
            surname = re.sub('-([a-z])', lambda n:'-' + n.group(1).upper(), surname)
            if not return_all_lower:
                return [surname, [], [], []]
            else:
                return [surname.lower(), [], [], []]

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


create_canonical_name_artifact_removal_re = re.compile("[^a-zA-Z0-9]")
create_canonical_name_whitespace_removal = re.compile("[ ]{1,10}")
def create_canonical_name(name):
    try:
        name = translate_to_ascii(name)[0]
    except IndexError:
        name = 'invalid'

    canonical_name = create_unified_name(name, reverse=True)
    canonical_name = create_canonical_name_artifact_removal_re.sub(" ", canonical_name)
    canonical_name = create_canonical_name_whitespace_removal.sub(" ", canonical_name)
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
    name = splitted_name[0]

    if not splitted_name[1] and not splitted_name[2]:
        return name

    name = name + ','

    for i in range(len(splitted_name[1])):
        try:
            fname = splitted_name[2][splitted_name[3].index(i)]
            name = name + ' ' + fname.capitalize()
        except (IndexError, ValueError):
            name = name + ' ' + splitted_name[1][i].capitalize() + '.'

    return name


create_indexable_name_artifact_removal_re = re.compile("[^a-zA-Z,\s]")
def create_indexable_name(name_string):
    '''
    Creates a normalized name from a given name array. A normalized name
    looks like "Lastname, Firstnames and Initials"

    @param splitted_name: name array from split_name_parts
    @type splitted_name: list in form [string, list, list]

    @return: normalized name
    @rtype: string
    '''


    name_string = create_indexable_name_artifact_removal_re.sub(' ',name_string)
    splitted_name = split_name_parts(name_string)

    name = splitted_name[0]

    if not splitted_name[1] and not splitted_name[2]:
        return name.lower()

    for i in range(len(splitted_name[1])):
        try:
            fname = splitted_name[2][splitted_name[3].index(i)]
            name = name + ' ' + fname
        except (IndexError, ValueError):
            name = name + ' ' + splitted_name[1][i]
    return name.lower()

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


clean_name_string_re_whitespace = re.compile("[^a-zA-Z0-9,.\s]")
clean_name_string_re =  re.compile("[^a-zA-Z0-9,.]")
clean_name_string_whitespace_removal = re.compile("[\s]{2,100}")

def clean_name_string(namestring, replacement=" ", keep_whitespace=True,
                      trim_whitespaces=False):
    '''
    remove specific artifacts from the names in order to be able to
    compare them. E.g. 't Hooft, G. and t'Hooft, G.

    @param namestring: the string to be cleaned
    @type namestring: string
    '''
#    artifact_removal = re.compile("['`\-\[\]\_\"]")
    artifact_removal_re = None

    if trim_whitespaces:
        namestring.strip()

    if keep_whitespace:
        artifact_removal_re = clean_name_string_re_whitespace
    else:
        artifact_removal_re = clean_name_string_re


    tmp = artifact_removal_re.sub(replacement, namestring)

    tmp = clean_name_string_whitespace_removal.sub(" ", tmp).strip()

    return tmp


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

    score = 0.0
    oname = deepcopy(origin_name)
    tname = deepcopy(target_name)

    oname = translate_to_ascii(oname)[0]
    tname = translate_to_ascii(tname)[0]

    orig_name = split_name_parts(oname.lower())
    targ_name = split_name_parts(tname.lower())
    orig_name[0] = clean_name_string(orig_name[0],
                                     replacement="",
                                     keep_whitespace=False)
    targ_name[0] = clean_name_string(targ_name[0],
                                     replacement="",
                                     keep_whitespace=False)
    if orig_name[0].lower() == targ_name[0].lower():
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


def full_names_are_equal_composites(name1, name2, only_names=False):
    '''
    Checks if names are equal composites; e.g. "guangsheng" vs. "guang sheng"

    @param name1: Full Name string of the first name (w/ last name)
    @type name1: string
    @param name2: Full Name string of the second name (w/ last name)
    @type name2: string

    @return: Are the names equal composites?
    @rtype: boolean
    '''
    if not isinstance(name1, list) and not only_names:
        name1 = split_name_parts(name1)[2]

    if not isinstance(name2, list) and not only_names:
        name2 = split_name_parts(name2)[2]

    is_equal_composite = False
    oname_variations = create_name_tuples(name1)
    tname_variations = create_name_tuples(name2)

    for oname_variation in oname_variations:
        for tname_variation in tname_variations:
            oname = clean_name_string(oname_variation.lower(), "", False, True)
            tname = clean_name_string(tname_variation.lower(), "", False, True)

            if oname == tname:
                is_equal_composite = True
                break

    return is_equal_composite


def full_names_are_equal_gender(name1, name2, gendernames, only_names=False):
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
    if not isinstance(name1, list) and not only_names:
        name1 = split_name_parts(name1)[2]

    if not isinstance(name2, list) and not only_names:
        name2 = split_name_parts(name2)[2]

    names_are_equal_gender_b = True
    ogender = None
    tgender = None
#    oname = name1[2][0].lower()
#    tname = name2[2][0].lower()
#    oname = clean_name_string(oname, "", False, True)
#    tname = clean_name_string(tname, "", False, True)

    onames = [clean_name_string(n.lower(), "", False, True) for n in name1]
    tnames = [clean_name_string(n.lower(), "", False, True) for n in name2]

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

    a = (name1 in nvar and name2 in nvar for nvar in name_variations)
    if True in a:
        return True
    return False

def full_names_are_synonymous(name1, name2, name_variations, only_names=False):
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
    if not isinstance(name1, list) and not only_names:
        name1 = split_name_parts(name1)[2]

    if not isinstance(name2, list) and not only_names:
        name2 = split_name_parts(name2)[2]

    names_are_synonymous_b = False
    max_matches = min(len(name1), len(name2))
    matches = []

    for i in xrange(max_matches):
        matches.append(False)

    for nvar in name_variations:
        for i in xrange(max_matches):
            oname = name1[i].lower()
            tname = name2[i].lower()
            oname = clean_name_string(oname, "", False, True)
            tname = clean_name_string(tname, "", False, True)

            if (oname in nvar and tname in nvar) or oname == tname:
                #name_comparison_print('      ', oname, ' and ', tname, ' are synonyms!')
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

def full_names_are_substrings(name1, name2, only_names=False):
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
    if not isinstance(name1, list) and not only_names:
        name1 = split_name_parts(name1)[2]

    if not isinstance(name2, list) and not only_names:
        name2 = split_name_parts(name2)[2]

    onames = name1
    tnames = name2
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

def _load_gender_firstnames_dict(files=None):
    if not files:
        files = {'boy':  os.path.join(CFG_AUTHORIDS_NAME_AUTHORITY_DIR,
                                      'male_firstnames.txt'),
                 'girl': os.path.join(CFG_AUTHORIDS_NAME_AUTHORITY_DIR,
                                      'female_firstnames.txt')}

    boyf = open(files['boy'], 'r')
    boyn = set([x.strip().lower() for x in boyf.readlines()])
    boyf.close()
    girlf = open(files['girl'], 'r')
    girln = set([x.strip().lower() for x in girlf.readlines()])
    girlf.close()
    return {'boys':(boyn - girln), 'girls':(girln - boyn)}


def _load_firstname_variations(filename=''):
    #will load an array of arrays: [['rick','richard','dick'],['john','jhonny']]
    if not filename:
        filename = os.path.join(CFG_AUTHORIDS_NAME_AUTHORITY_DIR,
                                'name_variants.txt')

    retval = []
    r = re.compile("\n")
    fp = open(filename)

    for l in fp.readlines():
        lr = r.sub("", l)
        retval.append(set([clean_name_string(name.lower(), "", False, True)
                       for name in lr.split(";") if name]))

    fp.close()

    return retval


def surname_compatibility(sa, sb):
    name_comparison_print('|-- Comparing surnames: %s %s'% (sa,sb))
    MAX_ALLOWED_SURNAME_DISTANCE_PERCENT = 0.33
    sa = clean_name_string(sa, replacement='', keep_whitespace=False, trim_whitespaces=True)
    sb = clean_name_string(sb, replacement='', keep_whitespace=False, trim_whitespaces=True)
    dist = distance(sa, sb)
    ml = float(max(len(sa),len(sb)))
    name_comparison_print('|--- dist:%s, ml:%s' % (dist,ml))

    if ml==0 or dist/ml > MAX_ALLOWED_SURNAME_DISTANCE_PERCENT:
        return 0.0
    else:
        return 1.-float(dist)/max(len(sa),len(sb))

def initials_compatibility(ia, ib):
    max_n_initials = max(len(ia), len(ib))
    initials_intersection = set(ia).intersection(set(ib))
    n_initials_intersection = len(initials_intersection)
    initials_union = set(ia).union(set(ib))
    n_initials_union = len(initials_union)
    initials_distance = distance("".join(ia), "".join(ib))

    name_comparison_print('|-- Comparing initials, %s %s' % (ia, ib))
    name_comparison_print('|--- initials distance %s'% (initials_distance))

    if n_initials_union > 0:
        initials_c = float(n_initials_intersection) / float(n_initials_union)
    else:
        initials_c = 1

    name_comparison_print('|--- initials c %s'% (initials_c))

    if len(ia) > len(ib):
        alo = ia
        alt = ib
    else:
        alo = ib
        alt = ia
    lo = len(alo)
    lt = len(alt)
    if max_n_initials > 0:
        initials_screwup = sum([i + 1 for i, k in enumerate(reversed(alo))
                            if lo - 1 - i < lt and k != alt[lo - 1 - i] ]) / \
                            float(float(max_n_initials * (max_n_initials + 1)) / 2)
        initials_distance = float(initials_distance) / max_n_initials
    else:
        initials_screwup = 0
        initials_distance = 0

    name_comparison_print('|--- initials screwup, %s '% (initials_screwup))
    name_comparison_print('|--- initials distance, %s'% (initials_distance))

    return max(0.0, 0.8*initials_c + 0.1*(1-initials_distance) + 0.1*(1-initials_screwup))


def compare_first_names(fna, fnb):
    gendernames = GLOBAL_gendernames
    name_variations = GLOBAL_name_variations

    initials_only = ((min(len(fna), len(fnb))) == 0)

    name_comparison_print('|-- Comparing names %s %s' % (fna,fnb))
    if len(fna) > 0 and len(fnb) > 0:
        gender_eq = full_names_are_equal_gender(fna, fnb, gendernames, only_names=True)
    else:
        gender_eq = None

    name_comparison_print("|--- gender equal: %s" % gender_eq)

    names_are_equal_composites = False
    if not initials_only:
        names_are_equal_composites = full_names_are_equal_composites(fna,fnb, only_names=True)
    name_comparison_print("|--- equal composites: %s" % names_are_equal_composites)

    vars_eq = full_names_are_synonymous(fna, fnb, name_variations, only_names=True)
    substr_eq = full_names_are_substrings(fna, fnb, only_names=True)

    name_comparison_print("|--- synonims: %s" % vars_eq)
    name_comparison_print("|--- substrings: %s" % substr_eq)

    if not initials_only:
        if len(fna) > len(fnb):
            nalo = fna
            nalt = fnb
        else:
            nalo = fnb
            nalt = fna
        nlo = len(nalo)
        nlt = len(nalt)
        names_screwup_list = [(distance(k, nalt[nlo - 1 - i]), max(len(k), len(nalt[nlo - 1 - i])))
                             for i, k in enumerate(reversed(nalo)) \
                             if nlo - 1 - i < nlt]

        def _min_names_screwup_list(nalo, nalt):
            nalo = list(nalo)
            nalt = list(nalt)
            sl = []
            for n in nalo:
                maxs = max(len(n), max((len(k) for k in nalt)))
                all_scr = [distance(n,k) for k in nalt]
                mins = min(all_scr)
                sl.append((mins,maxs))
                nalt.pop(all_scr.index(mins))
                if len(nalt) < 1:
                    break
            return sl

        min_names_screwup_list = _min_names_screwup_list(nalo, nalt)
        max_names_screwup = max([float(i[0]) / i[1] for i in names_screwup_list])
        min_names_screwup = min([float(i[0]) / i[1] for i in min_names_screwup_list])
        avg_names_screwup = (sum([float(i[0]) / i[1] for i in names_screwup_list])/len(names_screwup_list)+
                             sum([float(i[0]) / i[1] for i in min_names_screwup_list])/len(min_names_screwup_list))/2

    else:
        max_names_screwup = 0
        min_names_screwup = 0
        avg_names_screwup = 0

    name_comparison_print('|--- screwups min, max, avg: %s %s %s' %
                    (str(min_names_screwup),str(max_names_screwup), str(avg_names_screwup)))

    orig_max_names_screwup = max_names_screwup

    if max_names_screwup > 0.1:
        name_comparison_print("|--- forcing names screwup to one!")
        max_names_screwup = 1
        min_names_screwup = 1
        avg_names_screwup = 1

    name_comparison_print("|--- min screwup: %s" % min_names_screwup)
    name_comparison_print("|--- max screwup: %s" % max_names_screwup)
    name_comparison_print("|--- avg screwup: %s" % avg_names_screwup)

    compat_score = max(1 - ( 0.25 * max_names_screwup + 0.5 * avg_names_screwup + 0.25 * min_names_screwup), 0.0)

    name_comparison_print("|--- Name compatibility score: %s" % compat_score)

    if names_are_equal_composites and substr_eq:
        compat_score = min(1.0, compat_score + 0.7)
    elif not names_are_equal_composites and substr_eq:
        compat_score = min(1.0, compat_score + max(0., (1-orig_max_names_screwup)*0.75))

    name_comparison_print("|--- names are equal composites and subtring bonus: %s"% compat_score)


    if vars_eq:
        compat_score = min(1.0, compat_score + 0.5)

    name_comparison_print("|--- synonims bonus: %s"% compat_score)

    if gender_eq != None and not gender_eq:
        compat_score = max(0.0, compat_score * 0.25)

    name_comparison_print("|--- Different Gender penalty: %s"% compat_score)

    return compat_score

def compare_names(origin_name, target_name, initials_penalty=False):
    ''' Compare two names '''

    name_comparison_print("\nComparing: " , origin_name, ' ', target_name)

    origin_name = translate_to_ascii(origin_name)[0]
    target_name = translate_to_ascii(target_name)[0]

    no = split_name_parts(origin_name, True, "", True)
    nt = split_name_parts(target_name, True, "", True)

    name_comparison_print("|- splitted no: %s"% no)
    name_comparison_print("|- splitted nt: %s"% nt)

    FS_surname_score = surname_compatibility(no[0], nt[0])

    assert FS_surname_score >= 0 and FS_surname_score <=1, "Compare_names: Surname score out of range"

    name_comparison_print("|- surname score: %s"% FS_surname_score)

    FS_initials_only = ((min(len(no[2]), len(nt[2]))) == 0)
    FS_initials_score = initials_compatibility(no[1], nt[1])

    assert FS_initials_score >= 0 and FS_initials_score <=1, "Compare_names: initials score out of range"

    name_comparison_print('|- initials only %s'% FS_initials_only)
    name_comparison_print('|- initials score %s'% FS_initials_score)

    FS_first_names_score = compare_first_names(no[2],nt[2])

    assert FS_first_names_score >= 0 and FS_first_names_score <=1, "Compare_names: firstname score out of range"
    name_comparison_print('|- names score %s'% FS_first_names_score )

    if not FS_initials_only:
        x = FS_initials_score
        y = FS_first_names_score
        try:
            FS_ns = (x*y)/sqrt(x**2+y**2)*SQRT2
        except ZeroDivisionError:
            FS_ns = 0.0
    else:
        FS_ns = FS_initials_score * 0.6

    name_comparison_print('|- final scores %s %s'% (FS_surname_score, FS_ns))

    x = FS_surname_score
    y = FS_ns

    try:
        final_score = (x*y)/sqrt(x**2+y**2)*SQRT2
    except ZeroDivisionError:
        final_score = 0.0

    name_comparison_print("|- final score is... %s" % final_score)
    return final_score


def generate_last_name_cluster_str(name):
    '''
    Use this function to find the last name cluster
    this name should be associated with.
    '''
    family = split_name_parts(name.decode('utf-8'))[0]
    return artifact_removal.sub("", family).lower()

def most_relevant_name(name_variants):
    '''
    getting the most relevant name out of a list of names


    @param: name_variants
    @type: list of string names

    @return: most relevant name
    @type: String
    '''
    if not name_variants:
        return None
    name_parts_list = []

    for name in name_variants:
        name_parts_list.append(split_name_parts(name))
    sorted_by_relevance_name_list = sorted(sorted(name_parts_list, key=lambda k : len(k[1]), reverse=True), key = lambda k:len(k[2]), reverse=True)

    return create_normalized_name(sorted_by_relevance_name_list[0])

from invenio.utils.datastructures import LazyDict
GLOBAL_gendernames = LazyDict(_load_gender_firstnames_dict)
GLOBAL_name_variations = [] #_load_firstname_variations()

