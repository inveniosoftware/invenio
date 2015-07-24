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


/* A file containing the FlightJS component handling the faceting panel. */
define([
        'jquery',
        'flight/lib/component',
],
function(
    $,
    defineComponent) {
  "use strict";
  // return flightJS component
  return defineComponent(FacetsMenu);

  /**
   * FacetsMenu is a FlightJS component for handling facet menu.
   *
   * NOTE: it has to be attached to the DOM before the Search component so that
   * it can listen to facetsSet event.
   *
   * Listens on:
   * - facetsSet:
   *     => {facetsFilter: <FacetsFilter>, serializedFacetsFilter: <serialized filter>}
   *     Set all facets filter.
   * Sends:
   * - facetChange:
   *     => {state: <'include'|'exclude'>, name: <facet name>, value: <filtered value>}
   *     Include or exclude a filter in the facetsFilter.
   */
  function FacetsMenu() {
    this.attributes({
      includeFacetSelector: 'input.include-facet'
    });

    /**
     * Callback called when a facet's value has been included in query filters.
     * It will broadcast the corresponding event so that other components may
     * update.
     *
     * @param {} ev 
     * @param {} data
     */
    function facetChange(ev, data) {
      this.trigger(document, 'facetChange', {
        name: data.el.name,
        value: data.el.value,
        state: data.el.checked ? 'include' : 'default',
      });
    }

    /**
     * Initialize the component
     */
    this.init = function() {
      var that = this;
      $(that.attr.includeFacetSelector).each(function(idx, elt) {
        that.on(elt, 'click', {
          includeFacetSelector: facetChange,
        });
      });
    }

    this.after('initialize', function() {
      this.init();

      /**
       * Update selected facets after receiving event "facetsSet".
       */
      this.on(document, 'facetsSet', function(ev, data) {
        var that = this; 
        var filters = data.facetsFilter.getFilters();
        // uncheck all checkboxes
        $(that.attr.includeFacetSelector).prop('checked', false);
        // check only necessary checkboxes
        $.each(filters, function(facetName, facetFilter) {
          $.each(facetFilter.inc, function(idx, value) {
            $(that.attr.includeFacetSelector +
              '[name="' + facetName + '"][value="' + value + '"]')
              .prop('checked', true);
          });
        });
      });
    });
  }
});

