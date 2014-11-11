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
  'js/search/facets/options_list',
], function($) {

  "use strict";

  var DEBUG = false;
  var dataLabel = 'facet-filter';

  /**
   * One of many filters at facets sidebar
   *
   * @class Filter
   */
  function Filter(element, options) {

    this.$element = $(element);
    this.options = $.extend({}, $.fn.facet_filter.defaults, {
      translations: $.extend(
        {}, $.fn.facet_filter.defaults.translations, options.translations),
    }, options);

    /**
     * Has value 'true' when the filter content loading is finished
     *
     * @property is_loaded
     * @type {boolean}
     * @default false
     */
    this.is_loaded = false;

    this.url = this.options.url;
    this.header = this.options.header;
    this.id = this.options.id;
    this.filter_area = this.id;
    this.facet_engine = this.options.facet_engine;
    this.translations = this.options.translations;

    this.$element.append(this.options.template({
      header: this.header,
      any: this.translations.any,
    }));

    this.$reset_button = this.$element.find(
      this.options.reset_button_selector);

    this.$main_facet_box = this.$element.find(this.options.content_selector);

    /**
     * Collects ids of facet options with activated filters.
     *
     * Structure:
     * {
     *   filter_type (state): {
     *     facet_option_id: parent_path
     *     facet_option_id: parent_path
     *     ...
     *   }
     *   filter_type (state): {
     *     facet_option_id: parent_path
     *     facet_option_id: parent_path
     *     ...
     *   }
     *   ...
     * }
     *
     * @property filter_collections
     * @type {Object}
     * @default {}
     */
    this.filter_collections = {};

    /**
     * Collects ids of facet options with activated filters.
     *
     * Structure:
     * {
     *   option_id (state): parent_path
     *   ...
     * }
     *
     * @property filter_collections
     * @type {Object}
     * @default {}
     */
    this.paths = {};

    /**
     * A temporary variable to store a filter state if it cannot be restored
     * immediately. This happens when the filter is being loaded using
     * the ajax query in background at the moment of triggering loadState()
     * function.
     *
     * @property stored_state
     * @type {Object}
     */
    this.stored_state = {};
  }

  /**
   * All events emitted by the class.
   */
  Filter.events = {
    /**
     * Triggered when the filter content is ready.
     */
    loaded: 'filter_loaded',
    /**
     * Triggered when the filter is deactivated on reset button pressed or on
     * deactivate() method call.
     */
    deactivated: 'filter_deactivated',
    /**
     * Triggered when filter configuration changes.
     *
     * @event updated
     */
    updated: 'filter_updated',
  };

  Filter.prototype = {

    events: Filter.events,

    init: function () {

      var that = this;

      // create the main list of options
      this.loadedPromise = this.$main_facet_box.facet_options_list(
        $.extend({}, this.options.list_details, {

          option_details: this.options.option_details,
          list_details: this.options.list_details,
          translations: this.translations,

          facet_engine: this.facet_engine,
          filter: this,
          parent: null, // no parent, first level options
          activate_modifier_keys: this.options.activate_modifier_keys
        })
      )[0].loadedPromise.then(function () {
        that._loadState(that.stored_state);
        that.is_loaded = true;
      });

      this.options.on_deactivated(this.$element);
    },

    /**
     * Destructor
     */
    destroy: function() {
      this.$element.html('');
      this.$element.unbind();
      this.$element.removeData(dataLabel);
    },

    /**
     * Connects the events
     */
    connectEvents: function() {
      var that = this;

      this.$reset_button.on(this.options.reset_event, function(e) {
        that.deactivate();
      });
    },

    /**
     * Returns all filters of given type (having given state).
     * Possible states are in js/search/facets/states.js
     *
     * @param type
     * @returns {*}
     */
    getFilters: function(type) {
      if (!this.filter_collections[type])
        return [];
      return this.filter_collections[type];
    },

    /**
     * Print out the state for debugging
     *
     * @private
     */
    _printFilters: function _printFilters() {
      console.log('>>>>>>>>>>>>>>>>');
      for (var name in this.filter_collections) {
        console.log('---------------');
        console.log('Collection ' + name + ':');
        var collection = this.filter_collections[name];
        for (var i in collection) {
          console.log(i);
        }
      }

      console.log('>>>>>>>>>>>>>');
    },

    /**
     * Add filter option to the filter state.
     *
     * @param filter {Option} option
     * @param action {states}
     * @private
     */
    _addFilter: function(filter, action) {

      var id = filter.getId();

      // create collection if doesn't exist
      if (this.filter_collections[action] == undefined)
        this.filter_collections[action] = [];

      // already there
      if (id in this.filter_collections[action])
        return;

      // parent_path can be undefined if the item is at the main level
      this.filter_collections[action].push(id);
      if (filter.getParentPath().length) {
        this.paths[id] = filter.getParentPath();
      }

      if (DEBUG) console.log("AddFilter: " + id + ' ' + action);
    },

    /**
     * Remove filter option from the filter state.
     *
     * @param filter {Option} option
     * @private
     */
    _removeFilter: function(filter) {
      var collection_id;
      var id_to_delete = filter.getId();
      var idx_in_collection;
      for(var idx in this.filter_collections) {
        idx_in_collection = this.filter_collections[idx].indexOf(id_to_delete);
        if (idx_in_collection !== -1) {
          collection_id = idx;
          break;
        }
      }
      if (!collection_id)
        return;

      delete this.filter_collections[collection_id].splice(idx_in_collection, 1);
      delete this.paths[id_to_delete];

      if (!Object.keys(this.filter_collections[collection_id]).length) {
        delete this.filter_collections[collection_id];
      }
      if (DEBUG) console.log("RemoveFilter: " + id_to_delete);
    },

    /**
     * Returns an object describing filter state. This object can
     * be used later to retrieve the state using loadState() method
     *
     * @method getState
     */
    getState: function () {
      var state = {};
      if (this.filter_collections && Object.keys(this.filter_collections).length > 0) {
        state.filter_collections = $.extend({}, this.filter_collections);
      }
      if (this.paths && Object.keys(this.paths).length > 0) {
        state.paths = $.extend({}, this.paths);
      }
      return state;
    },

    /**
     * Returns query in object format.
     * @returns {{}}
     */
    getQueryStructure: function() {
      var query = {};
      if (this.filter_collections && Object.keys(this.filter_collections).length > 0) {
        query = $.extend(query, this.filter_collections);
      }
      return query;
    },

    /**
     * Loads previously saved state in lazy mode.
     *
     * If the filter is ready it is going to be called immediatelly.
     * If it is not then the state is going to be loaded when the
     * filter is ready.
     *
     * @param saved_state
     */
    loadState: function loadState(saved_state) {

      var stored_state = $.extend({}, saved_state);

      // if not loaded this function will be executed again
      // with the value this.stored_state as the argument,
      // when the filter is ready from deferred in constructor.
      if (!this.is_loaded) {
        this.stored_state = saved_state;
        return;
      }

      this._loadState(stored_state);
    },

    /**
     * Returns Option object with given id from all of children in DOM.
     *
     * @param id {String} option id
     * @returns {Option}
     */
    getOption: function getOption(id) {
      var $option = this.$element.find('[data-facet-name="' + id + '"]');
      if ($option) {
        return $option.data('facet-option');
      }
      // else return undefined
    },

    /**
     * Loads previously saved state.
     *
     * Don't use it externally. If the filter content is not loaded yet,
     * the state will not be properly loaded too!
     *
     * @method _loadState
     * @param saved_state a state saved with getState() method
     * @private
     */
    _loadState: function _loadState(saved_state) {

      var that = this;

      // reset first
      this._deactivate();

      // nothing to load
      if (!Object.keys(saved_state).length) {
        return;
      }

      if (DEBUG) console.log('------- Loaded state: ---------');

      this.filter_collections = saved_state.filter_collections;
      this.paths = $.extend({}, saved_state.paths);

      if (DEBUG) this._printFilters();
      if (DEBUG) console.log('------- Rebuilding the gui ---------');

      rebuildGuiState(this.filter_collections, this.paths);
      that.options.on_activated(that.$element);

      /**
       * Rebuilds state off all the options basing on the loaded state.
       *
       * @param filter_collections
       * @returns {$.Deferred} promise of gui rebuilt
       */
      function rebuildGuiState(filter_collections, paths) {

        return expandPaths(paths).then(
          restoreOptionsState,
          restoreOptionsState
        );

        function restoreOptionsState() {
          for (var state in filter_collections) {
            var collection = filter_collections[state];
            for (var idx in collection) {
              var option = that.getOption(collection[idx]);
              if (!option)
                continue;
              option._activate(state);
            }
          }
        }

        /**
         * Expands recursively the path, after expanding runs the callback
         *
         * @param path_array an array with path nodes ids
         */
        function expandPaths(paths) {

          // maps paths to expand tasks in form of deferred objects
          var singlePromises = $.map(paths, function(path, id) {

            var promise = $.Deferred().resolve();
            $.each(path, function(idx, id) {
              // chain expanding of the levels
              promise = promise.then(function() {
                var node = that.getOption(id);
                if (!node) {
                  return $.Deferred().reject();
                }
                return node.expand();
              });
            });
            return promise;
          });

          // return the promise of all paths expanded
          return $.when.apply(this, singlePromises);
        }
      }
    },

    /**
     * For internal use, doesn't emit events.
     * @private
     */
    _deactivate: function() {
      this.filter_collections = {};
      if (DEBUG) console.log('Reseted');
      if (DEBUG) this._printFilters();
      this.options.on_deactivated(this.$element);
    },

    /**
     * Resets the filter to state when it passes all the search results.
     */
    deactivate: function() {
      this._deactivate();
      this.$element.trigger(this.events.updated);
      this.$element.trigger(this.events.deactivated);
    },

    /**
     * Checks if the filter is active
     *
     * @returns {boolean}
     */
    isActive: function isActive() {
      return !!Object.keys(this.filter_collections).length;
    },

    /**
     * Updates the filter status with the actions collected in update_actions
     * parameter.
     *
     * @param update_actions
     */
    update: function(update_actions) {

      // when no update_actions
      if ((!update_actions.to_add || !update_actions.to_add.length) &&
        (!update_actions.to_delete || !update_actions.to_delete.length))
        return;

      var was_active = this.isActive();

      for (var i in update_actions.to_delete) {
        var filter = update_actions.to_delete[i];
        this._removeFilter(filter);
      }

      for (var i in update_actions.to_add) {
        var to_add = update_actions.to_add[i];
        this._addFilter(to_add.filter, to_add.action);
      }

      if (DEBUG) this._printFilters();

      var is_active = this.isActive();
      if (!was_active && is_active)
        this.options.on_activated(this.$element);

      if (was_active && !is_active)
        this.options.on_deactivated(this.$element);

      this.$element.trigger(this.events.updated);
    },

    getSearchArea: function getSearchArea() {
      return this.options.filter_area;
    }
  };

  $.fn.facet_filter = function (option) {

    var $elements = this;

    return $elements.map(function (idx, element) {
      var $element = $(element);
      var object = $element.data(dataLabel);
      var options = typeof option == 'object' && option;
      // attach jQuery plugin
      if (!object) {
        object = new Filter($element, options);
        $element.data(dataLabel, object);
        object.init();
        object.connectEvents();
      }
      return object;
    });
  };

  var defaultTemplate = Hogan.compile(
    '<a class="reset-button">Reset</a>' +
    '<ul class="list-content"></ul>'
  );

  $.fn.facet_filter.defaults = {

    /**
     * String labeling the area in which the search is made. Used to build
     * the query.
     *
     * @type {String}
     */
    filter_area: '',

    /**
     * Actions triggered on events with purpose of attaching code
     * which changes the visual state of facets - indicates changed state.
     *
     * Filter object should be accessible inside these functions by
     * $filter.data('facet-filter')
     *
     * @param $filter jQuery selector to an element with Filter object
     *  built on top of it
     */
    on_deactivated: function($filter) {},
    on_activated: function($filter) {},

    content_selector: '.list-content',

    /**
     * Selector of the button used to reset the filter
     *
     * @type {jQuery selector}
     */
    reset_button_selector: '.reset-button',

    /**
     * Event triggered by reset button to reset the filter
     */
    reset_event: 'click',

    /**
     * Moustache template returning HTML code with filter. Should contain
     * place for options list, and element which resets the filter.
     *
     * @param title
     */
    template: defaultTemplate.render.bind(defaultTemplate),
  };

  return Filter;
});
