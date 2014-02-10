/*
 * This file is part of Invenio.
 * Copyright (C) 2013 CERN.
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

!function( $ ){

  "use strict"

  function SearchTypeahead(autocompleteTypeKeys, keywords) {

    var field = this;

    var lowercaseKeywords = [];
    for (var idx in keywords) {
      lowercaseKeywords.push(keywords[idx].toLowerCase())
    }

    function getLastClosedBracketIdx(str) {
      var lastClosedIdx = str.lastIndexOf("\"");

      // count number of occurencies
      var count = str.match(/\"/g);
      if (count == null)
        return -1;

      if ((count.length % 2) == 0)
        return lastClosedIdx;

      return str.lastIndexOf("\"", lastClosedIdx - 1);
    }

    function getLastBracketsIdx(str) {
      var bracketsIdx = str.lastIndexOf('"');
      if (bracketsIdx == -1)
        return {
          lastClosed: -1,
          lastOpened: -1,
        };

      var closedBracketIdx = getLastClosedBracketIdx(str);

      // open bracket
      if (bracketsIdx > closedBracketIdx)
        return {
          lastClosed: closedBracketIdx,
          lastOpened: bracketsIdx
        }

      return {
        lastClosed: closedBracketIdx,
        lastOpened: -1
      };
    }

    function getLastOccurence(str, pattern, limit) {
      var result, savedRes;

      if (typeof limit == 'undefined') {
        limit = str.length;
      }

      do {
        savedRes = result;
        result = pattern.exec(str);
      } while (result !== null && result.index <= limit);

      if (typeof savedRes == 'undefined')
        return {
          start: -1,
          end: -1
        }

      return {
        start: savedRes.index,
        end: savedRes.index + savedRes[0].length
      }
    }

    function getLastSpace(str, limit) {
      // actually one or more spaces
      return getLastOccurence(str, /\s+/g, limit);
    }

    function getLastColon(str, limit) {
      // colon, any number of spaces then optional qoutation mark
      // all must be precieded by non-whitespace character, which is not included
      // in (start, end) range
      var res = getLastOccurence(str, /[^\s]:\s*[\"]*/g, limit - 1);
      /*"*/ // just to fix broken string highlighting in sublime :)
      
      // +1 because of checking for a preceding char
      if (res.start > -1)
        res.start += 1;

      return res;
    }

    function getAutocompleteValueCutoffInd(str, initialIdx) {

      /*
        @returns dictionary with two values different only 
          in case of existing open bracket
          inner - index of the content after the brackets
          withBrackets - index of an eventual bracket
      */

      if (typeof initialIdx == 'undefined') {
        initialIdx = str.length;
      }

      var bracketsIdx = getLastBracketsIdx(str);

      // value cutoff at an opened bracket
      if (bracketsIdx.lastOpened > -1) {
        return {
          inner: bracketsIdx.lastOpened + 1,
          withBrackets: bracketsIdx.lastOpened
        }
      }
      // closed bracket is the last sign
      if (bracketsIdx.lastClosed == str.length - 1) {
        return {
          inner: str.length - 1,
          withBrackets: str.length - 1
        }
      }

      var spaceIdx = getLastSpace(str);

      // length - 2 to avoid getting the colon when it is the last character
      var colonIdx = getLastColon(str, str.length - 2);

      return {
        inner: Math.max(colonIdx.end, spaceIdx.end, 0),
        withBrackets: Math.max(colonIdx.end, spaceIdx.end, 0)
      }
    }

    function getLastQueryCutoffIdx(str) {

      // cutoff index of last query, so expresion like a keyword:
      // AND, OR... author:, abstract:,
      // or a type:value pair e.g.:
      // author:"Robertson N A", author:Robe
      // whatever is after the colon

      var cutoff = getAutocompleteValueCutoffInd(str);
      var colonIdx = getLastColon(str, cutoff.inner);

      if (colonIdx.end !== cutoff.inner)
        return {
          typeStart: -1,
          typeEnd: -1,
          valueWithBracketsStart: cutoff.withBrackets,
          valueStart: cutoff.inner
        }

      // look for a type before the colon
      var spaceIdx = getLastSpace(str, colonIdx.start);

      return {
        typeStart: Math.max(spaceIdx.end, 0),
        typeEnd: colonIdx.start,
        valueWithBracketsStart: cutoff.withBrackets,
        valueStart: colonIdx.end
      }
    }

    function getQuery(str) {

      /// converts input field string to format type:value
      /// parsable later with parseQuery()

      var indices = getLastQueryCutoffIdx(str);
      var searchQuery = str.substring(indices.valueWithBracketsStart, str.lenght);
      
      if (indices.typeStart == -1 || indices.typeEnd == -1)
        return searchQuery;
      
      var type = str.substring(indices.typeStart, indices.typeEnd);

      if (searchQuery && type in autocompleteTypeKeys)
          return type + ':' + searchQuery;

      return searchQuery;
    }

    function bracketStr(str) {
      if (str[0] == '\"')
        return str + '"';
      return '"' + str + '"';
    }

    function parseQuery(str, colonChar)
    /// divides by colon sign already prepared query
    {
      if (typeof colonChar == 'undefined')
        colonChar = ':'

      var colonIdx = str.indexOf(colonChar);
      if (colonIdx == -1)
        return {
          value: str,
          type: 'KWORD'
        }

      return {
        value: str.substring(colonIdx + colonChar.length, str.length),
        type: str.substring(0, colonIdx)
      }
    }

    function mergeWithInputValue(value, typedText) {

      if (value.length == 0)
        return typedText;

      // the last char is closed bracket
      // open the bracket to autocomplete the stuf inside the brackets
      if (typedText[typedText.length - 1] == '\"' && getLastBracketsIdx(typedText).lastOpened == -1)
        typedText = typedText.substring(0, typedText.length - 1);

      // fix for completition of when the last value is a boolean keyword (ends with a space)
      // ignore the space at the end
      if (typedText[typedText.length - 1] == ' ')
        typedText = typedText.substring(0, typedText.length - 1);

      // substitute with query on blur - query if full query
      var query = parseQuery(value);
      // type 'KWORD' means that 'value' doesn't have the query type (apparently no colon ;) )
      // so for example it's just a value for the completition from the dropdown
      if (query.type !== 'KWORD' && query.value) {
        
        var parsingIndices = getLastQueryCutoffIdx(typedText);
        var strPrecedingQuery = typedText.substring(0, parsingIndices.typeStart);
        if (query.value.indexOf(' ') > -1)
          query.value = bracketStr(query.value);
        return strPrecedingQuery + query.type + ':' + query.value;
      }

      // cases below: 
      // autocomplete, select from dropdown ... also blur when user types a keyword
      // leaving the evental type label in the input box, adding autocompletition stuff
      var cutOffIdx = getAutocompleteValueCutoffInd(typedText).withBrackets;
      var strPrecedingQuery = typedText.substring(0, cutOffIdx);

      // the case on blur after typing the whole keyword
      if (lowercaseKeywords.indexOf(value.toLowerCase()) > -1) {
        return strPrecedingQuery + value;  
      }

      // autocompletition with a value containing spaces
      // (in keywords spaces can be only at the end - which is the previous case)
      if (value.indexOf(' ') > -1) {
        value = bracketStr(value);
      }

      return strPrecedingQuery + value; 
    }

    field.typeahead({
      local: keywords,
      remote: {
        url: '/list/%TYPE?q=%QUERY',
        
        replace: function(url, uriEncodedQuery) {

          var query = parseQuery(uriEncodedQuery, '%3A')

          url = url.replace('%TYPE', autocompleteTypeKeys[query.type]);
          url = url.replace('%QUERY', query.value);

          // console.log('server query: ' + url);

          return url;
        },

        filter: function(response) {
          return response.results;
        }

      },
      name: 'search',
      limit: 10
    });

    var orgTypeahead = {
      setInputValue: field.data("ttView").inputView.setInputValue,
      getQuery: field.data("ttView").inputView.getQuery,
      getSuggestions: field.data('ttView').datasets[0].getSuggestions
    };

    field.data("ttView").inputView.getQuery = function() {

      return getQuery(orgTypeahead.getQuery());
    }

    field.data("ttView").inputView.setInputValue = function(value, silent) {

      var typedText = this.$input.val();
      var merged = mergeWithInputValue(value, typedText);
      return orgTypeahead.setInputValue.apply(field.data("ttView"), [merged, silent]);
    }

    var dataset = field.data('ttView').datasets[0];

    dataset.getSuggestions = function(query, cb) { 

      var parsedQuery = parseQuery(query);

      // console.log(parsedQuery.value + "++++" + parsedQuery.type);

      // eventually remove the quotation mark
      if (parsedQuery.value[0] == '"') // '"'
      {
          parsedQuery.value = parsedQuery.value.substring(1, parsedQuery.value.length);
          query = parsedQuery.type + ':' + parsedQuery.value;
      }

      if (parsedQuery.type == "KWORD")
      {
        // a hack to disable remote queries 
        // there's an "if" to check "transport" existence
        // inside original getSuggestions() function
        var transportCopy = dataset.transport;
        dataset.transport = 0;
        var result = orgTypeahead.getSuggestions(query, cb);
        dataset.transport = transportCopy;
        return result;
      }

      // do the remote query only if the type is valid and query length
      // is at least 3 - which is also a server requirement
      if (parsedQuery.type in autocompleteTypeKeys && typeof(autocompleteTypeKeys[parsedQuery.type]) == 'string' && parsedQuery.value.length > 2) {

        // the same hack as above to disable the local queries
        var localCopy = dataset.local;
        dataset.local = [];
        var result = orgTypeahead.getSuggestions(query, cb);
        dataset.local = localCopy;
        return result;
      }
    }
  }

  $.fn.searchTypeahead = SearchTypeahead;

}( window.jQuery )
