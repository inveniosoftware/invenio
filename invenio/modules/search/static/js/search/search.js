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


define(function(require, exports, module) {
  "use strict";
  var $ = require('jquery');
  var QueryGenerator = require('js/search/query_generator');
  var HashStorage = require('js/search/hash_storage');
  // provides $.fn.facet
  require('js/search/facets/engine');

  function SearchResultsPage(options) {

    var options = $.extend({}, SearchResultsPage.defaults, options);

    this.$facets_element = options.$facets_element;
    this.$search_results = options.$search_results;
    this.$search_query_field = options.$search_query_field;

    this.previous_search_query = options.request_args.p;
    this.request_args = $.extend({}, options.request_args);
    this.search_url = options.search_url;

    this.facet_engine = this.$facets_element.facet($.extend({},
      options.facets_configuration,
    {
      facets: options.facets_content,
      activate_modifier_keys: true,
      translations: options.translations,
    }))[0];

    this.facet_engine.loaded_promise.done(function() {
      this.synchronizePageState();
    }.bind(this));

    this.connectEvents();

    // Load facets state on page load
    if (document.location.hash.length > 2) {
      var facets_state = HashStorage.getContent();
      this.facet_engine.loadState(facets_state);
    }
  }

  SearchResultsPage.prototype = {

    destroy: function() {
      this.facet_engine.destroy();
      this.$facets_element.unbind('updated');
      $(window).unbind('hashchange', this.onHashChange);
    },

    connectEvents: function() {
      var that = this;
      this.$facets_element.on('updated', function(event) {
        if (that.facet_engine.is_loaded) {
          that.synchronizePageState();
        }
      });

      // Rebuild facet filter on hash change.
      $(window).bind('hashchange', this.onHashChange.call(this));
    },

    /**
     * Update search field and hash accordingly to facets state
     */
    synchronizePageState: function() {
      var queryStructure = this.facet_engine.getQueryStructure();
      var facet_query = QueryGenerator.generateQuery(
        this.facet_engine.getQueryStructure(),
        !!this.previous_search_query
      );
      var merged_search_query = QueryGenerator.merge(
        [this.previous_search_query, facet_query], 'AND');

      this.$search_query_field.val(merged_search_query);

      var filter = this.facet_engine.getState();

      HashStorage.update(filter);

      this.updateSearchResults(queryStructure);
    },

    /**
     * Flaten the query structure to have one required by the server.
     * Temporary solution as we expect the port to ElasticSearch anyway.
     *
     * @param queryStructure
     * @returns {Array}
     */
    getInvenioFilter: function(queryStructure) {
      var filter = [];
      $.each(queryStructure, function(areaName, item) {
        $.each(item, function(operator, terms) {
          $.each(terms, function(idx, term) {
            filter.push([operator, areaName, term]);
          });
        });
      });
      return filter;
    },

    onHashChange: function(event) {
      var storedState = HashStorage.getContent();
      if (JSON.stringify(this.facet_engine.getState()) !==
          JSON.stringify(storedState)) {
        this.facet_engine.loadState(storedState);
      }
    },

    setUpFacets: function(facet_configuration, facets_content) {


    },

    updateSearchResults: function(queryStructure) {
      $.ajax(this.search_url, {
        type: 'POST',
        data: $.extend({}, this.request_args, {
          filter: JSON.stringify(this.getInvenioFilter(queryStructure))
        }),
        context: this,
      }).done(function(data) {
        this.$search_results.html(data);
      });
    }
  };

  /**
   * The default values can be put here, although this section is to document
   * the parameters too.
   */
  SearchResultsPage.defaults = {
    /**
     * @param The jQuery selector of an DOM element on which the facets will be
     *  shown (usually a div section)
     */
    $facets_element: undefined,
    /**
     * @param Configuration of displaying the facets. The default one is
     *  js/search/facet/configuration/links/main.js
     */
    facets_configuration: {},
    /**
     * @param Facets configuration received from server from
     *  modules.search.registry.FacetRegistry.get_facets_config
     */
    facets_content: undefined,
    /**
     * @param Search results frame
     */
    $search_results: undefined,
    /**
     * @param search query field
     */
    $search_query_field: undefined,
    /**
     * @param stored arguments of the search request made
     */
    request_args: [],
    /**
     * The general URL for search requests
     */
    search_url: undefined,
  };

  module.exports = SearchResultsPage;
});
