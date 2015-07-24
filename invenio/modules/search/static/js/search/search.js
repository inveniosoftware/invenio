/*
 * This file is part of Invenio.
 * Copyright (C) 2014, 2015 CERN.
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


define([
        'jquery',
        'flight/lib/component',
        'js/search/facets_filter',
],
function($, defineComponent, FacetsFilter) {

  /**
   * Serialize the given filters as a query.
   *
   * The resulting query format is:
   * `facet1:value AND (facet2:value OR facet2:value)...`
   *
   * @param {FacetsFilter} facetsFilter facets filters
   * @return {string} query corresponding to the given filters
   */
  function facetsFilterSerializer(facetsFilter) {
    var partials = [];
    $.each(facetsFilter.getFilters(), function(facetName, filters) {
      var incs = $.map(filters.inc, function(v) {
        return facetName + ':"' + v + '"';
      });
      if (incs.length > 1) {
        partials.push('(' + incs.join(' OR ') + ')');
      } else {
        partials.push(incs[0]);
      }
    });
    return partials.join(' AND ');
  }

  // return flightJS component
  return defineComponent(Search);

  /**
   * Main Search component. It updates the user query input field, and keep the
   * facets filter state up to date.
   *
   * Listens on:
   * - facetChange:
   *     => {state: <'include'|'exclude'>, name: <facet name>, value: <filtered value>}
   *     Include or exclude a filter in the facetsFilter.
   * - facetsEdit:
   *     => {}
   *     Appends the serialized facets filter to the user query and clear the
   *     facets filter.
   * Sends:
   * - facetsSet:
   *     => {facetsFilter: <FacetsFilter>, serializedFacetsFilter: <serialized filter>}
   *     Set all facets filter.
   */
  function Search() {
    this.attributes({
      // base url used for searching
      searchUrl: undefined,
      // query parameter used for user query
      userQueryParam: 'p',
      // query parameter used for facet filtering
      facetsFilterQueryParam: 'post_filter',
      // facets loaded by the server
      facetsFilter: new FacetsFilter(),
      // function used to serialize the facetsFilter in the URL
      facetsFilterSerializer: function() { return facetsFilterSerializer; },
      // jquery selector for the search form
      searchFormSelector: undefined,
      // jquery selector for the search results
      searchResultsSelector: undefined,
    });

    /**
     * Update the search form action according to the given filter query.
     *
     * @param {string} serializedFacetsFilter facet filters serialized as a query.
     */
    this.updateSearchFormAction = function(serializedFacetsFilter) {
      // update search form hidden field
      $('input[type="hidden"][name="' + this.attr.facetsFilterQueryParam + '"]')
        .prop('value', serializedFacetsFilter);
    }

    /**
     * Update window URL using the given facet filter and user query.
     *
     * @param {string} serializedFacetsFilter facet filters serialized as a query.
     * @param {string} userQuery (optional) query written by the user.
     */
    this.updateURL = function(serializedFacetsFilter, userQuery) {
      // update the URL
      if (typeof(window.history.pushState) === 'function') {
        // updating the query string
        var queryString = window.location.search;
        queryString = setQueryStringParam(queryString,
                                          this.attr.facetsFilterQueryParam,
                                          serializedFacetsFilter);
        queryString = setQueryStringParam(queryString,
                                          this.attr.userQueryParam,
                                          userQuery);
        // rebuild the URL
        var path = window.location.origin + window.location.pathname +
          queryString + window.location.hash;

        window.history.pushState({
          path: path,
          facetsFilter: this.facetsFilter.getFilters(),
          userQuery: userQuery,
        }, document.title, path);
      }
    }

    /**
     * Send the facets filter change in an event
     */
    this.broadcastFacetsFilterSet = function() {
      // send event updating the facets menu
      this.trigger(document, 'facetsSet', {
        facetsFilter: this.facetsFilter,
        serializedFacetsFilter: this.attr.facetsFilterSerializer(this.facetsFilter),
      });
    }

    this.after('initialize', function() {
      var that = this;

      // we might have missed a pop state event. Thus it is better to use the
      // window state if it exists.
      if (window.history.state !== null &&
          // there is no state for this location
          window.history.state.facetsFilter !== null) {
        this.facetsFilter = new FacetsFilter(window.history.state.facetsFilter);

        // generate the corresponding query
        var facetsQuery = this.attr.facetsFilterSerializer(this.facetsFilter);
        this.broadcastFacetsFilterSet();

        // update the search form
        this.updateSearchFormAction(facetsQuery);

        // update the search results
        this.search();
      } else {
        // else use the one provided by the backend-generated html
        this.facetsFilter = this.attr.facetsFilter;
      }

      // listen on events sent by the facet menu and update the facet filters
      this.on('facetChange', function(ev, data) {
        // update the facet filter
        switch (data.state) {
            case 'include':
                this.facetsFilter.resetFacetValue(data.name, data.value);
                this.facetsFilter.includeFacetValue(data.name, data.value);
                break;
            case 'exclude':
                this.facetsFilter.resetFacetValue(data.name, data.value);
                this.facetsFilter.excludeFacetValue(data.name, data.value);
                break;
            default:
                this.facetsFilter.resetFacetValue(data.name, data.value);
                break;
        }
        // generate the corresponding query
        var facetsQuery = this.attr.facetsFilterSerializer(this.facetsFilter);
        that.broadcastFacetsFilterSet();
        // update the search form
        that.updateSearchFormAction(facetsQuery);
        var userQuery = $('form[name="search"] input[name=p]').val();
        // update the URL
        that.updateURL(facetsQuery, userQuery);

        // update the search results
        this.search();
      });

      // listen on the "query filter" edition event
      this.on('facetsEdit', function(ev, data) {
        // move the filter query from its static display to the search input.
        // this makes it editable
        var filterQuery = this.attr.facetsFilterSerializer(this.facetsFilter);
        var userQuery = $('form[name="search"] input[name=p]').val();
        userQuery += (userQuery ? ' AND ' : '') + filterQuery;
        $('form[name="search"] input[name=p]').val(userQuery);

        // reset the facetsFilter
        this.facetsFilter = new FacetsFilter();
        this.broadcastFacetsFilterSet();
        this.updateSearchFormAction('');
        // update the url so that user can click "back" button and see the
        // previous view.
        this.updateURL('', userQuery);
        // reloading because the facets might have changed
        // TODO: we should return the facets with the Ajax response.
        window.location.reload();
      });

      // listen on popstate, i.e user clicks browser's back or forward button
      this.on(window, 'popstate', function() {
        // reload the page if
        if (window.history.state === null ||
            // there is no state for this location
            window.history.state.facetsFilter === null ||
            // or if the results set parent element is not here (not returned by
            // the server) FIXME: always generate the result set?
            $(this.attr.searchResultsSelector).length === 0 ||
            // or the user query changed (facets might have changed)
            window.history.state.userQuery != $('form[name="search"] input[name=p]').val()
           ) {
          return window.location.reload();
        }
        // retrieve the filters from the state
        this.facetsFilter = new FacetsFilter(window.history.state.facetsFilter);
        var userQuery = window.history.state.userQuery;

        var facetsQuery = this.attr.facetsFilterSerializer(this.facetsFilter);
        // broadcast the change
        this.broadcastFacetsFilterSet();
        // update the search form
        this.updateSearchFormAction(this.attr.facetsFilterSerializer(this.facetsFilter));
        // update search input with user query parameter
        $('form[name="search"] input[name=p]').val(userQuery);
        this.search();
      });
    });

    /**
     * Send a search request and update the search results
     */
    this.search = function() {
      var that = this;
      var searchUrl = this.attr.searchUrl;
      var userQuery = $('form[name="search"] input[name=p]').val();
      var filterQuery = this.attr.facetsFilterSerializer(this.facetsFilter);

      var data = {};
      data[this.attr.userQueryParam] = userQuery;
      data[this.attr.facetsFilterQueryParam] = filterQuery;
      $.ajax({
        url: searchUrl,
        data: data,
        context: $(that.attr.searchResultsSelector)
      }).done(function(response) {

        $(this).html(response);
      });
    }
  };

  /**
   * Generate a guid.
   *
   * As described here: http://stackoverflow.com/questions/105034/create-guid-uuid-in-javascript
   *
   * @return {string} a new guid
   */
  function guid() {
    function s4() {
      return Math.floor((1 + Math.random()) * 0x10000)
      .toString(16)
      .substring(1);
    }
    return s4() + s4() + '-' + s4() + '-' + s4() + '-' +
           s4() + '-' + s4() + s4() + s4();
  }

  /**
   * Basic query string parameter replacement function.
   *
   * @return {string} a new guid
   */
  function setQueryStringParam(queryString, name, value) {
    var encodedName = encodeURIComponent(name);
    var encodedValue = value ? encodeURIComponent(value) : '';
    var newQueryString = queryString.replace(new RegExp('(' + encodedName +
                                             '=)[^\&]*'), '$1' + encodedValue);
    if (newQueryString === queryString) {
      if (newQueryString.length === 0) {
        newQueryString = "?";
      } else if (newQueryString[newQueryString.length - 1] !== '?' &&
                 newQueryString[newQueryString.length - 1] !== '&') {
        newQueryString += "&";
      }
      newQueryString += encodedName + '=' + encodedValue;
    }
    return newQueryString;
  }
});
