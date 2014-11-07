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
  'jquery',
  'jasmine/spec/invenio.modules.search/facets/mocks',
  'js/search/facets/states',
  'js/search/facets/filter',
  'jasmine-boot',
  'jasmine-jquery',
  'jasmine-ajax',
], function($, mocks, states, Filter) {

  jasmine.getFixtures().fixturesPath = '/jasmine/spec/invenio.modules.search/';

  loadFixtures('simple_div.html');

  var filter;

  var $facetEngine = $('#simpleDiv2');
  var $filter = $('#simpleDiv4');

  var facetEngineMock = mocks.facetEngineGenerator($facetEngine);

  var savedStateMock = {
    filter_collections: {
      '+': ['Reports', 'Multimedia', 'Photos']
    }
  };

  var savedStateMock2 = {
    filter_collections: {
      '+': ['Articles & Preprints']
    }
  };

  function attachFilter(options) {
    $filter.facet_filter($.extend({}, mocks.filterConfiguration, {
      url: 'mockFilterURL',
      header: 'Test filter',
      id: 'test_filter',
      facet_engine: facetEngineMock,
      filter_area: 'test_area',
    }, options));
    filter = $filter.data('facet-filter');
  }

  function removeFilter() {
    filter.destroy();
    filter = undefined;
  }

  describe('Filter', function () {

    beforeEach(function() {
      jasmine.Ajax.install();
      attachFilter();
      spyOn(filter, '_loadState').and.callThrough();
    });

    afterEach(function() {
      removeFilter();
      jasmine.Ajax.uninstall();
    });

    it('has all properties initialized', function() {
      expect(filter).toHaveAllPropertiesInitialized();
      expect(filter).toHaveNoEmptyJQueryObjects();
    });

    it('is deactivated by default', function() {
      expect(filter.isActive()).toBe(false);
    });

    it('has internal events connected', function() {
      var testedConnections = [
        {
          triggered: {
            $element: filter.$reset_button,
            event: filter.options.reset_event
          },
          expected: {
            object: filter,
            methodName: 'deactivate'
          }
        },
        {
          triggered: {
            object: filter,
            methodName: 'deactivate'
          },
          expected: {
            object: filter.options,
            methodName: 'on_deactivated'
          }
        },
        {
          triggered: {
            object: filter,
            methodName: 'deactivate'
          },
          expected: {
            $element: filter.$element,
            event: filter.events.deactivated
          }
        },
        {
          triggered: {
            object: filter,
            methodName: 'deactivate'
          },
          expected: {
            $element: filter.$element,
            event: filter.events.updated
          }
        },
      ];
      expect(testedConnections).toPassConnectionTests();
    });

    it ('does not loads the state before the content is loaded', function () {
      filter.loadState(savedStateMock);
      expect(filter._loadState).not.toHaveBeenCalled();
    });

    describe('after the content is loaded', function () {

      var listRequest;

      beforeEach(function() {
        listRequest = jasmine.Ajax.requests.mostRecent();
        listRequest.response(mocks.getResponse(200, mocks.collectionResponseMock));
      });

      describe('after the state is loaded', function() {

        var savedState;

        beforeEach(function() {
          filter.loadState(savedStateMock);
          savedState = filter.getState();
        });

        it ('loads the state, loads again, deactivates', function() {
          expect(filter._loadState).toHaveBeenCalled();
          expect(filter.isActive()).toBe(true);
          expect(savedState).toEqual(savedStateMock);
        });

        it('loads the state again', function() {
          filter.loadState(savedState);
          var savedState2 = filter.getState();
          expect(savedState).toEqual(savedState2);
        });

        it('can overwrite the state', function() {
          filter.loadState(savedStateMock2);
          expect(filter.getState()).toEqual(savedStateMock2);
          filter.loadState({});
          expect(filter.getState()).toEqual({});
        });

        it('can reset state by deactivate', function() {
          filter.deactivate();
          expect(filter.isActive()).toBe(false);
          var emptyState = filter.getState();
          expect(emptyState).toEqual({});
        });

        it('new state affects the gui', function() {
          expect(filter.getOption('Reports').getState()).toEqual('+');
          expect(filter.getOption('Multimedia').getState()).toEqual('+');
          expect(filter.getOption('Photos').getState()).toEqual('+');
        });
      });

      describe('loading state which needs expanding of options', function() {

        var articlesPreprintsRequest, nextLevelRequest;

        beforeEach(function() {
          filter.loadState({
            filter_collections: {
              '+': ['Articles', 'item2']
            },
            paths: {
              Articles: ['Articles & Preprints', 'some next level'],
              'item2': ['Articles & Preprints']
            }
          });
          articlesPreprintsRequest = jasmine.Ajax.requests.mostRecent();
          articlesPreprintsRequest.response(mocks.getResponse(200, {
            facet: [
              {
                id: "some next level",
                is_expandable: true,
                label: "some next level",
                records_num: 10,
              },
              {
                id: "item2",
                is_expandable: false,
                label: "some other item here",
                records_num: 10,
              }
            ]
          }));
          nextLevelRequest = jasmine.Ajax.requests.mostRecent();
          nextLevelRequest.response(mocks.getResponse(200, {
            facet: [
              {
                id: "Articles",
                is_expandable: false,
                label: "Articles",
                records_num: 1,
              },
              {
                id: "Articles2",
                is_expandable: false,
                label: "Articles2",
                records_num: 1,
              }
            ]
          }));
        });

        it('expands the paths', function() {
          expect(filter.getOption('Articles & Preprints').is_expanded).toBe(true);
          expect(filter.getOption('some next level').is_expanded).toBe(true);
        });

        it('activates the options', function() {
          expect(filter.getOption('Articles & Preprints').isActive()).toBe(false);
          expect(filter.getOption('some next level').isActive()).toBe(false);
          expect(filter.getOption('Articles').isActive()).toBe(true);
          expect(filter.getOption('item2').isActive()).toBe(true);
        });
      });

      describe('filter states modifications influence for saved state',
        function() {

          var updateActions;

          beforeEach(function() {
            updateActions = {
              to_add: [
                {
                  action: '+',
                  filter: filter.getOption('Reports')
                },
                {
                  action: '+',
                  filter: filter.getOption('Multimedia')
                }
              ]
            };
          });

          it('activates filters and check if they are stored in ' +
            'the state description', function() {

            filter.update(updateActions);
            var state = filter.getState();
            expect(state).toEqual({
              filter_collections: {
                '+': ['Reports', 'Multimedia']
              }
            });
            filter.update({
              to_add: [
                {
                  action: 'blabla',
                  filter: filter.getOption('Photos')
                },
              ],
              to_delete: [
                filter.getOption('Reports'),
              ],
            });
            state = filter.getState();
            expect(state).toEqual({
              filter_collections: {
                '+': ['Multimedia'],
                'blabla': ['Photos'],
              }
            });
          });

        }
      );
    });
  });
});