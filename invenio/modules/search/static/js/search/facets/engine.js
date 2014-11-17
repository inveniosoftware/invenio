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
  'js/search/facets/filter'
], function($, Filter) {

  // provides $.fn.facet

  "use strict";

  /**
   * The engine which gathers all the active facet
   * filters and generates the query.
   *
   * @param element
   * @param options
   * @constructor
   */
  function Engine(element, options) {
    this.$element = $(element);

    this.options = $.extend({}, $.fn.facet.defaults, options, {
      option_details: $.extend({}, options.option_details),
      list_details: $.extend({}, options.list_details),
      filter_details: $.extend({}, options.filter_details),
      translations: $.extend(
        {}, $.fn.facet.defaults.translations, options.translations),
    });

    /**
     * dict with all the filter gui elements
     * @type {{id: {Filter}}}
     */
    this.filters = {};
    this.filter_wrapper = '<div class="facet-filter"></div>';
    this.is_loaded = false;
    this.translations = this.options.translations;
  }

  var dataLabel = 'facet-engine';

  Engine.events = {
    /**
     * State of the facets has changed.
     */
    updated: 'updated',
  };

  Engine.prototype = {

    events: Engine.events,

    init: function() {

      var that = this;

      var facets = this.options.facets;

      this.initCss();

      this.options.url_map = {};

      for (var i in facets) {
        var f = facets[i];
        var $new_filter = $(this.filter_wrapper);
        this.$element.append($new_filter);

        var facet_id = f.facet;

        this.filters[facet_id] = $new_filter.facet_filter($.extend({}, this.options.filter_details, {
          url: f.url,
          header: f.title,
          id: facet_id,
          facet_engine: this,
          option_details: this.options.option_details,
          list_details: this.options.list_details,
          activate_modifier_keys: this.options.activate_modifier_keys,
          translations: this.translations,
        }))[0];

        $new_filter.on(Filter.events.updated, function(event) {
          that.$element.trigger(that.events.updated);
        });
      }
      this.loaded_promise = $.when.apply(this, $.map(this.filters,
        function(item, idx) {
          return item.loadedPromise;
        }
      )).done(function() {
        this.is_loaded = true;
      }.bind(this));
    },

    /**
     * Destructor
     */
    destroy: function() {
      $('link[title="' + dataLabel + '"]').remove();
      this.$element.html('');
      this.$element.unbind();
      this.$element.removeData(dataLabel);
    },

    /**
     * Add css stylesheet of the facets theme.
     */
    initCss: function() {
      if (!this.options.stylesheet) {
        return;
      }
      this.$element.addClass(this.options.main_css_class);
      $('head').append(
          '<link rel="stylesheet" type="text/css" title="' + dataLabel + '" ' +
          'href="'+ this.options.stylesheet +'">'
      );
    },

    /**
     * Extracts the state of facets, so that it can be reverted by
     * loadState()
     *
     * @returns {{}}
     */
    getState: function() {
      return this._gatherResults('getState');
    },

    getQueryStructure: function() {
      return this._gatherResults('getQueryStructure');
    },

    /**
     * Gather results of methods of filters in format:
     * {
     *   filterName: result,
     *   filterName: result,
     *   ...
     * }
     *
     * @param {String} methodName
     * @returns {{}}
     * @private
     */
    _gatherResults: function(methodName) {
      var results = {};
      for (var i in this.filters) {
        var filter = this.filters[i];
        var result = filter[methodName]();
        if (result && Object.keys(result).length) {
          results[filter.id] = result;
        }
      }
      return results;
    },

    /**
     * Loads state saved before with getState()
     *
     * @param saved_state
     */
    loadState: function(saved_state) {
      // reset if saved state is empty
      if (!saved_state || !Object.keys(saved_state)) {
        for (var i in this.filters) {
          var filter = this.filters[i];
          filter.deactivate();
        }
      }

      for (var box_id in saved_state) {
        var filter = this.filters[box_id];
        filter.loadState(saved_state[box_id]);
      }
    }
  };

  $.fn.facet = function (option) {

    var $elements = this;

    return $elements.map(function (idx, element) {
      var $element = $(element);
      var object = $element.data(dataLabel);
      var options = typeof option == 'object' && option;
      // attach jQuery plugin
      if (!object) {
        object = new Engine($element, options);
        $element.data(dataLabel, object);
        object.init();
      }
      return object;
    });
  };

  $.fn.facet.defaults = {
    /**
     * Path of an additional stylesheet for facets to load.
     * @type {String}
     */
    stylesheet: null,
    /**
     * The class of the facets section.
     * @type {String}
     */
    main_css_class: 'facet-list',
    /**
     * Should modifier keys be used.
     *
     * Currently 'shift' changes the behaviour to 'exclude'.
     */
    activate_modifier_keys: false,
  };

});
