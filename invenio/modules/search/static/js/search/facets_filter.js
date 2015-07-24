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


define([],
function() {
  "use strict";

  /**
   * FacetsFilter is a description of how facet are filtered.
   * Filtering is done by either including or excluding a facet value.
   */
  function FacetsFilter(filters) {
    this.filters = filters || {};
  }

  /**
   * Retrieve the filters as a dictionary.
   *
   * @return {Object} A dict of facet_name -> { exc: [excluded_values], inc: [included_values] }
   */
  FacetsFilter.prototype.getFilters = function() {
    return this.filters;
  }

  /**
   * Create if it doesn't exist, and return a given facet's filter.
   *
   * @param {String} facetName facet name.
   * @return {Object} filters for the given facet name.
   */
  FacetsFilter.prototype.getOrCreateFilter = function(facetName) {
    var filter = this.filters[facetName];
    if (filter === undefined) {
      filter = { inc: [], exc: [] };
      this.filters[facetName] = filter;
    }
    return filter;
  }

  /**
   * Include a facet's value
   *
   * @param {String} facetName facet name
   * @param {string} value facet's value
   */
  FacetsFilter.prototype.includeFacetValue = function(facetName, value) {
    var filter = this.getOrCreateFilter(facetName)
    filter.inc.push(value);
  }

  /**
   * Exclude a facet's value
   *
   * @param {String} facetName facet name
   * @param {string} value facet's value
   */
  FacetsFilter.prototype.excludeFacetValue = function(facetName, value) {
    var filter = this.getOrCreateFilter(facetName)
    filter.exc.push(value);
  }

  /**
   * Remove any filtering on a given facet's value.
   *
   * @param {String} facetName facet name
   * @param {String} value facet's value
   */
  FacetsFilter.prototype.resetFacetValue = function(facetName, value) {
    var filter = this.getOrCreateFilter(facetName)
    var excIdx = filter.exc.indexOf(value);
    if (excIdx >= 0) {
      filter.exc.splice(excIdx, 1);
    }
    var incIdx = filter.inc.indexOf(value);
    if (incIdx >= 0) {
      filter.inc.splice(incIdx, 1);
    }
    if (filter.inc.length === 0 && filter.exc.length === 0) {
        delete this.filters[facetName];
    }
  }

  return FacetsFilter;

});
