# -*- coding: utf-8 -*-

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

# pylint: disable=C0301

"""CDS Invenio Search Engine query parsers."""

import re
import string

from invenio.bibindex_engine_tokenizer import BibIndexFuzzyNameTokenizer as FNT

NameScanner = FNT()


class SearchQueryParenthesisedParser:
    """Parse search queries containing parenthesis.

    Current implementation is a simple linear parsing that does not support
    nested parenthesis and priority of operators.

    In case there is a need for nested parenthesis and priority of operators,
    the current implementation can be replaced by one that uses expression
    trees as they are more or less a standard way for parsing expressions.

    The method doing the main work is parse_query()

    Input: parse_query("ellis AND (muon OR kaon)")
    Output: list of [operator1, expression1, operator2, expression2, operator3...,expressionN].
    In case of error: Exception is raised
    """

    # all operator symbols recognized in expression
    _operators = ['+', '|', '-']

    # error messages
    _error_message_mismatched_parentheses = "Mismatched parenthesis."
    _error_message_nested_parentheses_not_supported = "Nested parenthesis are currently not supported."

    def __init__(self, default_operator='+'):
        """Initialize the state of the parser"""

        # default operator to be used if operator is missing between patterns
        self._DEFAULT_OPERATOR = default_operator

        self._re_quotes_match = re.compile('[^\\\\](".*?[^\\\\]")|[^\\\\](\'.*?[^\\\\]\')')

        self._query = ''
        # list of parsed patterns and operators
        self._patterns = []
        # indexes in the parsed query of beginning and end of currently parsed pattern
        self._pattern_beginning = 0
        self._pattern_end = 0

        # operators before and after the current pattern matched during parsing
        _preceding_operator = ""
        _preceding_operator_position = -1

        _following_operator = ""
        _following_operator_position = -1

        # flag indicating if processed symbols are inside parenthesis
        self._inside_parentheses = False

        # all operator symbols recognized in expression
        _operators = ['+', '|', '-']
        #print "\n__init__ called!" # FIXME: why can't operator be defined local?

    def _reset_parse_state(self):
        """Clean up state from any previous parse operations."""

        # FIXME: Can this be done away with?  Is parse_query overly stateful?
        self._patterns = []
        self._pattern_beginning = 0
        self._pattern_end = 0
        self._clear_preceding_operator()
        self._clear_following_operator()
        self._inside_parentheses = False

    def _clean_query(self, query):
        """Clean the query performing replacement of AND, OR, NOT operators with their
        equivalents +, |, - """

        # result of the replacement
        result = ""
        current_position = 0

        for match in self._re_quotes_match.finditer(query):
            # clean the content after the previous quotes and before current quotes
            cleanable_content = query[current_position : match.start()]
            cleanable_content = self._clean_operators(cleanable_content)

            # get the content in the quotas
            quoted_content = match.group(0)

            # append the processed content to the result
            result = result + cleanable_content + quoted_content

            # move current position at the end of the processed content
            current_position = match.end()

        # clean the content from the last appearance of quotes till the end of the query
        cleanable_content = query[current_position : len(query)]
        cleanable_content = self._clean_operators(cleanable_content)
        result = result + cleanable_content

        return result

    def _clean_operators(self, query = ""):
        """Replaces some of the content of the query with equivalent content
        (e.g. replace 'AND' operator with '+' operator) for easier processing after that."""

        for word, symbol in (('not', '-'), ('and', '+'), ('or', '|')):
            query = re.sub('(?i)\\b'+word+'\\b', symbol, query)
        return query

    def parse_query(self, query=""):
        """Parses the query and generates as an output a list of values
        containing a sequence of patterns and operators
        [operator1, pattern1, operator2, pattern2, operator3, ..., operatorN, patternN]

        Every pattern is either sequence of search terms and operators
        inside parenthesis or sequence of such terms and operators that are
        outside parenthesis. Operators in the list are these operators that
        are between pattern in parenthesis and pattern that is not in parenthesis"""

        # if the query does not contain parentheses we just return it
        if not self._hasQueryParentheses(query):
            # we add the default operator in front of the query
            return [self._DEFAULT_OPERATOR, query]

        # clean the query replacing some of the content e.g. replace 'AND' with '+'
        query = self._clean_query(query)
        self._query = query

        self._reset_parse_state()
        # flag indicating if we are inside quotes
        inside_quotes = False
        # used for detecting escape sequences. Contains previously processed character.
        previous_character = ""
        # quotes that are recognized
        quotes_symbols = ['"', "'"]
        # contains the quotes symbol when we are between quotes
        current_quotes_symbol = ""

        # iterate through every character in query and perform appropriate action
        for current_index in range(0, len(self._query)):
            character = self._query[current_index]
            # end of the pattern is the current character, which is not included
            self._pattern_end = current_index

            # include all the characters between quotes in the pattern without special processing
            if inside_quotes and character != current_quotes_symbol:
                continue

            # process the quotes if they are not escaped
            if character in quotes_symbols and previous_character != '\\':
                # if we are not inside this should be a beginning of the quotes
                if not inside_quotes:
                    inside_quotes = True
                    current_quotes_symbol = character
                # in case we are inside quotes this is the closing quote
                elif inside_quotes and character == current_quotes_symbol:
                    inside_quotes = False
                    current_quotes_symbol = ""
                #asssign values to operators if necessary
                self._assign_default_values_for_operators_if_necessary()
            elif '(' == character and previous_character != '\\':
                self._handle_open_parenthesis()
            elif ')' == character and previous_character != '\\':
                self._handle_close_parenthesis()
            elif character in self._operators:
                self._handle_operator(current_index)
            else:
                self._handle_non_white_space_characters(current_index)

            # hold the previous character to use it when checking for escape sequences
            previous_character = character

        # as far as patterns are appended when reaching parenthesis we should ensure that we append the last pattern
        self._append_last_pattern()

        # check for mismatched parentheses
        if self._inside_parentheses:
            raise InvenioWebSearchQueryParserException("Mismatched parenthesis.")

        return self._patterns

    def _hasQueryParentheses(self, query=""):
        """Check if the query contain parentheses inside."""
        if -1 != query.find("("):
            return True

        if -1 != query.find(")"):
            return True

        return False

    def _handle_open_parenthesis(self):
        """Process opening parenthesis in the query."""

        # check if we are already inside parentheses
        if self._inside_parentheses:
            raise InvenioWebSearchQueryParserException("Nested parentheses currently unsupported.")

        # both operators preceding and following the pattern before parenthesis
        # are known and also the pattern itself so append them to the result list.
        self._append_preceding_operator()
        self._append_pattern()
        self._append_following_operator()

        # mark that we are inside parenthesis
        self._inside_parentheses = True

        # clear operators because they are already in the result.
        self._clear_preceding_operator()
        self._clear_following_operator()

    def _handle_close_parenthesis(self):
        """Process closing parenthesis in the query."""

        # check if we are inside parentheses
        if not self._inside_parentheses:
            raise InvenioWebSearchQueryParserException("Mismatched parenthesis.")

        # append the pattern between the parentheses
        self._append_pattern()
        # mark that we are not inside parenthesis any more
        self._inside_parentheses = False

    def _handle_operator(self, operator_position):
        """Process operator symbols in the query."""
        if self._inside_parentheses:
            return

        operator = self._query[operator_position]

        # if there is no preceding operator that means that this is the first
        # appearance of an operator after closing parenthesis so we assign
        # the value to the preceding operator
        if self._preceding_operator == "":
            self._preceding_operator = operator
            self._preceding_operator_position = operator_position
            # move the beginning of the patter after the operator
            self._pattern_beginning = operator_position + 1

            # if this is the operator preceding the query, we are not supposed
            # to know the following operator because we are parsing beginning
            self._clear_following_operator()
        # if the preceding operator is assigned then this operator is currently
        # the following operator of the pattern. If there operator after it will replace it
        else:
            self._following_operator = operator
            self._following_operator_position = operator_position

    def _handle_non_white_space_characters(self, character_postition):
        """Process all non white characters that are not operators, quotes
        or parenthesis and are not inside parenthesis or quotes"""

        character = self._query[character_postition]

        # if the character is white space or we are in parentheses we skip processing
        if character.isspace() or self._inside_parentheses:
            return

        self._assign_default_values_for_operators_if_necessary()

    def _assign_default_values_for_operators_if_necessary(self):
        """Assign default values for preceding or following operators if this is necessary."""

        # if the preceding operator is empty that means we are starting to parse a new
        # pattern but there is no operator in front of it. In this case assign default
        # value to preceding operator
        if self._preceding_operator == "":
            self._preceding_operator = self._DEFAULT_OPERATOR
            self._preceding_operator_position = -1
        # otherwise we are now parsing a pattern and can assign current value for following operator
        else:
            # default operator is assigned as a value and will be changed next
            # time operator character is reached
            self._following_operator = self._DEFAULT_OPERATOR
            self._following_operator_position = -1

    def _append_pattern(self):
        """Appends the currently parsed pattern to the list with results"""
        begin = self._calculate_pattern_beginning()
        end = self._calculate_pattern_end()

        current_pattern = self._query[begin : end]
        current_pattern = current_pattern.strip()

        #don't append empty patterns
        if current_pattern != "":
            self._patterns.append(current_pattern)

        # move the beginning of next pattern at the end of current pattern
        self._pattern_beginning = self._pattern_end+1

    def _append_preceding_operator(self):
        """Appends the operator preceding current pattern to the list with results."""
        if self._preceding_operator != "":
            self._patterns.append(self._preceding_operator)
        else:
            self._patterns.append(self._DEFAULT_OPERATOR)

    def _append_following_operator(self):
        """Appends the operator following current pattern to the list with results."""
        if self._following_operator != "":
            self._patterns.append(self._following_operator)

    def _append_last_pattern(self):
        """Appends the last pattern from the query to the list with results.
        Operator preceding this pattern is also appended."""
        self._pattern_end = self._pattern_end+1
        self._append_preceding_operator()
        self._append_pattern()

        # if the last pattern was empty but default preceding operator
        # is appended, then clean it
        if self._patterns[-1] == self._DEFAULT_OPERATOR:
            self._patterns = self._patterns[0 : -1] # remove last element

    def _calculate_pattern_beginning(self):
        """Calculates exact beginning of a pattern taking in mind positions of
        operator proceeding the pattern."""
        # if there is an operator character before the pattern it should not be
        # included in the pattern
        if self._pattern_beginning < self._preceding_operator_position:
            return self._preceding_operator_position + 1

        return self._pattern_beginning

    def _calculate_pattern_end(self):
        """Calculates exact end of a pattern taking in mind positions of
        operator following the pattern."""
        # if there is an operator character after the pattern it should not be
        # included in the pattern
        if self._pattern_end > self._following_operator_position and self._following_operator_position != -1:
            return self._following_operator_position

        return self._pattern_end

    def _clear_preceding_operator(self):
        """Cleans the value of the preceding operator"""
        self._preceding_operator = ""
        # after the value is cleaned the position is also cleaned. We accept -1 for cleaned value.
        self._preceding_operator_position = -1

    def _clear_following_operator(self):
        """Cleans the value of the following operator"""
        self._following_operator = ""
        # after the value is cleaned the position is also cleaned. We accept -1 for cleaned value.
        self._following_operator_position = -1


class InvenioWebSearchQueryParserException(Exception):
    """Exception for parsing errors."""
    def __init__(self, message):
        """Initialization."""
        self.message = message


class SpiresToInvenioSyntaxConverter:
    """Converts queries defined with SPIRES search syntax into queries
    that use Invenio search syntax.
    """

    # Constants defining fields
    _DATE_ADDED_FIELD = '961__x:'
    _DATE_UPDATED_FIELD = '961__c:' # FIXME: define and use dateupdate:
    _DATE_FIELD = '269__c:'

    _A_TAG = 'author:'
    _EA_TAG = 'exactauthor:'


    # Dictionary containing the matches between SPIRES keywords
    # and their corresponding Invenio keywords or fields
    # SPIRES keyword : Invenio keyword or field
    _SPIRES_TO_INVENIO_KEYWORDS_MATCHINGS = {
        # affiliation
        'affiliation' : 'affiliation:',
        'affil' : 'affiliation:',
        'aff' : 'affiliation:',
        'af' : 'affiliation:',
        'institution' : 'affiliation:',
        'inst' : 'affiliation:',
        # any field
        'any' : 'anyfield:',
        # bulletin
        'bb' : 'reportnumber:',
        'bbn' : 'reportnumber:',
        'bull' : 'reportnumber:',
        'bulletin-bd' : 'reportnumber:',
        'bulletin-bd-no' : 'reportnumber:',
        'eprint' : 'reportnumber:',
        # citation / reference
        'c' : 'reference:',
        'citation' : 'reference:',
        'cited' : 'reference:',
        'jour-vol-page' : 'reference:',
        'jvp' : 'reference:',
        # collaboration
        'collaboration' : 'collaboration:',
        'collab-name' : 'collaboration:',
        'cn' : 'collaboration:',
        # conference number
        'conf-number' : '111__g:',
        'cnum' : '111__g:',
        # country
        'cc' : '044__a:',
        'country' : '044__a:',
        # date
        'date': _DATE_FIELD,
        'd': _DATE_FIELD,
        # date added
        'date-added': _DATE_ADDED_FIELD,
        'dadd': _DATE_ADDED_FIELD,
        'da': _DATE_ADDED_FIELD,
        # date updated
        'date-updated': _DATE_UPDATED_FIELD,
        'dupd': _DATE_UPDATED_FIELD,
        'du': _DATE_UPDATED_FIELD,
        # first author
        'fa' : '100__a:',
        'first-author' : '100__a:',
        # author
        'a' : 'author:',
        'au' : 'author:',
        'author' : 'author:',
        'name' : 'author:',
        # exact author
        # this is not a real keyword match. It is pseudo keyword that
        # will be replaced later with author search
        'ea' : 'exactauthor:',
        'exact-author' : 'exactauthor:',
        # experiment
        'exp' : 'experiment:',
        'experiment' : 'experiment:',
        'expno' : 'experiment:',
        'sd' : 'experiment:',
        'se' : 'experiment:',
        # journal
        'journal' : 'journal:',
        'j' : 'journal:',
        'published_in' : 'journal:',
        'spicite' : 'journal:',
        'vol' : 'journal:',
        # journal page
        'journal-page' : '773__c:',
        'jp' : '773__c:',
        # journal year
        'journal-year' : '773__y:',
        'jy' : '773__y:',
        # key
        'key' : '970__a:',
        'irn' : '970__a:',
        'record' : '970__a:',
        'document' : '970__a:',
        'documents' : '970__a:',
        # keywords
        'k' : 'keyword:',
        'keywords' : 'keyword:',
        # note
        'note' : '500__a:',
        'n' : '500__a:',
        # old title
        'old-title' : '246__a:',
        'old-t' : '246__a:',
        'ex-ti' : '246__a:',
        'et' : '246__a:',
        # ppf subject
        'ppf-subject' : '650__a:',
        'ps' : '650__a:',
        'scl' : '650__a:',
        'status' : '650__a:',
        # report number
        'r' : 'reportnumber:',
        'rn' : 'reportnumber:',
        'rept' : 'reportnumber:',
        'report' : 'reportnumber:',
        'report-num' : 'reportnumber:',
        # title
        't' : 'title:',
        'ti' : 'title:',
        'title' : 'title:',
        'with-language' : 'title:',
        # topic
        'topic' : '653__a:',
        'tp' : '653__a:',
        'hep-topic' : '653__a:',
        'desy-keyword' : '653__a:',
        'dk' : '653__a:',
        # replace all the keywords without match with empty string
        # this will remove the noise from the unknown keywrds in the search
        # and will in all fields for the words following the keywords


        # category
        'arx' : '037__c:',
        'category' : '037__c:',
        # primarch
        'parx' : '037__c:',
        'primarch' : '037__c:',
        # texkey
        'texkey' : '035__z:',
        # type code
        'tc' : '690C_a:',
        'ty' : '690C_a:',
        'type' : '690C_a:',
        'type-code' : '690C_a',
        # field code
        'f' : '65017a:',
        'fc' : '65017a:',
        'field' : '65017a:',
        'field-code' : '65017a:',
        # coden
        'bc' : '',
        'browse-only-indx' : '',
        'coden' : '',
        'journal-coden' : '',
        # energy
        'e' : '',
        'energy' : '',
        'energyrange-code' : '',
        # exact experiment number
        'ee' : '',
        'exact-exp' : '',
        'exact-expno' : '',
        # hidden note
        'hidden-note' : '',
        'hn' : '',
        # ppf
        'ppf' : '',
        'ppflist' : '',
        # slac topics
        'ppfa' : '',
        'slac-topics' : '',
        'special-topics' : '',
        'stp' : '',
        # test index
        'test' : '',
        'testindex' : '',
        }

    def __init__(self):
        """Initialize the state of the converter"""
        self._init_months()
        self._compile_regular_expressions()

    def _compile_regular_expressions(self):
        """Compiles some of the regular expressions that are used in the class
        for higher performance."""

        # regular expression that matches the contents in single and double quotes
        # taking in mind if they are escaped.
        self._re_quotes_match = re.compile('[^\\\\](".*?[^\\\\]")|[^\\\\](\'.*?[^\\\\]\')')

        # for matching cases where kw needs distributing
        self._re_distribute_keywords = re.compile(r'\b(?P<keyword>\S*:)(?P<content>.+?)\s*(?P<combination>and not | and | or | not )\s*(?P<last_content>[^:]*?)(?= and not | and | or | not |$)', re.IGNORECASE)

        # regular expression that matches author patterns
        self._re_author_match = re.compile(r'\bauthor:\s*(?P<name>.+?)\s*(?= and not | and | or | not |$)', re.IGNORECASE)

        # regular expression that matches exact author patterns
        # the group defined in this regular expression is used in method
        # _convert_spires_exact_author_search_to_invenio_author_search(...)
        # in case of changes correct also the code in this method
        self._re_exact_author_match = re.compile(r'\bexactauthor:(?P<author_name>[^\'\"].*?[^\'\"]\b)(?= and not | and | or | not |$)', re.IGNORECASE)

        # regular expression that matches search term, its conent (words that
        # are searched)and the operator preceding the term. In case that the
        # names of the groups defined in the expression are changed, the
        # chagned should be reflected in the code that use it.
        self._re_search_term_pattern_match = re.compile(r'\b(?P<combine_operator>find|and|or|not)\s+(?P<search_term>title:|keyword:)(?P<search_content>.*?(\b|\'|\"|\/))(?= and | or | not |$)', re.IGNORECASE)

        # regular expression used to split string by white space as separator
        self._re_split_pattern = re.compile(r'\s*')

        # regular expression matching date after pattern
        self._re_date_after_match = re.compile(r'\b(d|date)\b\s*(after|>)\s*(?P<year>\d{4})\b', re.IGNORECASE)

        # regular expression matching date after pattern
        self._re_date_before_match = re.compile(r'\b(d|date)\b\s*(before|<)\s*(?P<year>\d{4})\b', re.IGNORECASE)

        # regular expression matching dates in general
        self._re_dates_match = self._compile_dates_regular_expression()

        # for finding (and changing) a variety of different SPIRES search keywords
        self._re_find_or_fin_at_start = re.compile('^find? .*$')

        # patterns for subbing out spaces within quotes temporarily
        self._re_pattern_single_quotes = re.compile("'(.*?)'")
        self._re_pattern_double_quotes = re.compile("\"(.*?)\"")
        self._re_pattern_regexp_quotes = re.compile("\/(.*?)\/")
        self._re_pattern_space = re.compile("__SPACE__")
        self._re_pattern_IRN_search = re.compile(r'970__a:(?P<irn>\d+)')

    def convert_query(self, query):
        """Converts the query from SPIRES syntax to Invenio syntax

        Queries are assumed SPIRES queries only if they start with FIND or FIN"""

        # allow users to use "f" only...
        query = re.sub('^[fF] ', 'find ', query)

        # SPIRES syntax allows searches with 'find' or 'fin'.
        if self._re_find_or_fin_at_start.match(query.lower()):

            # Everywhere else make the assumption that all and only queries
            # starting with 'find' are SPIRES queries.  Turn fin into find.
            query = re.sub('^[fF][iI][nN] ', 'find ', query)

            # these calls are before keywords replacement becuase when keywords
            # are replaced, date keyword is replaced by specific field search
            # and the DATE keyword is not match in DATE BEFORE or DATE AFTER
            query = self._convert_spires_date_before_to_invenio_span_query(query)
            query = self._convert_spires_date_after_to_invenio_span_query(query)

            # call to _replace_spires_keywords_with_invenio_keywords should be at the
            # beginning because the next methods use the result of the replacement
            query = self._replace_spires_keywords_with_invenio_keywords(query)
            query = self._distribute_keywords_across_combinations(query)

            query = self._convert_dates(query)
            query = self._convert_irns_to_spires_irns(query)
            query = self._convert_spires_author_search_to_invenio_author_search(query)
            query = self._convert_spires_exact_author_search_to_invenio_author_search(query)
            query = self._convert_spires_truncation_to_invenio_truncation(query)
            query = self._expand_search_patterns(query)

            # remove FIND in the beginning of the query as it is not necessary in Invenio
            query = query[4:]
            query = query.strip()

        return query

    def _init_months(self):
        """Defines a dictionary matching the name
        of the month with its corresponding number"""

        # this dictionary is used when generating match patterns for months
        self._months = {'jan':'01', 'january':'01',
                         'feb':'02', 'february':'02',
                         'mar':'03', 'march':'03',
                         'apr':'04', 'april':'04',
                         'may':'05', 'may':'05',
                         'jun':'06', 'june':'06',
                         'jul':'07', 'july':'07',
                         'aug':'08', 'august':'08',
                         'sep':'09', 'september':'09',
                         'oct':'10', 'october':'10',
                         'nov':'11', 'november':'11',
                         'dec':'12', 'december':'12'}
        # this dicrionary is used to transform name of the month
        # to a number used in the date format. By this reason it
        # contains also the numbers itself to simplify the conversion
        self._month_name_to_month_number = {'1':'01', '01':'01',
                                            '2':'02', '02':'02',
                                            '3':'03', '03':'03',
                                            '4':'04', '04':'04',
                                            '5':'05', '05':'05',
                                            '6':'06', '06':'06',
                                            '7':'07', '07':'07',
                                            '8':'08', '08':'08',
                                            '9':'09', '09':'09',
                                            '10':'10',
                                            '11':'11',
                                            '12':'12',}
        # combine it with months in order to cover all the cases
        self._month_name_to_month_number.update(self._months)

    def _get_month_names_match(self):
        """Retruns part of a patter that matches month in a date"""

        months_match = ''
        for month_name in self._months.keys():
            months_match = months_match + month_name + '|'

        months_match = r'\b(' + months_match[0:-1] + r')\b'

        return months_match

    def _get_month_number(self, month_name):
        """Returns the corresponding number for a given month
        e.g. for February it returns 02"""

        return self._month_name_to_month_number[month_name.lower()]

    def _compile_dates_regular_expression(self):
        """ Returns compiled regular expression matching dates in general that follow particular keywords"""

        date_preceding_terms_match = r'\b((?<=' + \
                    self._DATE_ADDED_FIELD +')|(?<=' + \
                    self._DATE_UPDATED_FIELD + ')|(?<=' + \
                    self._DATE_FIELD +'))'
        day_match = r'\b(0?[1-9]|[12][0-9]|3[01])\b'
        month_match = r'\b(0?[1-9]|1[012])\b'
        month_names_match = self._get_month_names_match()
        year_match = r'\b([1-9][0-9]?)?[0-9]{2}\b'
        date_separator_match = r'(\s+|\s*[,/\-\.]\s*)'

        dates_re = date_preceding_terms_match + r'\s*' + \
            r'(((((?P<day>' + day_match + r')' + date_separator_match + ')?' + \
            r'(?P<month>' + month_match + r'|' + month_names_match + r'))' + \
            r'|' + \
            r'((?P<month2>' + month_names_match + r')' + date_separator_match + \
            r'(?P<day2>' + day_match + r')))' + \
            date_separator_match + r')?' + \
            r'(?P<year>' + year_match + r')'

        return re.compile(dates_re, re.IGNORECASE)

    def _convert_dates(self, query):
        """Converts dates in the query in format expected from invenio"""

        def create_replacement_pattern(match):
            """method used for replacement with regular expression"""

            QUOTES = '"'

            # retrieve the year
            year = match.group('year')
            # in case only last two digits are provided, consider it is 19xx
            if len(year) == 2:
                year = '19' + year

            # retrieve the month
            month_name = match.group('month')
            if None == month_name:
                month_name =  match.group('month2')

            # if there is no month, look for everything in given year
            if None == month_name:
                return QUOTES + year + '*' + QUOTES

            month = self._get_month_number(month_name)

            # retrieve the day
            day = match.group('day')
            if None == day:
                day = match.group('day2')

            # if day is missing, look for everything in geven year and month
            if None == day:
                return QUOTES + year + '-' + month + '-*' + QUOTES

            if len(day) == 1:
                day = '0'+day

            return   QUOTES + year + '-' + month + '-' + day + QUOTES

        query = self._re_dates_match.sub(create_replacement_pattern, query)

        return query

    def _convert_irns_to_spires_irns(self, query):
        """Prefix IRN numbers with SPIRES- so they match the INSPIRE format."""
        def create_replacement_pattern(match):
            """method used for replacement with regular expression"""
            return '970__a:SPIRES-' + match.group('irn')
        query = self._re_pattern_IRN_search.sub(create_replacement_pattern, query)
        return query

    def _convert_spires_date_after_to_invenio_span_query(self, query):
        """Converts date after SPIRES search term into invenio span query"""

        def create_replacement_pattern(match):
            """method used for replacement with regular expression"""
            return 'year:' + match.group('year') + '->9999'

        query = self._re_date_after_match.sub(create_replacement_pattern, query)

        return query

    def _convert_spires_date_before_to_invenio_span_query(self, query):
        """Converts date before SPIRES search term into invenio span query"""

        # method used for replacement with regular expression
        def create_replacement_pattern(match):
            return 'year:' + '0->' + match.group('year')

        query = self._re_date_before_match.sub(create_replacement_pattern, query)

        return query

    def _expand_search_patterns(self, query):
        """Expands search queries.

        If a search term is followed by several words e.g.
        author: ellis or title:THESE THREE WORDS it is exoanded to
        author:ellis or (title: THESE and title:THREE...)


        For a combining operator "and" is used though FIXME this is not
        correct, it should really be calculated by boolean expansion of parens.


        Not all the search terms are expanded this way, but only a short
        list of them"""

        def create_replacement_pattern(match):
            result = ''
            search_term = match.group('search_term')
            combine_operator = match.group('combine_operator')
            search_content = match.group('search_content').strip()


            # replace spaces within quotes by __SPACE__ temporarily:
            search_content = self._re_pattern_single_quotes.sub(lambda x: "'"+string.replace(x.group(1), ' ', '__SPACE__')+"'", search_content)
            search_content = self._re_pattern_double_quotes.sub(lambda x: "\""+string.replace(x.group(1), ' ', '__SPACE__')+"\"", search_content)
            search_content = self._re_pattern_regexp_quotes.sub(lambda x: "/"+string.replace(x.group(1), ' ', '__SPACE__')+"/", search_content)

            words = self._re_split_pattern.split(search_content)
            if len(words) > 1:
                #FIXME this will break if it happens to be nested.
                result = combine_operator + ' (' + search_term + words[0]
                for word in words[1:]:
                    result =  result + ' and ' + search_term + word
                result = result + ') '
            else:
                result = combine_operator + ' ' + search_term + words[0]
            # replace back __SPACE__ by spaces:
            result = self._re_pattern_space.sub(" ", result)
            return result.strip()

        query = self._re_search_term_pattern_match.sub(create_replacement_pattern, query)
        return query

    def _convert_spires_truncation_to_invenio_truncation(self, query):
        """Replace SPIRES truncation symbol # with invenio trancation symbol *"""
        return query.replace('#', '*')

    def _convert_spires_exact_author_search_to_invenio_author_search(self, query):
        """Converts SPIRES search patterns for exact author into search pattern
        for invenio"""

        # method used for replacement with regular expression
        def create_replacement_pattern(match):
            # the regular expression where this group name is defined is in
            # the method _compile_regular_expressions()
            return self._EA_TAG + '"' + match.group('author_name') + '"'

        query = self._re_exact_author_match.sub(create_replacement_pattern, query)

        return query

    def _convert_spires_author_search_to_invenio_author_search(self, query):
        """Converts SPIRES search patterns for authors to search patterns in invenio
        that give similar results to the spires search.
        """

        # result of the replacement
        result = ''
        current_position = 0
        for match in self._re_author_match.finditer(query):
            result += query[current_position : match.start() ]
            scanned_name = NameScanner.scan(match.group('name'))
            author_atoms = self._create_author_search_pattern_from_fuzzy_name_dict(scanned_name)
            if author_atoms.find(' ') == -1:
                result += author_atoms + ' '
            else:
                result += '(' + author_atoms + ') '
            current_position = match.end()
        result += query[current_position : len(query)]
        return result

    def _create_author_search_pattern_from_fuzzy_name_dict(self, fuzzy_name):
        """Creates an invenio search pattern for an author from a fuzzy name dict"""

        author_name = ''
        author_middle_name = ''
        author_surname = ''
        if len(fuzzy_name['nonlastnames']) > 0:
            author_name = fuzzy_name['nonlastnames'][0]
        if len(fuzzy_name['nonlastnames']) == 2:
            author_middle_name = fuzzy_name['nonlastnames'][1]
        if len(fuzzy_name['nonlastnames']) > 2:
            author_middle_name = ' '.join(fuzzy_name['nonlastnames'][1:])
        author_surname = ' '.join(fuzzy_name['lastnames'])

        NAME_IS_INITIAL = (len(author_name) == 1)
        NAME_IS_NOT_INITIAL = not NAME_IS_INITIAL

        # we expect to have at least surname
        if author_surname == '' or author_surname == None:
            return ''

        # ellis ---> "author:ellis"
        #if author_name == '' or author_name == None:
        if not author_name:
            return self._A_TAG + author_surname

        # ellis, j ---> "ellis, j*"
        if NAME_IS_INITIAL and not author_middle_name:
            return self._A_TAG + '"' + author_surname + ', ' + author_name + '*"'

        # if there is middle name we expect to have also name and surname
        # ellis, j. r. ---> ellis, j* r*
        # j r ellis ---> ellis, j* r*
        # ellis, john r. ---> ellis, j* r* or ellis, j. r. or ellis, jo. r.
        # ellis, john r. ---> author:ellis, j* r* or exactauthor:ellis, j r or exactauthor:ellis jo r
        if author_middle_name:
            search_pattern = self._A_TAG + '"' + author_surname + ', ' + author_name + '*' + ' ' + author_middle_name.replace(" ","* ") + '*"'
            if NAME_IS_NOT_INITIAL:
                for i in range(1,len(author_name)):
                    search_pattern += ' or ' + self._EA_TAG + "\"%s, %s %s\"" % (author_surname, author_name[0:i], author_middle_name)
            return search_pattern

        # ellis, jacqueline ---> "ellis, jacqueline" or "ellis, j.*" or "ellis, j" or "ellis, ja.*" or "ellis, ja" or "ellis, jacqueline *"
        # in case we don't use SPIRES data, the ending dot is ommited.
        search_pattern = self._A_TAG + '"' + author_surname + ', ' + author_name + '*"'
        if NAME_IS_NOT_INITIAL:
            for i in range(1,len(author_name)):
                search_pattern += ' or ' + self._EA_TAG + "\"%s, %s\"" % (author_surname, author_name[0:i])

        return search_pattern


    def _replace_spires_keywords_with_invenio_keywords(self, query):
        """Replaces SPIRES keywords that have directly
        corresponding Invenio keywords

        Replacements are done only in content that is not in quotes."""

        # result of the replacement
        result = ""
        current_position = 0

        for match in self._re_quotes_match.finditer(query):
            # clean the content after the previous quotes and before current quotes
            cleanable_content = query[current_position : match.start()]
            cleanable_content = self._replace_all_spires_keywords_in_string(cleanable_content)

            # get the content in the quotes (group one matches double
            # quotes, group 2 singles)
            if match.group(1):
                quoted_content = match.group(1)
            elif match.group(2):
                quoted_content = match.group(2)

            # append the processed content to the result
            result = result + cleanable_content + quoted_content

            # move current position at the end of the processed content
            current_position = match.end()

        # clean the content from the last appearance of quotes till the end of the query
        cleanable_content = query[current_position : len(query)]
        cleanable_content = self._replace_all_spires_keywords_in_string(cleanable_content)
        result = result + cleanable_content

        return result

    def _replace_all_spires_keywords_in_string(self, query):
        """Replaces all SPIRES keywords in the string with their
        corresponding Invenio keywords"""

        for spires_keyword, invenio_keyword in self._SPIRES_TO_INVENIO_KEYWORDS_MATCHINGS.iteritems():
            query = self._replace_keyword(query, spires_keyword,\
                                          invenio_keyword)

        return query

    def _replace_keyword(self, query, old_keyword, new_keyword):
        """Replaces old keyword in the query with a new keyword"""
        # perform case insensitive replacement with regular expression

        regex_string = r'\b(?P<operator>(find|and|or|not)\b[\s\(]*)' + \
                       old_keyword + r'(?P<end>[\s\(]+|$)'
        regular_expression = re.compile(regex_string, re.IGNORECASE)
        result = regular_expression.sub(r'\g<operator>' + new_keyword + r'\g<end>', query)
        result = re.sub(':\s+', ':', result)
        return result

    def _distribute_keywords_across_combinations(self, query):
        # method used for replacement with regular expression

        def create_replacement_pattern(match):
            # the regular expression where this group name is defined is in
            # the method _compile_regular_expressions()
            return match.group('keyword') + match.group('content') + \
                   ' ' +  match.group('combination') + ' ' + match.group('keyword') + \
                   match.group('last_content')

        query = self._re_distribute_keywords.sub(create_replacement_pattern, query)
        return query
