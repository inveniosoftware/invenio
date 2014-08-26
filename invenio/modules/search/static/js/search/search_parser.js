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

/*
DOCUMENTATION

To be used with modules/search/typeahead.js script.
The above script contains also the documentation

 */

// enables printing the parse results to the console
var DEBUG = false;

define([
  'jquery',
], function ($) {

  function SearchParser(options, default_set_name) {

    // stores the role to which every character belongs
    // as one of 'char_roles_enum' values
    this.char_roles = [];

    // stores the analysed string
    this.str = '';

    // there can be a couple of parsing schemas switched even by keywords
    this.options_sets = options;
    this.default_options_set = default_set_name;

    this._setOptions(this.default_options_set);

    // here you can add other parsing methods
    this.methods = {
      SEARCH: this._findBySearch
    }
  }

  SearchParser.prototype = {

    /**
     * Finds all quotation mark sequences until the limit index.
     *
     * @param limit_idx the limit index
     * @returns {Array} array of objects:
     *  begin: begin index
     *  end: end index
     * @private
     */
    _findQuotationMarks: function(limit_idx) {

      var quotation_mark_indices = [];

      var str = this.str.slice(0, limit_idx);

      var current_index = 0, begin_idx, end_idx;
      while(true) {
        begin_idx = str.indexOf('"', current_index);
        end_idx = str.indexOf('"', begin_idx + 1);
        quotation_mark_indices.push({
          begin: begin_idx,
          end: end_idx
        });
        if (begin_idx == -1 || end_idx == -1)
          break;
        current_index = end_idx + 1;
      }

      var last_element = quotation_mark_indices[quotation_mark_indices.length - 1];
      if (last_element.begin == -1)
        quotation_mark_indices.pop();

      return quotation_mark_indices;
    },

    /**
     * Returns the next word type according to get_next_word_type
     * configuration parameter
     *
     * @param previous_word_type the previous word, if no previous word
     *  undefined should be passed
     * @param is_full_word is the word fully typed or there is just a part
     *  of it typed
     * @returns {String} word type from this.word_types enum
     * @private
     */
    _getNextWordType: function(previous_word_type, is_full_word) {

      var word_types = this.get_next_word_type(
        previous_word_type, this.word_types)
      if (!is_full_word)
        return word_types;

      // types of full words are chosen only from the types detected
      // by order analysis - not SEARCH method

      var i = 0;
      while (i < word_types.length) {
        if (word_types[i] in this.keywords.SEARCH)
          // delete type
          word_types.splice(i, i);
        else
          i++;
      }
      if (word_types.length == 1)
        word_types = word_types.pop();
      return word_types;
    },

    /**
     * Changes currently used options set
     *
     * @param set_name
     */
    setOptions: function(set_name) {
      this._setOptions(set_name);
    },

    /**
     * Initialize options set
     *
     * @param options options set
     * @returns the set after the initialization
     * @private
     */
    _initializeOptions: function(options) {
      options.word_types = {};
      for (var method_key in options.keywords) {
        var method = options.keywords[method_key];
        for (var word_type in method) {
          var conf = method[word_type];
          options.word_types[word_type] = word_type;
          if (method_key == 'SEARCH') {
            conf.sorted_values = conf.values.slice(0).sort(sortByLength);
          }
        }
      }

      // kind of enum :) with possible values in char_roles array
      options.char_roles_enum = {
        // characters separating expressions and logical connectors
        SEPARATOR: 'SEPARATOR'
      };
      $.extend(options.char_roles_enum, options.word_types);

      options.initialized = true;

      return options;

      function sortByLength(a, b) {
        return b.length - a.length;
      }
    },

    /**
     * Resets to the default option set - internal function
     *
     * @private
     */
    _setOptions: function(set_name) {

      var options = this.options_sets[set_name];

      this.current_options_set = set_name;

      if (!options.initialized)
        this.options_sets[set_name] = options = this._initializeOptions(options);

      this.keywords = options.keywords;
      this.keywords_flat = options.keywords_flat;
      this.separators = options.separators;
      this.char_roles_enum = options.char_roles_enum;
      this.word_types = options.word_types;
      this.get_next_word_type = options.get_next_word_type;
      this.value_type_interpretation = options.value_type_interpretation;
    },

    /**
     * Resets to the default option set
     */
    resetOptions: function() {
      this._setOptions(this.default_options_set);
    },

    /**
     * Gets the name (key) of the currently chosen options set
     *
     * @returns {*}
     */
    getOptionsSetName: function() {
      return this.current_options_set;
    },

    /**
     * Checks if the character under the index is a part
     * of an autocomplete word.
     *
     * Returns false also when the word has not been analysed by the parser yet.
     *
     * @param idx index of the checked character
     * @returns {boolean}
     * @private
     */
    _isWordPart: function(idx) {
      return !!this.char_roles[idx] && !this._isSeparator(idx);
    },

    /**
     * Finds the indices range in string which is going
     * to be substituted uses the current caret index to
     * as reference point of the place the query is written
     * The returned range includes quotation marks if they
     * exist at the beginning or end of the query value
     *
     * @param caretIdx
     * @returns {{start: number, end: number}} A dictionary
     *  with start index and end index
     */
    getQueryRangeIdx: function(caretIdx) {
      var idx = caretIdx - 1;
      var start, end;
      // by default model type is undefined
      var model;

      // if the character at idx was not analysed yet model type stays undefined
      if (this._isWordPart(idx))
        model = this.char_roles[idx];

      while (idx >= 0 && this.char_roles[idx] == model)
        idx--;

      start = idx + 1;

      end = caretIdx;

      // if the query is only just one typed char
      // don't involve the word after it
      if (caretIdx - start > 1) {
        while (end < this.str.length && this.char_roles[end] == model)
          end++;
      }

      return {
        start: start,
        end: end
      }
    },

    /**
     * Checks if the character at the index idx is a separator
     * @param idx character index
     * @returns {boolean} decision result
     * @private
     */
    _isSeparator: function(idx) {
      var role = this.char_roles[idx];
      if (role) // look at interpretation
        return role == this.char_roles_enum.SEPARATOR;
      else // no interpretation - use raw data
        return this.separators.indexOf(this.str[idx]) > -1;
    },

    /**
     * Finds the autocomplete query with its type and eventually
     * the type identifier for remote queries
     *
     * @param query_beginning
     * @param caretPos
     * @returns {*}
     */
    getAutocompleteQuery: function(query_beginning, caretPos) {

      var query = this.str.slice(query_beginning, caretPos);
      var idx = query_beginning - 1;

      // check if before the query there is a separator
      if (idx >= 0 && this.char_roles[idx] != this.char_roles[query_beginning] &&
        !this._isSeparator(idx)) {
        return  {
          value: query,
          type: undefined
        }
      } else {
        idx--;
      }

      // jump over more separators
      while (!this._isWordPart(idx) && idx >= 0 || this.str[idx] == '"') {
        idx--;
      }

      var previous_word_type = this.char_roles[idx];
      // the word is currently autocompleted - cannot be full
      var isWordFull = false;
      var autocomplete_type = this._getNextWordType(previous_word_type, isWordFull);

      query = removeQuotationMarks(query);

      var result = {
        value: query,
        type: autocomplete_type
      };

      if (autocomplete_type == this.word_types.QUERY_VALUE) {
        // find what kind of value label stands in before
        // the value (keywords: author, abstract etc)
        var type_start_idx = idx;
        while (this.char_roles[type_start_idx] == this.char_roles_enum.QUERY_TYPE)
          type_start_idx--;

        var type_label = this.str.slice(type_start_idx + 1, idx + 1);
        result.remote = this.value_type_interpretation[type_label];
      }

      return result;

      /**
       * Gets the string without quotation marks at the beginning and the end
       *
       * @param {String} str input string with eventual quotation marks
       * @returns {String} the string with the quotation marks removed
       */
      function removeQuotationMarks(str) {
        if (str[0] == '"') {
          str = str.slice(1, str.length);
        }

        if (str[str.length - 1] == '"') {
          str = str.slice(0, str.length - 1);
        }

        return str;
      }
    },

    /**
     * Marks the parsed string characters from 'start'
     * (including) to 'stop' (excluding) with given word type
     *
     * @method _markAs
     * @param {String} type word type wit which the part will be marked
     * @param {Integer} start start index
     * @param {Integer} stop stop index
     * @private
    */
    _markAs: function(type, start, stop) {
      for (var i = start; i < stop; i++) {
        this.char_roles[i] = type;
      }
    },

    /**
     * Compares strings to get the user action. It is assumed that
     * the user changed a continues block of length which equals
     * the length difference of strings, and that the end of changed
     * block is in caret_pos
     *
     * @param old old string
     * @param nev new string
     * @param caret_pos caret position after the operation
     * @returns {Object} the result consists of an object with
     *  following properties:
     *    start: start index of the inconsistency between the strings,
     *    end: end index of the inconsistency
     *    operation: operation done on the string, can have values:
     *      'INSERTED': start -> end part was inserted
     *      'DELETED': start -> end part was deleted
     *      'SUBSTITUTED': the strings differ in another way than
     *        predicted - probably the string was substituted by
     *        another one
     * @private
     */
    _compareStr: function(old, nev, caret_pos) {
      var length_diff = nev.length - old.length;
      var longer, shorter;

      var inserted = (length_diff > 0);

      longer = inserted ? nev : old;
      shorter = inserted ? old : nev;

      var diff_start, diff_end;

      // hypothesis:
      // 1. the inserted/deleted string
      // is as long as the new and old strings length
      // difference
      // 2. the changed part is continuous and it has
      // one end at the current cursor position
      if (!inserted) {
        // deleted
        diff_start = caret_pos;
        diff_end = diff_start + Math.abs(length_diff);
      } else {
        diff_end = caret_pos;
        diff_start = diff_end - Math.abs(length_diff);
      }

      // modification was done at the end of the string
      if (diff_start == shorter.length) {
        return {
          start: diff_start,
          end: longer.length,
          operation: inserted ? 'INSERTED' : 'DELETED'
        };
      }

      if (checkHypothesis(diff_start, diff_end)) {
        return {
          start: diff_start,
          end: diff_end,
          operation: inserted ? 'INSERTED' : 'DELETED'
        };
      }

      // the string was totally changed
      return {
        operation: 'SUBSTITUTED'
      };

      function checkHypothesis(diff_start, diff_end) {
        // check hypothesis
        var i_lon = diff_end;
        var i_sh = diff_start;
        var i = 0;

        while (i < shorter.length && shorter[i] == longer[i]) {
          i++;
        }

        if (i < diff_start) {
          return false;
        }

        while (i_sh < shorter.length && shorter[i_sh] == longer[i_lon]) {
          i_lon++;
          i_sh++;
          // hypothesis is true
          if (i_sh == shorter.length) {
            return true;
          }
        }

        return false;
      }
    },

    /**
     * Looks for particular word types in the parsed string
     * in range 0 to limit index
     *
     * @param word_type word type used to mark found words
     * @param conf word configuration
     * @param limit the limiting index
     * @private
     */
    _findBySearch: function(word_type, conf, limit) {

      var str = this.str.slice(0, limit);

      for (var keyword_idx in conf.sorted_values) {
        var found_start_idx = 0, found_end_idx = 0;
        var keyword = conf.sorted_values[keyword_idx].toLowerCase();
        // find occurences of this keyword
        while (true) {
          found_start_idx = str.indexOf(keyword, found_end_idx);

          // not found -> break
          if (found_start_idx == -1)
            break;

          found_end_idx = found_start_idx + keyword.length;

          // already marked -> e.g. inside parentheses
          // or different keyword
          if (this.char_roles[found_start_idx])
            continue;

          // the keyword doesn't begin or end with separator
          if (found_start_idx > 0 && !this._isSeparator(found_start_idx - 1) ||
            (found_end_idx < limit && !this._isSeparator(found_end_idx)))
            continue;

          // detection_condition not passed
          if (conf.detection_condition && !conf.detection_condition(
            str, this.char_roles, found_start_idx, keyword))
            continue;

          // mark fields belonging to it
          this._markAs(word_type, found_start_idx, found_end_idx);

          if (conf.keyword_function)
            conf.keyword_function(this);
        }
      }
    },

    /**
     * Looks for separators in the parsed string
     *
     * @returns {Array} array with indices of separators
     *  in the parsed string
     * @private
     */
    _findSeparators: function() {
      var separator_indices = [];

      // find separators which are not in quotation marks
      for (var char_idx = 0; char_idx < this.str.length; char_idx++) {
        // is marked
        if (this._isWordPart(char_idx))
          continue;
        // is separator ?
        if (this.separators.indexOf(this.str[char_idx]) > -1) {
          this.char_roles[char_idx] = this.char_roles_enum.SEPARATOR;
          separator_indices.push(char_idx);
          continue;
        }
      }
      return separator_indices;
    },

    /**
     * Parses the set string basing the decision on the order of
     * words from the beginning of the string until limit_idx
     *
     * @param limit_idx the part of string beyond limit_idx
     *  will not be analyzed
     * @private
     */
    _findByOrderAnalysis: function(limit_idx) {

      var separator_indices = this._findSeparators();
      var parser = this;

      // by default undefined what means that the currently analysed word is
      // the first one
      var previous_word_type;

      separator_indices.push(limit_idx);
      // to return by pop from the first index
      separator_indices.reverse();
      var word_end, word_begin = 0;
      var is_word_last;
      while (separator_indices.length) {
        var word_type = previous_word_type;
        if (isWordFinished(word_end, previous_word_type)) {
          // omit separators
          word_begin = omitSeparators(word_begin);
          // omit marked words
          while (this.char_roles[word_begin] !== undefined) {
            previous_word_type = this.char_roles[word_begin];
            word_begin = separator_indices.pop() + 1;
            word_begin = omitSeparators(word_begin);
          }
          // if there's just one separator left the word is the last
          is_word_last = (separator_indices.length == 1);
          word_type = this._getNextWordType(previous_word_type, !is_word_last);
        }
        else {
          // overwrite separator
          this.char_roles[word_begin - 1] = previous_word_type;
          separator_indices.pop();
        }
        word_end = separator_indices.pop();
        // otherwise it's QUERY_VALUE without type - general search
        if (!(is_word_last ||
          checkDetectionCondition(word_begin, word_end, word_type))
        ) {
          word_type = this.char_roles_enum.QUERY_VALUE;
        }

        this._markAs(word_type, word_begin, word_end);
        previous_word_type = word_type;

        word_begin = word_end + 1;
      }

      function omitSeparators(idx) {
        while (parser._isSeparator(idx)) {
          idx++;
          separator_indices.pop();
        }
        return idx;
      }

      function checkDetectionCondition(start, end, word_type) {
        var condition = parser.keywords_flat[word_type].detection_condition;
        if (!condition)
          return true;
        return condition(parser.str, parser.char_roles, start, end);
      }

      function isWordFinished(end_idx, word_type) {
        if (!word_type)
          return true;
        var terminating_separators =
          parser.keywords.ORDER[word_type].terminating_separators;
        if (terminating_separators)
          return terminating_separators.indexOf(parser.str[end_idx]) > -1;
        return true;
      }
    },

    /**
     * Debug function to print the parsing result on the console
     * @private
     */
    _printCharRoles: function() {
      var translation_key = {
        QUERY_VALUE: 'V',
        QUERY_TYPE: 'T',
        SEPARATOR: 'S',
        NOT: 'N',
        LOGICAL_EXP: 'L',
        SPIRES: 'R'
      };

      var translated = [];
      for (var i in this.char_roles) {
        var source = [].concat(this.char_roles[i]);
        if (source.length == 1)
          translated[i] = translation_key[source];
        else
          translated[i] = source.length;
      }
      console.log(translated.join(''));
    },

    /**
     * Reinterprets the parsed string until the 'limit_idx' index
     * @param limit_idx limiting index
     * @private
     */
    _reinterpretFragment: function(limit_idx) {
      var quotation_marks = this._findQuotationMarks(limit_idx);

      // mark text in quotation marks as query value
      for (var i in quotation_marks) {
        var begin_idx = quotation_marks[i].begin;
        var end_idx = quotation_marks[i].end;

        if (end_idx == -1)
          end_idx = limit_idx - 1;

        this._markAs(this.char_roles_enum.QUERY_VALUE,
          begin_idx, end_idx + 1);
      }

      var doOrderMethod = false;
      // iterate over method
      for (var method in this.keywords) {

        if (method == 'ORDER') {
          doOrderMethod = true;
          continue;
        }

        // iterate over word types
        for (var type in this.keywords[method]) {
          this.methods[method].call(this, type, this.keywords[method][type],
            limit_idx);
        }
      }

      // do order method at the end
      if (doOrderMethod)
        this._findByOrderAnalysis(limit_idx);
    },

    /**
     * Updates the parsed string and analize it. Uses caret
     * position to predict wat part was changed and improve
     * the analisys results.
     *
     * @param str the new string
     * @param caret_pos caret position after making the change
     */
    updateSource: function(str, caret_pos) {
      str = str.toLowerCase();

      // no changes
      if (this.str == str)
        return;

      if (DEBUG) console.log(str);

      var comparison = this._compareStr(this.str, str, caret_pos);
      this.str = str;

      if (comparison.operation == 'DELETED') {
        this.char_roles.splice(
          comparison.start, comparison.end - comparison.start);
        if (DEBUG) this._printCharRoles();
        return;
      }

      this.resetOptions();

      var update_end = str.length;
      if (comparison.operation == 'INSERTED') {
        var to_insert = new Array(comparison.end);
        var part_after_caret = this.char_roles.slice(
          comparison.start, this.char_roles.length);
        update_end = comparison.end;

        this.char_roles = to_insert.concat(part_after_caret);
      } else { // comparison.operation == 'SUBSTITUTED'
        this.char_roles = [];
      }

      this._reinterpretFragment(update_end);
      if (DEBUG) this._printCharRoles();
    },

    /**
    * Reparses the whole string. Use only when the whole string was changed.
    *
    * Don't use this function on key-press event as the query while typing may
    * have temporary invalid syntax until a user finishes typing. In such
    * a situation use updateSource() with a proper caret position.
    *
    * @param str the new string
    * @returns {*} updateSource() result
    */
    reparseSource: function(str) {
      return this.updateSource(str, str.length);
    }
  };

  return SearchParser;
});
