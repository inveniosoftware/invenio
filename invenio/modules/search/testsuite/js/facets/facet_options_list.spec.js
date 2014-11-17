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
  'js/search/facets/states',
  'jasmine/spec/invenio.modules.search/facets/mocks',
  'js/search/facets/options_list',
  'jasmine-boot',
  'jasmine-jquery',
], function(states, mocks, OptionsList) {

  jasmine.getFixtures().fixturesPath = '/jasmine/spec/invenio.modules.search/';

  loadFixtures('simple_div.html');

  var optionsList;

  var $optionsList = $('#simpleDiv');
  var $facetEngine = $('#simpleDiv2');
  var $listParent = $('#simpleDiv3');
  var $filter = $('#simpleDiv4');

  var configurationMock = $.extend({}, $.fn.facet_options_list.defaults,
    mocks.optionListConfiguration);
  var facetEngineMock = mocks.facetEngineGenerator($facetEngine);
  var parentOptionMock = mocks.facetOptionGenerator($listParent);
  var filterMock = mocks.filter($filter);

  function attachOptionsList(options) {
    jasmine.Ajax.install();

    $optionsList.facet_options_list($.extend({}, configurationMock, {
      id: 'testList',
      facet_engine: facetEngineMock,
      filter: filterMock,
    }, options));
    optionsList = $optionsList.data('facet-options-list');
  }

  function removeOptionsList() {
    optionsList.destroy();
    optionsList = undefined;
  }

  describe('Options list', function() {

    var spyLoadedEvent, request;

    beforeEach(function() {
      jasmine.Ajax.install();
    });

    afterEach(function() {
      jasmine.Ajax.uninstall();
    });

    describe('with a parent', function() {

      beforeEach(function() {
        spyLoadedEvent = spyOnEvent($optionsList, OptionsList.events.loaded);
        attachOptionsList({parent: parentOptionMock});
        request = jasmine.Ajax.requests.mostRecent();
      });

      afterEach(function() {
        removeOptionsList();
        spyLoadedEvent = undefined;
        request = undefined;
      });

      it('makes a proper request with parent', function () {
        expect(request.url).toBe('mocked_url?parent=parentMock');
        expect(request.method).toBe('GET');
        expect(request.data()).toEqual({});
      });

      it ('has variables initialized', function () {
        expect(optionsList.name).toEqual('testList');
        expect(optionsList.facet_engine).toEqual(facetEngineMock);
        expect(optionsList.parent).toEqual(parentOptionMock);
        expect(optionsList.$list).not.toBe(undefined);
        expect(optionsList.$button_more).not.toBe(undefined);
        expect(optionsList.$button_less).not.toBe(undefined);
      });

      it ('has internal events connected', function () {
        spyOn(optionsList, 'showMore');
        spyOn(optionsList, 'showLess');
        expect(optionsList.showMore).not.toHaveBeenCalled();
        optionsList.$button_more.trigger('click');
        expect(optionsList.showMore).toHaveBeenCalled();
        expect(optionsList.showLess).not.toHaveBeenCalled();
        optionsList.$button_less.trigger('click');
        expect(optionsList.showLess).toHaveBeenCalled();
      });

      describe('after the elements are loaded', function () {

        // ':visible' selector doesn't work in tests hence it doesn't really
        // check 'display' value, which is changed by show()/hide() methods of
        // jquery.
        // The main reason may be that the elements are not really displayed.
        // explaination here:
        // http://blog.jquery.com/2009/02/20/jquery-1-3-2-released/
        var visibleSelector = "[style!='display: none;']";
        var notVisibleSelector = "[style$='display: none;']";

        beforeEach(function() {
          request.response(mocks.listEntriesQueryMock.success);
        });

        it('has all options loaded', function() {
          expect(optionsList.$options.length)
            .toEqual(mocks.listEntriesMock.facet.length);
        });

        it('has split_by options shown', function() {
          expect(optionsList.$options.filter(visibleSelector).length)
            .toEqual(optionsList.split_by);
        });

        // this doesn't work because of broken `:visible` selector when tests
        // are run
//        it('has button `more` visible cause there are more options to show',
//          function() {
//            optionsList.$button_more.css('display', 'block')
//            expect(optionsList.$button_more).toBeVisible();
//          }
//        );

        it ('has button `less` hidden', function () {
          expect(optionsList.$button_less).toBeHidden();
        });

        it ('has working "show more/less" mechanism', function () {
          // there are 5 items, and split_by is set to 2
          optionsList.showMore();
          expect(optionsList.$options.filter(visibleSelector).length)
            .toEqual(4);
          optionsList.showMore();
          expect(optionsList.$options.filter(visibleSelector).length)
            .toEqual(5);
          optionsList.showLess();
          expect(optionsList.$options.filter(visibleSelector).length)
            .toEqual(3);
          optionsList.showLess();
          expect(optionsList.$options.filter(visibleSelector).length)
            .toEqual(2);
        });
      });

    });

    describe('without a parent', function() {

      beforeEach(function() {
        spyLoadedEvent = spyOnEvent($optionsList, OptionsList.events.loaded);
        attachOptionsList();
        request = jasmine.Ajax.requests.mostRecent();
      });

      afterEach(function() {
        removeOptionsList();
        spyLoadedEvent = undefined;
        request = undefined;
      });

      it('makes a proper request', function () {

        expect(request.url).toBe('mocked_url');
        expect(request.method).toBe('GET');
        expect(request.data()).toEqual({});

        expect(spyLoadedEvent).not.toHaveBeenTriggered();
        request.response(mocks.listEntriesQueryMock.success);
        expect(spyLoadedEvent).toHaveBeenTriggered();
      });

      it ('has parent "undefined"', function () {
        expect(optionsList.parent).toBe(undefined);
      });

    });
  });

});