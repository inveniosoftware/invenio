/*
 * This file is part of Invenio.
 * Copyright (C) 2014 CERN.
 *
 * Invenio is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 2 of the
 * License, or (at your option) any later version.
 *
 * Invenio is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Invenio; if not, write to the Free Software Foundation, Inc.,
 * 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
 */

/**
  * Generates configuration of invenio syntax for search field typeahead
  *
  * @method getInvenioParserConf
  * @param {Array of strings} Contains values of possible query type
  *  keywords as 'author', 'abstract' etc.
  */
define([], function() {
  return function (area_keywords) {

    var get_next_word_type = function(previous_word_type, word_types) {
      // returns the next type according to syntax order

      // the case when this is the first word
      if (previous_word_type == undefined)
        return [word_types.QUERY_TYPE, word_types.NOT];

      if (previous_word_type == word_types.QUERY_TYPE)
        return word_types.QUERY_VALUE;

      if (previous_word_type == word_types.QUERY_VALUE)
        return [word_types.QUERY_TYPE, word_types.LOGICAL_EXP, word_types.NOT]

      if (previous_word_type == word_types.LOGICAL_EXP)
        return [word_types.QUERY_TYPE, word_types.NOT];

      if (previous_word_type == word_types.NOT)
        return word_types.QUERY_TYPE;
    }

    function endsWithColon(str, char_roles, start_idx, end_idx) {
      return str[end_idx] == ':';
    }

    function notStartsNorEndsWithColon(str, char_roles, start_idx, end_idx) {
      return !endsWithColon(str, char_roles, start_idx, end_idx)
        && !(start_idx > 0 && str[start_idx - 1] == ':');
    }

    var invenio_syntax = {
      keywords: {
        SEARCH: {
          LOGICAL_EXP: {
            min_length: 1,
            values: ['AND', 'OR'],
            detection_condition: notStartsNorEndsWithColon,
            autocomplete_suffix: ' '
          },
          NOT: {
            min_length: 1,
            values: ['NOT'],
            detection_condition: notStartsNorEndsWithColon,
            autocomplete_suffix: ' '
          }
        },
        ORDER: {
          QUERY_TYPE: {
            min_length: 1,
            detection_condition: endsWithColon,
            values: area_keywords,
            autocomplete_suffix: ':'
          },
          QUERY_VALUE: {
            min_length: 3,
            terminating_separators: [' ']
          }
        }
      },
      get_next_word_type: get_next_word_type,
      value_type_interpretation: {
        author: 'exactauthor'
      },
      separators: [' ', ':', '(', ')']
    };

    return {
      invenio: invenio_syntax,
    };
  }
});
