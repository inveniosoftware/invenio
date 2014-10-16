/*
 * This file is part of Invenio.
 * Copyright (C) 2013, 2014 CERN.
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


/* A file contatining fuctions treating the search field. */
/**
 * @requires jQuery-caret: https://github.com/acdvorak/jquery.caret
 * @requires search_parser.js: invenio/modules/search
 *
 *
 * CONFIGURATION

  Example:

  searchField.searchTypeahead({
    value_hints_url: '/list/%TYPE?q=%QUERY',
    options_sets: {
      invenio: invenio_parser_options,
      spires: spires_parser_options
    },
    default_set: 'invenio'
  }

  searchField - jQuery selector
  value_hints_url - url for getting remote queries - other than keywords
    e.g. authors
  options_sets - syntax schema, there can be many of them switched with custom keywords
  default_set - default options set, used when the typeahead field is empty

  Below an example of one of the options set

  var invenio_parser_options = {
      keywords: {
        SEARCH: {
          SPIRES_SWITCH: {
            min_length: 1,
            keyword_function: setSpireSyntax,
            detection_condition: isFirstWord,
            values: ['find'],
            autocomplete_suffix: ' '
          },
          LOGICAL_EXP: {
            min_length: 1,
            values: ['AND', 'OR', 'AND NOT'],
            autocomplete_suffix: ' '
          }
        },
        ORDER: {
          QUERY_TYPE: {
            min_length: 1,
            finish_condition: endsWithColon,
            values: area_keywords,
            autocomplete_suffix: ':'
          },
          QUERY_VALUE: {
            min_length: 3,
            finish_condition: notEndsWithColon
          }
        }
      },
      get_next_word_type: get_next_word_type,
      value_type_interpretation: {
        author: 'exactauthor'
      },
      separators: [' ', '(', ')', ':']
    };

    separators - all keywords separators
    value_type_interpretation - keys are QUERY_TYPE values,
     whereas values are the corresponding strings used
     for substitution of '%TYPE' string in value_hints_url
     in the main configuration options.

    get_next_word_type(previous_word_type, word_types) -
      function used by ORDER method to get the next word type
      can return array of keywords names, but there cannot be
      two of them from ORDER method
        word_types - all the keywords names

    keywords - a dictionary with all the words types interpreted
      by the parser.

      First key is the method used for parsing.

      There are two methods:
        SEARCH - searches for the keyword in a parsed string and
          marks it corespondingly,
        ORDER - detects the kind of typeahead basing the decision
          on the order of words using get_next_word_type function

      Method SEARCH has priority over method ORDER. It may be used
      to find keywords containing separators as well as special
      functional keywords which are used to change option set
      (key options_sets in configuration).

    Parsing algorithm:
      1. do SEARCH method - look for keywords
      2. find separators which are not marked as words
        with SEARCH method
      3. do ORDER method - get type of every not marked
        keyword basing on the get_next_word_type function

    Inside methods configuration there are keywords defined.

    KEYWORDS_GROUP_NAME: {
      min_length: 1,
      keyword_function: function(search_typeahead),
      detection_condition: function(str, char_roles, start_idx),
      finish_condition: function(str, char_roles, end_idx)
      values: [],
      autocomplete_suffix: ' '
    }

    KEYWORDS_GROUP_NAME - just identifier of the group
    min_length - minimal length to show the hints
    keyword_function - function run on keyword detection
      search_typeahead - typeahead object
    detection_condition - addtional detection condition boolean function
      tested for SEARCH method keywords (optional)
      when false the string part will not be marked as the
      keyword despite such a string was found
    finish_condition - addtional word finish condition boolean
      function tested for ORDER method keywords
      when false the keyword will be marked continually despde
      a following separator (optional)
    values - possible values of a keyword - required for all
      keywords beside QUERY_VALUE which values are get remotely
    autocomplete_suffix - string added after the autocompleted
      value, may be a default separator
 *
 */

define([
  'jquery',
  'js/search/search_parser',
  'typeahead', // $.fn.typeahead()
  'jquery-caret',
], function($, SearchParser, Bloodhound) {
  "use strict";

  function SearchTypeahead(element, options) {

    this.$element = $(element);
    this.options = $.extend({}, $.fn.searchTypeahead.defaults,
      options);

    this.dontBracket = false;
    this.value_types = this.options.value_types;
    var that = this;

    for (var i in this.options.options_sets) {
      this.options.options_sets[i] =
        this.initializeOptionsSet(this.options.options_sets[i]);
    }

    this.parser = new SearchParser(this.options.options_sets, this.options.default_set);

    this.initTypeahead();

    this.ttTypeahead = this.$element.data("ttTypeahead");

    // saves overwritten functions
    this.orgTypeahead = {
      setInputValue: this.ttTypeahead.input.setInputValue,
      setHintValue: this.ttTypeahead.input.setHintValue,
    };

    this.ttTypeahead.input.setInputValue = function(value, silent) {
      return that.setInputFieldValue.apply(that, [value, silent]);
    };

    // update parser state on input event
    this.$element.on('input', function(event) {
      var input_field_value = $(this).val();
      that.parser.updateSource(input_field_value, $(this).caret());
    });

    // disable grey hint in input field background - not compatible yet
    // with this kind of typeahead
    this.ttTypeahead.input.setHintValue = function(value) {};

    // sets initial query_range
    this.parser.reparseSource(this.$element.val());
    this.query_range = this.parser.getQueryRangeIdx(this.$element.val().length);
  }

  var PluginClass = SearchTypeahead;
  var dataLabel = 'search_typeahead';

  SearchTypeahead.prototype = {

    /**
     * Setups the typeahead element
     */
    initTypeahead: function() {

      var that = this;

      var engine = new Bloodhound({
        remote: {
          url: this.options.value_hints_url,
          replace: function(url, query) {
            return that.getUrl.call(that, url, query);
          },
          filter: this.processResponse
        },
        datumTokenizer: function(d) {
          return Bloodhound.tokenizers.whitespace(d.value);
        },
        // not used after the modifications but required by bloodhound
        queryTokenizer: Bloodhound.tokenizers.whitespace
      });

      for (var set_name in this.options.options_sets) {
        var options = this.options.options_sets[set_name];
        options.indices = this.createIndices(engine, options.keywords);
      }

      engine.get = function(field_value, cb) {
        return that.getHints(field_value, cb, this);
      };

      engine.initialize();

      this.$element.typeahead({
        // min length is controlled in getHints function
        // this setting is to pass everything
        minLength: 1
      },
      {
        source: engine.ttAdapter(),
        displayKey: 'value'
      });
    },

    /**
     * Initialize an option set
     *
     * @param options option set
     * @returns initialized set
     */
    initializeOptionsSet: function(options) {
      options.word_types = {};
      options.keywords_flat = {};
      for (var method_key in options.keywords) {
        var method = options.keywords[method_key];
        for (var word_type in method) {
          var conf = method[word_type];
          options.keywords_flat[word_type] = conf;
        }
      }

      return options;
    },

    /**
     * Creates search indices for typeahead engine
     *
     * @param engine empty engine should be passed here
     * @param keywords keywords configuration -
     *  the part passed in to the class constructor at key
     *  keywords
     * @returns {Array} Array of search indices
     */
    createIndices: function(engine, keywords) {
      var search_indices = [];

      for (var method_key in keywords) {
        var method = keywords[method_key];
        for (var word_type in method) {
          var conf = method[word_type];
          if (conf.values === undefined)
            continue;

          var index = deepCopy(engine.index);
          index.add(convertToTypeaheadDict(conf));
          search_indices[word_type] = index;
        }
      }

      return search_indices;

      function deepCopy(obj) {
        /// clones an object
        return jQuery.extend(true, {}, obj);
      }

      function convertToTypeaheadDict(conf) {
        var suffix = '';
        if (conf.autocomplete_suffix)
          suffix += conf.autocomplete_suffix;
        return $.map(conf.values,
          function(val, i) {
            var result = {
              value: val + suffix,
              raw_value: val,
              suffix: suffix
            };
            return result;
          }
        );
      }
    },

    /**
     * Updates the template url with a query
     *
     * @param url template url containing '%TYPE' in
     *  the place of query type and '%QUERY' in the place
     *  of query value
     * @param query {Object} an object with properties:
     *  remote: the string to be put instead of %TYPE
     *  value: the string to be put instead of %QUERY
     * @returns {String} the result url
     */
    getUrl: function(url, query) {

      url = url.replace('%TYPE', query.remote);
      url = url.replace('%QUERY', query.value);

      return url;
    },

    /**
     * Processes the coming response to get the one in the format
     * expected by typeahead - an Array of dictionaries
     *
     * @param response
     * @returns {*}
     */
    processResponse: function(response) {
      return response.results;
    },

    /**
     * Fetches hints for typeahead
     *
     * @param field_value the new value of the input field
     * @param cb typeahead callback
     * @param bloodhound bloodhound engine
     */
    getHints: function(field_value, cb, bloodhound) {
      var matches = [];

      var caretIdx = this.$element.caret();

      this.parser.updateSource(field_value, caretIdx);
      this.query_range = this.parser.getQueryRangeIdx(caretIdx);
      var query = this.parser.getAutocompleteQuery(
        this.query_range.start, caretIdx);

      // saves the current query inside typeahead to prevent improper text
      // merging on blur
      this.ttTypeahead.input.setQuery(query.value);

      var options_set = this.options.options_sets[
        this.parser.getOptionsSetName()
      ];

      if (!query.type) {
        cb && cb([]);
        return;
      }

      if (query.type == options_set.word_types.QUERY_VALUE && query.remote) {
        if (query.value.length < getMinLength(query.type)) {
          cb && cb([]);
          return;
        }
        // later used in setInputValue cannot be passed in another way
        this.dontBracket = false;
        bloodhound._getFromRemote(query, returnRemoteMatches);
        return;
      } else {

        // assure it's an array
        query.type = [].concat(query.type);
        var search_indices = options_set.indices;

        for (var i in query.type) {
          var type_name = query.type[i];
          if (query.value.length < getMinLength(type_name))
            continue;
          if (!search_indices[type_name])
            continue;
          matches = matches.concat(search_indices[type_name].get(query.value));
        }
        if (matches.length > 0) {
          matches = bloodhound.sorter(matches).slice(0, bloodhound.limit);
        }
        this.dontBracket = true;
        cb && cb(matches);
      }

      function returnRemoteMatches(remoteMatches) {
          cb && cb(bloodhound.sorter(remoteMatches));
      }

      function getMinLength(type) {
        return options_set.keywords_flat[type].min_length;
      }
    },

    /**
     * Merges the current input field value with a hint
     * from typeahead
     *
     * @param {String} to_merge the value to be merged
     * @param {*} query_range
     * @returns {string} merged string
     */
    mergeWithCurrentInputFieldValue: function(to_merge, query_range) {
      var input_field_value = this.$element.val();

      var precedingStr = input_field_value.slice(
        0, query_range.start);
      var followingStr = input_field_value.slice(
        query_range.end, input_field_value.length);

      if (precedingStr[precedingStr.length - 1] == '"' &&
          to_merge[0] == '"') {
        precedingStr = precedingStr.slice(0, precedingStr.length - 1);
      }

      return precedingStr + to_merge + followingStr;
    },

    /**
     * Checks if the input field is focused.
     *
     * @returns {boolean}
     * @private
     */
    _isFocused: function() {
      return !!this.$element.filter($(document.activeElement)).length;
    },

    /**
     * Does all the tricks which need to be done at setting
     * a value of the input field.
     *
     * It is run also by resetInputValue from twitter's typeahead.js on blur
     * event.
     *
     * @param {String} value typeahead suggestion
     * @param silent corresponding twitter's typeahead parameter - see
     *   twitter typeahead documentation
     * @returns {*}
     */
    setInputFieldValue: function(value, silent) {

      var bracketedValue = value;
      if (value.indexOf(' ') > -1 && !this.dontBracket) {
        bracketedValue = bracketStr(value);
      }

      var merged = this.mergeWithCurrentInputFieldValue(
        bracketedValue, this.query_range);

      // run original setInputValue with merged value
      // must be run before setting the caret position as the caret position
      // should be updated after updating the value of the input field
      var result = this.orgTypeahead.setInputValue.call(
        this.ttTypeahead.input, merged, silent);

      // update query range
      this.query_range.end =
        this.query_range.start + bracketedValue.length;

      // update the parser until the end of the typed and autocompleted part of
      // the query
      this.parser.updateSource(merged, this.query_range.end);

      // To set the caret position the element must be focused, otherwise
      // $.fn.caret focuses it which is not the desired result on blur event.
      // When the element is not focused we don't care about the caret position
      // update. In this situation a focus event by pressing Tab button selects
      // the whole text, whereas focus by clicking moves the caret to the click
      // position, so the caret position is not stored anyway.
      if (this._isFocused())
        // if a user types and just autocompleted, move the caret to the end of
        // the autocompleted part
        this.$element.caret(this.query_range.end);

      return result;

      function bracketStr(str) {
        if (str[0] == '\"')
          return str + '"';
        return '"' + str + '"';
      }
    },

    /**
     * The function should be used to set field value of
     * typeahead-enabled input field using javascript.
     * It updates internal query value of typeahead.js
     * to which the field is reseted on blur event.
     *
     * @method setFieldValue
     * @param {String} new_value new value to set
     */
    setFieldValue: function(new_value) {
      this.$element.val(new_value);
      this.ttTypeahead.input.setQuery(new_value);
    }
  };

  $.fn.searchTypeahead = function (option) {

    var $elements = this;

    return $elements.map(function (idx, element) {
      var $element = $(element);
      var object = $element.data(dataLabel)
      var options = typeof option == 'object' && option;
      // attach jQuery plugin
      if (!object) {
        object = new PluginClass($element, options)
        $element.data(dataLabel, object)
      }
      return object;
    });
  };

  $.fn.searchTypeahead.defaults = {};

});
