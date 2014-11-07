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

define([], function() {

  var QueryGenerator = {};

  /**
   * Concatenates query words with a logical operator.
   * Wraps the result in parentheses.
   *
   * @param {Array} filters_array array of query words
   * @param {String} logical_operator logical operator to use
   * @param {boolean} add_parentheses if true,
   *  adds parentheses when there are more than one filter item
   *
   * @returns {String} the processed string
   */
  QueryGenerator.merge = function(queriesArray, operator) {
    if (queriesArray.length === 0)
      return '';

    // clean array from empty values
    queriesArray = queriesArray.filter(Boolean);

    var str = queriesArray.join(' ' + operator + ' ');
    return str;
  };

  /**
   * Generates query in invenio format
   *
   * @param {{
   *  area: {
   *    '+': {Array},
   *    '-': {Array}
   *  },
   *  area2: {
   *    '+': {Array},
   *    '-': {Array}
   *  }
   * }} queryData
   * @param {boolean} add_parentheses_if_necessary if set to true,
   *  adds parentheses when there is more than one word to easyli connect
   *  with another part using a logical operator.
   * @returns {string} invenio query
   */
  QueryGenerator.generateQuery = function(queryData, add_parentheses_if_necessary) {
    var box_queries = [];
    var between_boxes_operator = 'AND';
    var words_counter;

    var boxes_number = Object.keys(queryData).length;
    // add_parentheses_if_necessary means that there is one more part of the
    // query. Logically increasing boxes_number simulates the situation.
    if (add_parentheses_if_necessary) {
      boxes_number++;
    }

    for (var area in queryData) {

      words_counter = 0;

      var areaQuery = queryData[area];

      var limit_to_filters = [];
      var exclude_filters = [];

      for (var idx in areaQuery['+']) {
        limit_to_filters.push(area + ':' + bracketStr(areaQuery['+'][idx]))
      }

      for (var idx in areaQuery['-']) {
        exclude_filters.push(area + ':' + bracketStr(areaQuery['-'][idx]))
      }

      var limit_to_part = QueryGenerator.merge(limit_to_filters, 'OR');
      var exclude_part = QueryGenerator.merge(exclude_filters, 'OR');

      // add parentheses to both parts if there are two of them
      // or there is one only but there are more filters than one
      var do_both_parts_exist = limit_to_filters.length &&
        exclude_filters.length;
      if (limit_to_filters.length > 1 &&
          (boxes_number > 1 || do_both_parts_exist)) {
        limit_to_part = addParentheses(limit_to_part);
      }
      // here parentheses need to be added anyway, because of NOT keyword
      if (exclude_filters.length > 1) {
        exclude_part = addParentheses(exclude_part);
      }

      var box_query = limit_to_part;
      if (limit_to_part && exclude_part)
        box_query += ' AND ';
      if (exclude_part)
        box_query += 'NOT ' + exclude_part;

      if (do_both_parts_exist && boxes_number > 1) {
        box_query = addParentheses(box_query);
      }

      if (box_query)
        box_queries.push(box_query);
    }

    // add parentheses if there are at least two boxes and the parameter is
    // set adequately
    var query = QueryGenerator.merge(box_queries, between_boxes_operator);
    if (box_queries.length > 1 && add_parentheses_if_necessary) {
      query = addParentheses(query);
    }

    return query;

    function addParentheses(str) {
      if (!str)
        return str;
      return '(' + str + ')';
    }

    /**
     * str -> "str" if str has spaces inside
     * @param str
     * @returns {String}
     */
    function bracketStr(str) {
      if (str.indexOf(' ') == -1)
        return str;
      if (str[0] !== '\"')
        str = '"' + str;
      if (str[str.length - 1] !== '\"')
        str = str + '"';
      return str;
    }
  };

  return QueryGenerator;

});
