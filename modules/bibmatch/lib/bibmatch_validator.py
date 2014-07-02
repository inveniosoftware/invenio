## This file is part of Invenio.
## Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""
BibMatch - tool to match records with database content of
an Invenio instance, either locally or remotely.

bibmatch_validator - module containing functions for match validation step
"""

__revision__ = "$Id$"

import re
import sys
import pprint
import difflib

from invenio.config import CFG_BIBMATCH_MATCH_VALIDATION_RULESETS, \
                           CFG_BIBMATCH_FUZZY_MATCH_VALIDATION_LIMIT, \
                           CFG_BIBMATCH_MIN_VALIDATION_COMPARISONS
from invenio.bibmatch_config import CFG_BIBMATCH_VALIDATION_MATCHING_MODES, \
                                    CFG_BIBMATCH_VALIDATION_RESULT_MODES, \
                                    CFG_BIBMATCH_VALIDATION_COMPARISON_MODES, \
                                    CFG_BIBMATCH_LOGGER
from invenio.bibrecord import create_records, record_get_field_values
from invenio.xmlmarc2textmarc import get_sysno_from_record, create_marc_record
from invenio.bibauthorid_name_utils import soft_compare_names
from invenio.textutils import translate_to_ascii

re_valid_tag = re.compile("^[0-9]{3}[a-zA-Z0-9_%]{0,3}$")


class BibMatchValidationError(Exception):
    pass


def validate_matches(bibmatch_recid, record, server, result_recids, \
                     collections="", verbose=0, ascii_mode=False):
    """
    Perform record validation on a set of matches. This function will
    try to find any search-result that "really" is a correct match, based on
    various methods defined in a given rule-set. See more about rule-sets in
    validate_match() function documentation.

    This function will return a tuple containing a list of all record IDs
    satisfying the count of field matching needed for exact matches and a
    similar list for fuzzy matches that has less fields matching then the
    threshold. Records that are not matching at all are simply left out of
    the lists.

    @param bibmatch_recid: Current record number. Used for logging.
    @type bibmatch_recid: int

    @param record: bibrec structure of original record
    @type record: dict

    @param server: InvenioConnector object to matched record source repository
    @type server: InvenioConnector object

    @param result_recids: the list of record ids from search result.
    @type result_recids: list

    @param collections: list of collections to search, if specified
    @type collections: list

    @param verbose: be loud
    @type verbose: int

    @param ascii_mode: True to transform values to its ascii representation
    @type ascii_mode: bool

    @return: list of record IDs matched
    @rtype: list
    """
    matches_found = []
    fuzzy_matches_found = []

    # Generate final rule-set by analyzing the record
    final_ruleset = get_validation_ruleset(record)
    if not final_ruleset:
        raise BibMatchValidationError("Bad configuration rule-set." \
                                      "Please check that CFG_BIBMATCH_MATCH_VALIDATION_RULESETS" \
                                      " is formed correctly.")

    if verbose > 8:
        sys.stderr.write("\nStart record validation:\n\nFinal validation ruleset used:\n")
        pp = pprint.PrettyPrinter(stream=sys.stderr, indent=2)
        pp.pprint(final_ruleset)
    CFG_BIBMATCH_LOGGER.info("Final validation ruleset used: %s" % (final_ruleset,))

    # Fetch all records in MARCXML and convert to BibRec
    found_record_list = []
    query = " OR ".join(["001:%d" % (recid,) for recid in result_recids])

    if collections:
        search_params = dict(p=query, of="xm", c=collections)
    else:
        search_params = dict(p=query, of="xm")
    CFG_BIBMATCH_LOGGER.info("Fetching records to match: %s" % (str(search_params),))
    result_marcxml = server.search_with_retry(**search_params)
    # Check if record was found
    if result_marcxml:
        found_record_list = [r[0] for r in create_records(result_marcxml)]
        # Check if BibRecord generation was successful
        if not found_record_list:
            # Error fetching records. Unable to validate. Abort.
            raise BibMatchValidationError("Error retrieving MARCXML for possible matches from %s. Aborting." \
                                          % (server.server_url,))
        if len(found_record_list) < len(result_recids):
            # Error fetching all records. Will still continue.
            sys.stderr.write("\nError retrieving all MARCXML for possible matched records from %s.\n" \
                              % (server.server_url,))

    # Validate records one-by-one, adding any matches to the list of matching record IDs
    current_index = 1
    for matched_record in found_record_list:
        recid = record_get_field_values(matched_record, tag="001")[0]
        if verbose > 8:
            sys.stderr.write("\n Validating matched record #%d (%s):\n" % \
                             (current_index, recid))
        CFG_BIBMATCH_LOGGER.info("Matching of record %d: Comparing to matched record %s" % \
                                 (bibmatch_recid, recid))

        match_ratio, fuzzy = validate_match(record, matched_record, final_ruleset,
                                            verbose, ascii_mode)

        if match_ratio == 1.0 and not fuzzy:
            # All matches were a success, this is an exact match
            CFG_BIBMATCH_LOGGER.info("Matching of record %d: Exact match found -> %s" % (bibmatch_recid, recid))
            matches_found.append(recid)
        elif match_ratio >= CFG_BIBMATCH_FUZZY_MATCH_VALIDATION_LIMIT or fuzzy:
            # This means that some matches failed, but some succeeded as well. That's fuzzy...
            CFG_BIBMATCH_LOGGER.info("Matching of record %d: Fuzzy match found -> %s" % \
                                     (bibmatch_recid, recid))
            fuzzy_matches_found.append(recid)
        else:
            CFG_BIBMATCH_LOGGER.info("Matching of record %d: Not a match" % (bibmatch_recid,))
        current_index += 1

    # Return list of matching record IDs
    return matches_found, fuzzy_matches_found

def validate_match(org_record, matched_record, ruleset, verbose=0, ascii_mode=False):
    """
    This function will try to match the original record with matched record.
    This comparison uses various methods defined in configuration and/or
    determined from the source record.

    These methods can be derived from each rule-set defined, which contains a
    mapping of a certain pattern to a list of rules defining the "match-strategy".

    For example:

    ('260__', [{ 'tags' : '260__c',
                 'threshold' : 0.8,
                 'compare_mode' : 'lazy',
                 'match_mode' : 'date',
                 'result_mode' : 'normal' }])

    Quick run-down of possible values:
      Compare mode:
        'strict'    : all (sub-)fields are compared, and all must match. Order is significant.
        'normal'    : all (sub-)fields are compared, and all must match. Order is ignored.
        'lazy'      : all (sub-)fields are compared with each other and at least one must match
        'ignored'   : the tag is ignored in the match. Used to disable previously defined rules.

      Match mode:
        'title'     : uses a method specialized for comparing titles, e.g. looking for subtitles
        'author'    : uses a special authorname comparison. Will take initials into account.
        'identifier': special matching for identifiers, stripping away punctuation
        'date'      : matches dates by extracting and comparing the year
        'normal'    : normal string comparison.

      Result mode:
        'normal'    : a failed match will cause the validation to continue on other rules (if any)
                      a successful match will cause the validation to continue on other rules (if any)
        'final'     : a failed match will cause the validation to immediately exit as a failure.
                      a successful match will cause validation to immediately exit as a success.
        'joker'     : a failed match will cause the validation to continue on other rules (if any).
                      a successful match will cause validation to immediately exit as a success.
        'fuzzy'     : a failed match will cause the validation to continue on other rules (if any)
                      so long as it is the only rule that is failing, else exit as failure.
                      a successful match will cause the validation to continue on other rules (if any)

    Fields are considered matching when all its subfields or values match. ALL matching strategy
    must return successfully for a match to be validated (except for 'joker' mode).

    @param org_record: bibrec structure of original record
    @type org_record: dict

    @param matched_record: bibrec structure of matched record
    @type matched_record: dict

    @param ruleset: the default rule-set {tag: strategy,..} used when validating
    @type ruleset: dict

    @param verbose: be loud
    @type verbose: int

    @param ascii_mode: True to transform values to its ascii representation
    @type ascii_mode: bool

    @return: Number of matches succeeded divided by number of comparisons done. At least two
        successful matches must be done unless a joker or final match is found
    @rtype: float
    """
    total_number_of_matches = 0
    total_number_of_comparisons = 0
    fuzzy_flag = False
    for field_tags, threshold, compare_mode, match_mode, result_mode in ruleset:
        field_tag_list = field_tags.split(',')
        if verbose > 8:
            sys.stderr.write("\nValidating tags: %s in parsing mode '%s' and comparison\
 mode '%s' as '%s' result with threshold %0.2f\n" \
                             % (field_tag_list, compare_mode, match_mode, \
                                result_mode, threshold))
        current_matching_status = False

        ## 1. COMPARE MODE
        # Fetch defined fields from both records
        original_record_values = []
        matched_record_values = []
        for field_tag in field_tag_list:
            tag_structure = validate_tag(field_tag)
            if tag_structure != None:
                tag, ind1, ind2, code = tag_structure
                # Fetch all field instances to match
                original_values = record_get_field_values(org_record, tag, ind1, ind2, code)
                original_record_values.extend([value for value in original_values if value])
                matched_values = record_get_field_values(matched_record, tag, ind1, ind2, code)
                matched_record_values.extend([value for value in matched_values if value])

        if (len(original_record_values) == 0 or len(matched_record_values) == 0):
            # Both records do not have values, ignore.
            if verbose > 8:
                sys.stderr.write("\nBoth records do not have this field. Continue.\n")
            continue

        if result_mode != 'joker':
            # Since joker is a special beast (should have no impact on failure),
            # We first check if it is the current mode before incrementing number
            # of matching comparisons / attempts
            total_number_of_comparisons += 1

        if ascii_mode:
            original_record_values = translate_to_ascii(original_record_values)
            matched_record_values = translate_to_ascii(matched_record_values)

        ignore_order = True
        matches_needed = 0
        # How many field-value matches are needed for successful validation of this record
        if compare_mode == 'lazy':
            # 'lazy' : all fields are matched with each other, if any match = success
            matches_needed = 1
        elif compare_mode == 'normal':
            # 'normal' : all fields are compared, and all must match.
            # Order is ignored. The number of matches needed is equal
            # to the value count of original record
            matches_needed = len(original_record_values)
        elif compare_mode == 'strict':
            # 'strict' : all fields are compared, and all must match. Order matters.
            if len(original_record_values) != len(matched_record_values):
                # Not the same number of fields, not a valid match
                # Unless this is a joker, we return indicating failure
                if result_mode != 'joker':
                    return (0.0, fuzzy_flag)
                continue
            matches_needed = len(original_record_values)
            ignore_order = False
        if verbose > 8:
            sys.stderr.write("Total matches needed: %d -> " % (matches_needed,))

        ## 2. MATCH MODE
        comparison_function = None
        if match_mode == 'title':
            # Special title mode
            comparison_function = compare_fieldvalues_title
        elif match_mode == 'author':
            # Special author mode
            comparison_function = compare_fieldvalues_authorname
        elif match_mode == 'identifier':
            # Special identifier mode
            comparison_function = compare_fieldvalues_identifier
        elif match_mode == 'date':
            # Special identifier mode
            comparison_function = compare_fieldvalues_date
        else:
            # Normal mode
            comparison_function = compare_fieldvalues_normal

        # Get list of comparisons to perform containing extracted values
        field_comparisons = get_paired_comparisons(original_record_values, \
                                                   matched_record_values, \
                                                   ignore_order)

        if verbose > 8:
            sys.stderr.write("Field comparison values:\n%s\n" % (field_comparisons,))

        # Run comparisons according to match_mode
        current_matching_status, matches = comparison_function(field_comparisons, \
                                                               threshold, \
                                                               matches_needed)
        CFG_BIBMATCH_LOGGER.info("-- Comparing fields %s with %s = %d matches of %d" % \
                                 (str(original_record_values), \
                                  str(matched_record_values), \
                                  matches, matches_needed))

        ## 3. RESULT MODE
        if current_matching_status:
            if verbose > 8:
                sys.stderr.write("Fields matched successfully.\n")
            if result_mode in ['final', 'joker']:
                # Matching success. Return 5,5 indicating exact-match when final or joker.
                return (1.0, False)
            total_number_of_matches += 1
        else:
            # Matching failed. Not a valid match
            if result_mode == 'final':
                # Final does not allow failure
                return (0.0, False)
            elif result_mode == 'joker':
                if verbose > 8:
                    sys.stderr.write("Fields not matching. (Joker)\n")
            elif result_mode == 'fuzzy':
                if not fuzzy_flag:
                    fuzzy_flag = True
                    total_number_of_matches += 1
                else:
                    return (0.0, False)
            else:
                if verbose > 8:
                    sys.stderr.write("Fields not matching. \n")

    if total_number_of_matches < CFG_BIBMATCH_MIN_VALIDATION_COMPARISONS \
        or total_number_of_comparisons == 0:
        return (0.0, fuzzy_flag)
    ratio = total_number_of_matches / float(total_number_of_comparisons)
    return (ratio, fuzzy_flag)

def transform_record_to_marc(record, options={'text-marc':1, 'aleph-marc':0}):
    """ This function will transform a given bibrec record into marc using
    methods from xmlmarc2textmarc in invenio.textutils. The function returns the
    record as a MARC string.

    @param record: bibrec structure for record to transform
    @type record: dict

    @param options: dictionary describing type of MARC record. Defaults to textmarc.
    @type options: dict

    @return resulting MARC record as string """
    sysno = get_sysno_from_record(record, options)
    # Note: Record dict is copied as create_marc_record() perform deletions
    return create_marc_record(record.copy(), sysno, options)

def compare_fieldvalues_normal(field_comparisons, threshold, matches_needed):
    """
    Performs field validation given an list of field comparisons using a standard
    normalized string distance metric. Each comparison is done according to given
    threshold which the normalized result must be equal or above to match.

    Before the values are compared they will be massaged by putting all values
    lower-case and any leading/trailing spaces are removed.

    During validation the fields are compared and matches are counted per
    field, up to the given amount of matches needed is met, causing the
    function to return True. If validation ends before this threshold is met
    it will return False.

    @param field_comparisons: list of comparisons, each which contains a list
        of field-value to field-value comparisons.
    @type field_comparisons: list

    @param threshold: number describing the match threshold a comparison must
        exceed to become a positive match.
    @type threshold: float

    @param matches_needed: number of positive field matches needed for the entire
        comparison process to give a positive result.
    @type matches_needed: int

    @return: tuple of matching result, True if enough matches are found, False if not,
        and number of matches.
    @rtype: tuple
    """
    matches_found = 0
    # Loop over all possible comparisons field by field, if a match is found,
    # we are done with this field and break out to try and match next field.
    for comparisons in field_comparisons:
        for value, other_value in comparisons:
            # Value matching - put values in lower case and strip leading/trailing spaces
            diff = difflib.SequenceMatcher(None, value.lower().strip(), \
                                           other_value.lower().strip()).ratio()
            if diff >= threshold:
                matches_found += 1
                break
        # If we already have found required number of matches, we return immediately
        if matches_found >= matches_needed:
            return True, matches_found
    return matches_found >= matches_needed, matches_found

def compare_fieldvalues_authorname(field_comparisons, threshold, matches_needed):
    """
    Performs field validation given an list of field comparisons using a technique
    that is meant for author-names taking into account initials vs. full-name,
    using matching techniques available from BibAuthorId.

    Each comparison is done according to given threshold which the result must
    be equal or above to match.

    During validation the fields are compared and matches are counted per
    field, up to the given amount of matches needed is met, causing the
    function to return True. If validation ends before this threshold is met
    it will return False.

    @param field_comparisons: list of comparisons, each which contains a list
        of field-value to field-value comparisons.
    @type field_comparisons: list

    @param threshold: number describing the match threshold a comparison must
        exceed to become a positive match.
    @type threshold: float

    @param matches_needed: number of positive field matches needed for the entire
        comparison process to give a positive result.
    @type matches_needed: int

    @return: tuple of matching result, True if enough matches are found, False if not,
        and number of matches.
    @rtype: tuple
    """
    matches_found = 0
    # Loop over all possible comparisons field by field, if a match is found,
    # we are done with this field and break out to try and match next field.
    for comparisons in field_comparisons:
        for value, other_value in comparisons:
            # Grab both permutations of a name (before, after and after, before)
            # and compare to each unique commutative combination. Ex:
            # Doe,J vs. Smith,J -> [(('Smith,J', 'Doe,J'), ('Smith,J', 'J,Doe')),
            #                       (('J,Smith', 'Doe,J'), ('J,Smith', 'J,Doe'))]
            author_comparisons = [pair for pair in get_paired_comparisons(\
                                          get_reversed_string_variants(value), \
                                          get_reversed_string_variants(other_value))][0]
            for str1, str2 in author_comparisons:
                # Author-name comparison - using BibAuthorid function
                diff = soft_compare_names(str1, str2)
                if diff >= threshold:
                    matches_found += 1
                    break
            else:
                # We continue as no match was found
                continue
            # We break out as a match was found
            break
        # If we already have found required number of matches, we return immediately
        if matches_found >= matches_needed:
            return True, matches_found
    # Often authors are not matching fully, so lets allow for the number of matches to
    # be a little lower, using the same threshold
    result = matches_found >= matches_needed or matches_found / float(matches_needed) > threshold
    return result, matches_found

def compare_fieldvalues_identifier(field_comparisons, threshold, matches_needed):
    """
    Performs field validation given an list of field comparisons using a method to
    normalize identifiers for comparisons. For example by removing hyphens and other
    symbols.

    Each comparison is done according to given threshold which the normalized
    result must be equal or above to match. Before the values are compared they will be
    converted to lower-case.

    During validation the fields are compared and matches are counted per
    field, up to the given amount of matches needed is met, causing the
    function to return True. If validation ends before this threshold is met
    it will return False.

    @param field_comparisons: list of comparisons, each which contains a list
        of field-value to field-value comparisons.
    @type field_comparisons: list

    @param threshold: number describing the match threshold a comparison must
        exceed to become a positive match.
    @type threshold: float

    @param matches_needed: number of positive field matches needed for the entire
        comparison process to give a positive result.
    @type matches_needed: int

    @return: tuple of matching result, True if enough matches are found, False if not,
        and number of matches.
    @rtype: tuple
    """
    matches_found = 0
    # Loop over all possible comparisons field by field, if a match is found,
    # we are done with this field and break out to try and match next field.
    for comparisons in field_comparisons:
        for value, other_value in comparisons:
            # Value matching - put values in lower case and remove punctuation
            # and trailing zeroes. 'DESY-F35D-97-04' -> 'DESYF35D974'
            value = re.sub('\D[0]|\W+', "", value.lower())
            other_value = re.sub('\D[0]|\W+', "", other_value.lower())
            diff = difflib.SequenceMatcher(None, value, other_value).ratio()
            if diff >= threshold:
                matches_found += 1
                break
        # If we already have found required number of matches, we return immediately
        if matches_found >= matches_needed:
            return True, matches_found
    return matches_found >= matches_needed, matches_found

def compare_fieldvalues_title(field_comparisons, threshold, matches_needed):
    """
    Performs field validation given an list of field comparisons using a method
    specialized for comparing titles. For example by looking for possible
    concatenated title and subtitles or having a KB of common word aliases.

    Each comparison is done according to given threshold which the normalized
    result must be equal or above to match.

    Before the values are compared they will be massaged by putting all values
    lower-case and any leading/trailing spaces are removed.

    During validation the fields are compared and matches are counted per
    field, up to the given amount of matches needed is met, causing the
    function to return True. If validation ends before this threshold is met
    it will return False.

    @param field_comparisons: list of comparisons, each which contains a list
        of field-value to field-value comparisons.
    @type field_comparisons: list

    @param threshold: number describing the match threshold a comparison must
        exceed to become a positive match.
    @type threshold: float

    @param matches_needed: number of positive field matches needed for the entire
        comparison process to give a positive result.
    @type matches_needed: int

    @return: tuple of matching result, True if enough matches are found, False if not,
        and number of matches.
    @rtype: tuple
    """
    matches_found = 0
    # Loop over all possible comparisons field by field, if a match is found,
    # we are done with this field and break out to try and match next field.
    for comparisons in field_comparisons:
        for value, other_value in comparisons:
            # TODO: KB of alias mappings of common names
            title_comparisons = [pair for pair in _get_grouped_pairs(\
                                            get_separated_string_variants(value), \
                                            get_separated_string_variants(other_value))][0]
            for str1, str2 in title_comparisons:
                # Title comparison
                diff = difflib.SequenceMatcher(None, str1.lower().strip(), \
                                               str2.lower().strip()).ratio()
                if diff >= threshold:
                    matches_found += 1
                    break
            else:
                # We continue as no match was found
                continue
            # We break out as a match was found
            break
        # If we already have found required number of matches, we return immediately
        if matches_found >= matches_needed:
            return True, matches_found
    return matches_found >= matches_needed, matches_found

def compare_fieldvalues_date(field_comparisons, threshold, matches_needed):
    """
    Performs field validation given an list of field comparisons specialized
    towards matching dates. Each comparison is done according to given
    threshold which the final result must be equal or above to match.

    During validation the fields are compared and matches are counted per
    field, up to the given amount of matches needed is met, causing the
    function to return True. If validation ends before this threshold is met
    it will return False.

    @param field_comparisons: list of comparisons, each which contains a list
        of field-value to field-value comparisons.
    @type field_comparisons: list

    @param threshold: number describing the match threshold a comparison must
        exceed to become a positive match.
    @type threshold: float

    @param matches_needed: number of positive field matches needed for the entire
        comparison process to give a positive result.
    @type matches_needed: int

    @return: tuple of matching result, True if enough matches are found, False if not,
        and number of matches.
    @rtype: tuple
    """
    matches_found = 0
    # Loop over all possible comparisons field by field, if a match is found,
    # we are done with this field and break out to try and match next field.
    for comparisons in field_comparisons:
        for value, other_value in comparisons:
            value_list = re.findall('[0-9]{4}', value.lower())
            other_value_list = re.findall('[0-9]{4}', other_value.lower())
            for year1 in value_list:
                for year2 in other_value_list:
                    # Value matching - convert values to int
                    diff = compare_numbers(int(year1), int(year2))
                    if diff >= threshold:
                        matches_found += 1
                        break
                else:
                    continue
                break
            else:
                continue
            break
        # If we already have found required number of matches, we return immediately
        if matches_found >= matches_needed:
            return True, matches_found
    return matches_found >= matches_needed, matches_found

def get_validation_ruleset(record):
    """
    This function will iterate over any defined rule-sets in
    CFG_BIBMATCH_MATCH_VALIDATION_RULESETS, generating a validation
    rule-set for use when comparing records.

    in the order of appearance. Meaning that the last rules will have
    precedence over earlier one, should MARC tags be conflicting.

    You can add your own rule-sets in invenio.conf. The 'default' rule-set
    is always applied, but the tag-rules can be overwritten by other
    rule-sets. The rule-sets are only allowed to be tuples of two items.
    For example: ('980__ \$\$aTHESIS', { tag : (rules) })

    * The first part is a string containing a regular expression
      that is matched against the textmarc representation of each
      record. If a match is found, the final rule-set is updated with
      the given "sub rule-set", i.e. second item.

    * The second item is a dict that indicates specific MARC tags with
      corresponding validation rules.

    @param record: bibrec record dict to analyze
    @type record: dict

    @return: list of ordered rule-sets
    @rtype: list
    """
    # Convert original record to textmarc in order to regexp search
    original_record_marc = transform_record_to_marc(record)

    # Lets parse the rule-set configuration to try to match rule-sets
    # with original record, adding to/overwritin as we go
    validation_ruleset = {}
    for pattern, rules in CFG_BIBMATCH_MATCH_VALIDATION_RULESETS:
        if pattern == "default" or re.search(pattern, original_record_marc) != None:
            for rule in rules:
                # Simple validation of rules syntax
                if rule['compare_mode'] not in CFG_BIBMATCH_VALIDATION_COMPARISON_MODES:
                    return
                if rule['match_mode'] not in CFG_BIBMATCH_VALIDATION_MATCHING_MODES:
                    return
                if rule['result_mode'] not in CFG_BIBMATCH_VALIDATION_RESULT_MODES:
                    return

                try:
                    # Update/Add rule in rule-set
                    validation_ruleset[rule['tags']] = (rule['threshold'], \
                                                        rule['compare_mode'], \
                                                        rule['match_mode'], \
                                                        rule['result_mode'])
                except KeyError:
                    # Bad rule-set, return None
                    return

    # Now generate the final list of rules in proper order, so final and joker result-modes
    # are executed before normal rules. Order of precedence: final, joker, normal
    final_list = []
    joker_list = []
    normal_list = []
    for tag, (threshold, compare_mode, match_mode, result_mode) in validation_ruleset.iteritems():
        if compare_mode == 'ignored' or threshold <= 0.0:
            # Ignore rule
            continue
        if result_mode == 'final':
            final_list.append((tag, threshold, compare_mode, match_mode, result_mode))
        elif result_mode == 'joker':
            joker_list.append((tag, threshold, compare_mode, match_mode, result_mode))
        else:
            normal_list.append((tag, threshold, compare_mode, match_mode, result_mode))
    return final_list + joker_list + normal_list

def validate_tag(field_tag):
    """
    This function will return a tuple of (tag, ind1, ind2, code) as extracted
    from given string. If the tag is not deemed valid: return None.

    For example: "100__a" will return ('100', '', '', 'a')

    @param field_tag: field tag to extract MARC parts from
    @type field_tag: string

    @return: tuple of MARC tag parts, tag, ind1, ind2, code
    @rtype: tuple
    """
    if re_valid_tag.match(field_tag) != None:
        tag = field_tag[0:3]
        ind1 = field_tag[3:4]
        ind2 = field_tag[4:5]
        code = field_tag[5:6]
        if ind1 == "_":
            ind1 = ""
        if ind2 == "_":
            ind2 = ""
        return tag, ind1, ind2, code
    return None

def get_paired_comparisons(first_list, second_list, ignore_order=True):
    """
    This function will return a a list of comparisons, each which contains
    a list of all the possible unique item to item comparisons.

    If ordering is required, the lists must be of same length and the
    comparisons will be single item by item comparisons.

    @param first_list: a iterable to pair with second_list items
    @type first_list: iterable

    @param second_list: an iterable to be paired against first_list
    @type first_list: iterable

    @return: the resulting iterable of pairs grouped by first_list items
    @rtype: iterable
    """
    if ignore_order:
        # Get grouped permutations of comparisons between subfields
        paired_comparisons = _get_grouped_pairs(first_list, second_list)
    else:
        # Must have same number of items
        if len(first_list) != len(second_list):
            return []
        # Now prepare direct one-to-one comparisons
        paired_comparisons = [((first_list[i], second_list[i]),) \
                                for i in range(0, len(first_list))]
    return paired_comparisons

def compare_numbers(num1, num2):
    """
    This function will try to compare two numbers to each other,
    returning the normalized distance between them. The value
    returned will be between 0.0 - 1.0, with 1.0 being a full
    match, decreasing 0.1 per year in difference.

    Inspired by similar function in MarcXimil
    (http://marcximil.sourceforge.net/).

    @param num1: the first number to compare
    @type num1: int

    @param num2: the second number to compare
    @type num2: int

    @return: the normalized equality score between 0.0 and 1.0
    @rtype: float
    """
    return 1.0 - (abs(num1 - num2) * 0.1)

def get_separated_string_variants(s, sep=':'):
    """
    This function will return a list of all the possible combinations
    of substrings of given title when separated by given separator.

    For example:
    "scalar tensor theory : validity of Cosmic no hair conjecture"

    produces:

    ['scalar tensor theory ',
     ' validity of Cosmic no hair conjecture',
     'scalar tensor theory : validity of Cosmic no hair conjecture']

    It also returns variants containing several separators:

    "scalar tensor theory : validity of Cosmic no hair : conjecture"

    produces:

    ['scalar tensor theory ',
     ' validity of Cosmic no hair : conjecture',
     'scalar tensor theory : validity of Cosmic no hair ',
     ' conjecture',
     'scalar tensor theory : validity of Cosmic no hair : conjecture']

    @param s: string to generate variants from
    @type s: string

    @param sep: separator that splits the string in two. Defaults to colon (:).
    @type sep: string

    @return: list of strings
    @rtype: list
    """
    string_variants = []
    str_parts = s.split(sep)
    start_index = 1
    for dummy in str_parts:
        first_part = sep.join(str_parts[:start_index])
        if first_part != '':
            string_variants.append(first_part)
        last_part = sep.join(str_parts[start_index:])
        if last_part != '':
            string_variants.append(last_part)
        if start_index <= len(str_parts):
            start_index += 1
        else:
            break
    return string_variants

def get_reversed_string_variants(s, sep=','):
    """
    This function will return a tuple containing a pair of the original
    string and the reversed version, with regards to text before/after the
    separator (on first encounter of said separator).

    For example, "lastname, firstname", "firstname, lastname"

    @param s: string to extract pair from
    @type s: string

    @param sep: separator that splits the string in two. Defaults to comma (,).
    @type sep: string

    @return: tuple of strings
    @rtype: tuple
    """
    # Extract the different parts of the name using partition function.
    left, sep, right = s.partition(sep)
    return (left + sep + right, right + sep + left)

def _get_grouped_pairs(first_list, second_list):
    """
    This function will return a list of grouped pairs of items from
    the first list with every item in the second list.
    e.g. [1,2,3],[4,5] -> [([1, 4], [1, 5]),
                           ([2, 4], [2, 5]),
                           ([3, 4], [3, 5])]

    @param first_list: an iterable to pair with second_list items
    @type first_list: iterable

    @param second_list: an iterable to be paired against first_list
    @type second_list: iterable

    @return: the resulting iterable of pairs grouped by first_list items
    @rtype: iterable
    """
    pairs = []
    for first_item in first_list:
        pair_group = []
        for second_item in second_list:
            pair_group.append((first_item, second_item))
        pairs.append(tuple(pair_group))
    return pairs
