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
  'jasmine/spec/invenio.modules.search/facets/mocks',
  'js/search/facets/states',
  'js/search/facets/option',
  'jasmine-boot',
  'jasmine-jquery',
  'jasmine-ajax',
], function(mocks, states) {

  jasmine.getFixtures().fixturesPath = '/jasmine/spec/invenio.modules.search/';

  loadFixtures('simple_div.html');

  var $facetOption = $('#simpleDiv');
  var $filter = $('#simpleDiv2');

  var configurationMock = mocks.optionConfiguration;
  var optionContent = mocks.optionContent;
  var filterMock = mocks.filter($filter);

  function attachFacet(jasmine) {
    $facetOption.facet_option($.extend({}, configurationMock, {
      entry: optionContent,
      filter: filterMock,
    }));
    jasmine.facetOption = $facetOption.data('facet-option');
  }

  function removeFacet(jasmine) {
    jasmine.facetOption.destroy();
    jasmine.facetOption = undefined;
  }

  describe("Facet option", function() {

    beforeEach(function() {
      jasmine.Ajax.install();
    });

    afterEach(function() {
      jasmine.Ajax.uninstall();
    });

    describe("destruction", function () {

      it('doesn\'t leave html after destruction', function () {
        $facetOption.facet_option($.extend({}, configurationMock, {
          entry: optionContent,
          filter: filterMock,
        }));
        var facetOption = $facetOption.data('facet-option');
        facetOption.destroy();
        expect($facetOption.html()).toEqual('');
      });

      it('doesn\'t leave data in facet-option data key after destruction',
        function () {
          $facetOption.facet_option($.extend({}, configurationMock, {
            entry: optionContent,
            filter: filterMock,
          }));
          var facetOption = $facetOption.data('facet-option');
          facetOption.destroy();
          expect($facetOption.data('facet-option')).toEqual(undefined);
        }
      );
    });

    describe("initialization", function() {

      beforeEach(function() {
        spyOn(configurationMock, 'on_deactivated').and.callThrough();
        spyOn(configurationMock, 'disable_expansion').and.callThrough();
        attachFacet(this);
      });

      afterEach(function() {
        removeFacet(this);
      });

      it('is stored at facet-option key', function() {
        expect(this.facetOption).not.toBe(undefined);
      });

      it('has inactive state by default', function () {
        expect(this.facetOption.getState()).toBe(states.inactive);
        expect(this.facetOption.isActive()).toBe(false);
      });

      it('calls on_deactivated after applying default inactive state',
        function() {
          expect(configurationMock.on_deactivated).toHaveBeenCalled();
          expect(configurationMock.on_deactivated)
            .not.toHaveBeenCalledWith(undefined);
        }
      );

      it('calls disable_expansion on object creation ' +
          'because is_expandable is false',
        function() {
          expect(configurationMock.disable_expansion).toHaveBeenCalled();
          expect(configurationMock.disable_expansion)
            .not.toHaveBeenCalledWith(undefined);
        }
      );
    });

    describe('state changes', function () {
      beforeEach(function() {
        spyOn(configurationMock, 'on_activated');
        spyOn(configurationMock, 'on_deactivated');
        spyOn(filterMock, 'update');
        attachFacet(this);
      });

      afterEach(function() {
        removeFacet(this);
      });

      it('has a proper state activated after activation/deactivation',
        function() {
          this.facetOption.activate(states.limitTo);
          expect(this.facetOption.getState()).toBe(states.limitTo);
          expect(this.facetOption.isActive()).toBe(true);
          this.facetOption.activate(states.exclude);
          expect(this.facetOption.getState()).toBe(states.exclude);
          expect(this.facetOption.isActive()).toBe(true);
          this.facetOption.deactivate(states.exclude);
          expect(this.facetOption.getState()).toBe(states.inactive);
          expect(this.facetOption.isActive()).toBe(false);
        }
      );

      it('treats partially active state as inactive - a child ' +
        'is active then', function() {
        this.facetOption._setState(states.partiallyActive);
        expect(this.facetOption.isActive()).toBe(false);
      });

      it('calls on_activated on activation', function() {
        this.facetOption.activate(states.limitTo);
        expect(configurationMock.on_activated).toHaveBeenCalled();
        expect(configurationMock.on_activated)
          .not.toHaveBeenCalledWith(undefined);
      });

      it('calls on_deactivated on deactivation', function() {
        this.facetOption.activate(states.limitTo);
        this.facetOption.deactivate(states.limitTo);
        expect(configurationMock.on_deactivated).toHaveBeenCalled();
      });

      it('calls update method of the filter cause it doesn\'t have parent ' +
        'to propagate', function() {
        this.facetOption.activate(states.limitTo);
        expect(filterMock.update).toHaveBeenCalled();
      });

      it('calls update method of the filter cause it doesn\'t have parent ' +
        'to propagate', function() {
        this.facetOption.activate(states.exclude);
        expect(filterMock.update).toHaveBeenCalled();
      });

      it('calls update method of the filter cause it doesn\'t have parent ' +
        'to propagate', function() {
        this.facetOption._setState(states.limitTo);
        expect(filterMock.update).not.toHaveBeenCalled();
        this.facetOption.deactivate();
        expect(filterMock.update).toHaveBeenCalled();
      });
    });

    describe('events', function() {

      beforeEach(function () {
        $facetOption.facet_option($.extend({}, configurationMock, {
          entry: optionContent,
          filter: filterMock,
          activate_modifier_keys: true,
        }));
        this.facetOption = $facetOption.data('facet-option');
      });

      afterEach(function () {
        this.facetOption.destroy();
        this.facetOption = undefined;
      });

      it('has state `exclude` when activated with shift', function() {
        var shiftToggled = jQuery.Event(
          this.facetOption.options.toggle_filter_event);
        shiftToggled.shiftKey = true;
        this.facetOption.$toggle_filter_button.trigger(shiftToggled);
        expect(this.facetOption.getState()).toBe(states.exclude);
      });

      it('has state `limitTo` when activated without shift', function() {
        var noShiftToggled = jQuery.Event(
          this.facetOption.options.toggle_filter_event);
        noShiftToggled.shiftKey = false;
        this.facetOption.$toggle_filter_button.trigger(noShiftToggled);
        expect(this.facetOption.getState()).toBe(states.limitTo);
      });

      it('has state `deactivated` when toggled after the state was ' +
        'active and shift not pressed', function() {
        var toggledEvent = this.facetOption.options.toggle_filter_event;
        this.facetOption.$toggle_filter_button.trigger(toggledEvent);
        this.facetOption.$toggle_filter_button.trigger(toggledEvent);
        expect(this.facetOption.getState()).toBe(states.inactive);
      });

      it('has state `deactivated` when toggled after the state was ' +
        'active and shift pressed', function() {
        var shiftToggled = jQuery.Event(
          this.facetOption.options.toggle_filter_event);
        shiftToggled.shiftKey = true;
        this.facetOption.$toggle_filter_button.trigger(shiftToggled);
        this.facetOption.$toggle_filter_button.trigger(shiftToggled);
        expect(this.facetOption.getState()).toBe(states.inactive);
      });

      it('triggers `activated` event on activated, and `deactivated` ' +
        'when deactivated', function() {
        var toggledEvent = this.facetOption.options.toggle_filter_event;
        var spyActivated = spyOnEvent(
          $facetOption, this.facetOption.events.activated);
        var spyDeactivated = spyOnEvent(
          $facetOption, this.facetOption.events.activated);
        this.facetOption.$toggle_filter_button.trigger(toggledEvent);
        expect(spyActivated).toHaveBeenTriggered();
        this.facetOption.$toggle_filter_button.trigger(toggledEvent);
        expect(spyDeactivated).toHaveBeenTriggered();
      });

    });

    var articlesResponseMock = {
      facet: [
        {
          id: "Articles",
          is_expandable: false,
          label: "Articles",
          records_num: 32
        },
        {
          id: "Preprints",
          is_expandable: false,
          label: "Preprints",
          records_num: 37
        }
      ]
    };

    describe('expandable option with initial state', function() {

      var expandRequest, articles, preprints;

      function getOption($element, id) {
        var $option = $element.find('[data-facet-name="' + id + '"]');
        if ($option) {
          return $option.data('facet-option');
        }
        // else return undefined
      }

      beforeEach(function() {
        spyOn(configurationMock, 'on_partially_activated');
        optionContent.is_expandable = true;
        attachFacet(this);
        this.facetOption.activate('+');
        this.facetOption.expand();
        expandRequest = jasmine.Ajax.requests.mostRecent();
        expandRequest.response(mocks.getResponse(200, articlesResponseMock));
        articles = getOption(this.facetOption.$element, 'Articles');
        preprints = getOption(this.facetOption.$element, 'Preprints');
      });

      afterEach(function() {
        expandRequest = undefined;
        articles = undefined;
        preprints = undefined;
        removeFacet(this);
      });

      it('initializes children with its state', function() {
        expect(this.facetOption.getState()).toBe('+');
        expect(articles.getState()).toBe('+');
        expect(preprints.getState()).toBe('+');
      });

      it('properly propagates state', function() {

        this.facetOption.deactivate();
        expect(this.facetOption.getState()).toBe(states.inactive);
        expect(articles.getState()).toBe(states.inactive);
        expect(preprints.getState()).toBe(states.inactive);

        articles.activate('+');
        expect(this.facetOption.getState()).toBe(states.partiallyActive);
        expect(configurationMock.on_partially_activated).toHaveBeenCalled();
        expect(configurationMock.on_partially_activated)
          .not.toHaveBeenCalledWith(undefined);

        preprints.activate('+');
        expect(this.facetOption.getState()).toBe('+');

        preprints.deactivate();
        expect(this.facetOption.getState()).toBe(states.partiallyActive);

        articles.deactivate();
        expect(this.facetOption.getState()).toBe(states.inactive);
      });

      it('does not activate a parent option when child are not identical',
        function () {
          this.facetOption.deactivate();
          articles.activate('+');
          expect(this.facetOption.getState()).toBe(states.partiallyActive);
          preprints.activate('a');
          expect(this.facetOption.getState()).toBe(states.partiallyActive);
        }
      );

    });
  });

});
