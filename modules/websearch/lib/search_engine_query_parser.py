# -*- coding: utf-8 -*-
## $Id$

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

# pylint: disable-msg=C0301

"""CDS Invenio Search Engine query parsers."""

__lastupdated__ = """$Date$"""

__revision__ = "$Id$"

import re

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

    # string containing the query that will be parsed
    _query = ""
    # operators before and after the current pattern matched during parsing
    _preceding_operator = ""
    _preceding_operator_position = -1

    _following_operator = ""
    _following_operator_position = -1
    # indexes in the parsed query of beginning and end of currently parsed pattern
    _pattern_beginning = 0
    _pattern_end = 0
    # list of parsed patterns and operators
    _patterns = []
    # flag indicating if processed symbols are inside parenthesis
    _inside_parentheses = False
    # all operator symbols recognized in expression
    _operators = ['+', '|', '-']
    # default operator if operator is missing between patterns
    _DEFAULT_OPERATOR = '+'

    # error messages
    _error_message_mismatched_parentheses = "Mismatched parenthesis."
    _error_message_nested_parentheses_not_supported = "Nested parenthesis are currently not supported."

    def __init__(self):
        """Initialize the state of the parser"""
        self._init_parsing()

    def _init_parsing(self, query=""):
        """Initialize variables before parsing """

        # clean the query replacing some of the content e.g. replace 'AND' with '+'
        query = self._clean_query(query)
        self._query = query

        self._patterns = []
        self._pattern_beginning = 0
        self._pattern_end = 0

        self._clear_preceding_operator()
        self._clear_following_operator()

        self._inside_parentheses = False

    def _clean_query(self, query):
        """Clean the query performing replacement of AND, OR, NOT operators with their
        equivalents +, |, - """

        # regular expression that matches the contents in single and double quotes
        # taking in mind if they are escaped.
        # if this became bottleneck at some moment, the compilation of the expression
        # can be moved outside in order to be compiled only once.
        re_quotes_match = re.compile('[^\\\\](".*?[^\\\\]")|[^\\\\](\'.*?[^\\\\]\')')

        # result of the replacement
        result = ""
        current_position = 0

        for match in re_quotes_match.finditer(query):
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

        # replace first the appearances of AND NOT, and after that appearances of NOT
        query = self._replace_word_case_insensitive(query, "and not", "-")
        # the order here does matter. Replacement of AND should be after replacement of AND NOT
        query = self._replace_word_case_insensitive(query, "and", "+")
        query = self._replace_word_case_insensitive(query, "or", "|")

        return query

    def _replace_word_case_insensitive(self, str, old_word, new_word):
        """Returns a copy of string str where all occurrences of old_word
        are replaced by new_word"""

        regular_expression = re.compile('\\b'+old_word+'\\b', re.IGNORECASE)

        result = regular_expression.sub(new_word, str)

        return result

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

        self._init_parsing(query)
        # all operator symbols recognized in expression
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
                # if we are not inside this should be a begining of the quotes
                if not inside_quotes:
                    inside_quotes = True
                    current_quotes_symbol = character
                    self._assign_default_values_for_operators_if_necessary()
                # in case we are insede quotes this is the closing quote
                elif inside_quotes and character == current_quotes_symbol:
                    inside_quotes = False
                    current_quotes_symbol = ""
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
            self._raise_error(self._error_message_mismatched_parentheses)

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
            self._raise_error(self._error_message_nested_parentheses_not_supported)

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
            self._raise_error(self._error_message_mismatched_parentheses)

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
        else :
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

    def _raise_error(self, error_message_text):
        """Raises an exception with the specified error message"""
        raise InvenioWebSearchQueryParserException(error_message_text)

class InvenioWebSearchQueryParserException(Exception):
    """Exception for bad collection."""
    def __init__(self, message):
        """Initialization."""
        self.message = message