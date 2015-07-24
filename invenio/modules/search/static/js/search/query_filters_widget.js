/*
 * This file is part of Invenio.
 * Copyright (C) 2015 CERN.
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
 * A file containing the FlightJS component displaying the filters applied to
 * the user's query.
 */
define([
        'jquery',
        'flight/lib/component',
],
function(
    $,
    defineComponent) {
  "use strict";
  // return flightJS component
  return defineComponent(SearchQueryFiltersWidget);

  /**
   * Widget Displaying the query filters as text.
   *
   * Listens on:
   * - facetsSet:
   *     => {facetsFilter: <FacetsFilter>, serializedFacetsFilter: <serialized filter>}
   *     Display the new serialized facets filter.
   * Sends:
   * - facetsEdit:
   *     => {}
   *     When the edit button is clicked.
   */
  function SearchQueryFiltersWidget() {
    this.attributes({
      // element containing the query text
      searchQueryFiltersTextSelector: undefined,
      // button enabling the query edition
      searchQueryFiltersEditSelector: undefined,
    });


    this.after('initialize', function() {
      /**
       * Update the displayed query filter after receiving event "facetsSet".
       */
      this.on(document, 'facetsSet', function(ev, data) {
        var that = this; 
        // get facet filters serialized as a query.
        var serializedFacetsFilter = data.serializedFacetsFilter;

        // mark the element as empty if the quey is empty
        if (!serializedFacetsFilter) {
          this.$node.addClass('empty');
          return;
        }
        this.$node.removeClass('empty');
        // update the displayed facets filter query
        $(this.attr.searchQueryFiltersTextSelector).text(serializedFacetsFilter);
      });


      // listen on the "query filter" edit button clicks
      this.on(this.attr.searchQueryFiltersEditSelector, 'click', function(ev, data) {
        // broadcast the event
        this.trigger(document, 'facetsEdit', {});
      });
    });
  }
});
