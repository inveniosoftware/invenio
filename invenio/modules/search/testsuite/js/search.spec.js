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

define([
  'js/search/search',
  'js/search/hash_storage',
  'jasmine/spec/invenio.modules.search/facets/mocks',
  'jasmine-boot',
  'jasmine-jquery',
  'jasmine-ajax',
], function(SearchResultsPage, HashStorage, mocks) {

  jasmine.getFixtures().fixturesPath = '/jasmine/spec/invenio.modules.search/';
  loadFixtures('search_results.html');

  var $searchField = $('input[name="search-field"]');
  var $facets = $('#facets');

  var page;
  var pageConf = {
    $facets_element: $facets,
    $search_results: $('#search-results'),
    $search_query_field: $searchField,
    facets_configuration: {
      option_details: mocks.optionConfiguration,
      filter_details: mocks.filterConfiguration
    },
    request_args: {"action_search": "", "ln": "en", "p": ""},
    search_url: '/search',
    facets_content: mocks.facetsContentMock,
  };

  var collectionRequest;
  var yearRequest;
  var $filters;
  var collectionFilter;
  var yearFilter;

  function initFacets() {
    collectionRequest = jasmine.Ajax.requests.filter('/facet/collection/mock').pop();
    yearRequest = jasmine.Ajax.requests.filter('/facet/year/mock').pop();
    yearRequest.response(mocks.listEntriesQueryMock.success);
    collectionRequest.response(mocks.getResponse(200, mocks.collectionResponseMock));
    $filters = page.facet_engine.$element.children().filter('.facet-filter');
    collectionFilter = $($filters[1]).data('facet-filter');
    yearFilter = $($filters[0]).data('facet-filter');
  }

  describe('Search results page', function() {

    beforeEach(function() {
      jasmine.Ajax.install();
    });

    afterEach(function() {
      page.destroy();
      page = undefined;
      HashStorage.clean();
      jasmine.Ajax.uninstall();
    });

    describe('with empty hash', function() {

      beforeEach(function() {
        page = new SearchResultsPage(pageConf);
        initFacets();
      });

      it('has no undefined properties nor empty jQuery objects', function() {
        expect(page).toHaveAllPropertiesInitialized();
        expect(page).toHaveNoEmptyJQueryObjects();
      });

      it('has internal events connected', function() {
        var testedConnections = [
          {
            triggered: {
              $element: $facets,
              event: page.facet_engine.events.updated,
            },
            expected: {
              object: HashStorage,
              methodName: 'update'
            },
          },
          {
            triggered: {
              $element: $facets,
              event: page.facet_engine.events.updated,
            },
            expected: {
              object: page,
              methodName: 'updateSearchResults'
            },
          },
        ];
        expect(testedConnections).toPassConnectionTests();
      });

      it('doesn\'t modify external pageConf.request_args', function() {
        yearFilter.getOption('2002').activate('+');
        expect(pageConf.request_args.p).toEqual('');
      });

      it('generates query when facets state changes', function() {
        yearFilter.getOption('2002').activate('+');
        yearFilter.getOption('2000').activate('-');
        expect($searchField.val()).toEqual('year:2002 AND NOT year:2000')
      });

    });

    describe('when loaded with initial facets state in the hash', function() {

      var engine;

      beforeEach(function() {
        HashStorage.update({
          year: {
            filter_collections: {
              '+': ['1972', '2001'],
            }
          },
          collection: {
            filter_collections: {
              '-': ['Reports'],
            }
          }
        });
        page = new SearchResultsPage(pageConf);
        engine = $facets.data('facet-engine');
        initFacets();
      });

      it('runs the loadState of facets', function() {
        expect(yearFilter.getOption('2001').getState()).toEqual('+');
        expect(yearFilter.getOption('1972').getState()).toEqual('+');
        expect(collectionFilter.getOption('Reports').getState()).toEqual('-');
      });

    });

    it('doesn\'t change the state on refresh', function() {
      page = new SearchResultsPage(pageConf);
      initFacets();

      yearFilter.getOption('2002').activate('+');
      expect(yearFilter.getState()).toEqual({
        filter_collections: {
          '+': ['2002']
        }
      });
      expect($searchField.val()).toEqual('year:2002');
      expect(HashStorage.getContent()).toEqual({
        year: {
          filter_collections: {
            '+': ['2002']
          }
        }
      });

      // destroy everything but the hash state
      page.destroy();
      page = undefined;
      $searchField.val('');

      // initialize again
      page = new SearchResultsPage(pageConf);
      initFacets();

      expect(yearFilter.getState()).toEqual({
        filter_collections: {
          '+': ['2002']
        }
      });
      expect($searchField.val()).toEqual('year:2002');
      expect(HashStorage.getContent()).toEqual({
        year: {
          filter_collections: {
            '+': ['2002']
          }
        }
      });
    });
  });
});
