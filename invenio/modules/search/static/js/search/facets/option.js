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
  'js/search/facets/states',
], function($, states_enum) {

  /**
   * Selectable facet option.
   *
   * Can have one of three states which are stored in attribute data-filter-state:
   * '+' / '-' : active with given action
   * 'inactive',
   * 'partiallyActive' : not active, but some of sub-filters are active
   *
   * @param element HTML element
   * @param options configuration
   * @constructor
   */
  function Option(element, options) {

    this.$element = $(element);
    this.options = $.extend({}, $.fn.facet_option.defaults, options);

    this.is_expanded = false;
    this.is_sublist_built = false;
    this.id = this.options.entry.id;
    this.is_expandable = this.options.entry.is_expandable;
    this.parent = this.options.parent;
    this.filter = this.options.filter;
    this.records_num = this.options.entry.records_num;
    this.label = this.options.entry.label;
    this.template = this.options.template;

    this.$element.attr('data-facet-name', this.id);

    this._render();

    this.$sublist = this.$element.find(this.options.sublist_place_selector);
    this.$sublist.hide();

    this.$suboptions = [];

    this.$entry = this.$element.find(this.options.entry_selector);

    this.$expansion_button = this.$element.find(
      this.options.expansion_button_selector);
    this.$toggle_filter_button = this.$element.find(
      this.options.toggle_filter_button_selector);
  }

  /**
   * All events emitted by the class.
   */
  Option.events = {
    /**
     * The option was activated.
     *
     * @type {{filter_option_id: id, action: new state}}
     */
    activated: 'activated',
    /**
     * The option was deactivated. The new state is 'inactive'.
     */
    deactivated: 'deactivated',
  };

  Option.prototype = {

    events: Option.events,

    /**
     * Initialize an option with given state
     *
     * @param initial_state initial state
     */
    init: function() {

      var initial_state = this.options.initial_state;

      this._setState(initial_state);
      if (!this.is_expandable) {
        this.options.disable_expansion(this.$element);
      }
      if (initial_state == states_enum.inactive)
        this.options.on_deactivated(this.$element);
      else
        this.options.on_activated(this.$element);
    },

    /**
     * Destructor
     */
    destroy: function() {
      this.$element.html('');
      this.$element.unbind();
      this.$element.removeData('facet-option');
    },

    /**
     * Renders the facet option
     * @private
     */
    _render: function() {
      this.$element.append(this.template({
        label: this.label,
        records_num: this.records_num,
        id: this.id
      }));
    },

    /**
     * Connects events
     */
    connectEvents: function() {

      var that = this;

      this.$toggle_filter_button.on(
        this.options.toggle_filter_event, function(event) {
          that.toggleFilter(event.shiftKey);
        }
      );

      this.$expansion_button.on(this.options.expand_event, function(event) {
        that.toggleCollapse();
      });

      this.filter.$element.on(this.filter.events.deactivated, function(event) {
        that._deactivate();
      });

      // this.$entry.on(this.events.activated, function propagate(event) {
      //   this.$element.trigger(this.events.activated);
      // }.bind(this));
    },

    /**
     * Toggles option state as if one has clicked on it.
     *
     * @param {boolean} shift_pressed a modifier key is pressed or not
     */
    toggleFilter: function(shift_pressed) {
      if (this.isActive()) {
        this.deactivate();
        return;
      }

      var new_state = states_enum.limitTo;

      if (this.options.activate_modifier_keys && shift_pressed)
        new_state = states_enum.exclude;

      this.activate(new_state);
    },

    /**
     * Collapse/expands the filter option as if one has clicked on
     * the corresponding button.
     */
    toggleCollapse: function() {

      if (this.is_expanded) {
        this.collapse();
      } else {
        this.expand();
      }
    },

    /**
     * Returns current state
     *
     * @returns {String} current state - one of the states
     *  from states_enum
     */
    getState: function () {
      return this.$element.attr('data-filter-state');
    },

    /**
     * Sets current state
     *
     * @param {String} one of the states from states_enum - new_state
     * @private
     */
    _setState: function (new_state) {
      this.$element.attr('data-filter-state', new_state);
    },

    /** Returns node path where levels are following elements in the array.
     * Caches path at first function call.
     *
     * @method getPath
     * @returns {Array} with ids of Option objects
     */
    getPath: function() {
      if (!this.path) {
        if (!this.parent)
          this.path = [this.id];
        else {
          this.path = this.parent.getPath();
          this.path.push(this.id);
        }
      }
      return this.path;
    },

    /**
     * Returns path of the node parent where levels are following elements in the array.
     * Caches path at first function call.
     *
     * @method getPath
     * @returns {Array} with ids of Option objects
     */
    getParentPath: function() {
      if (!this.parent)
        return [];
      return this.parent.getPath();
    },

    /**
     * Checks if the state is active.
     *
     * There can be a couple of activation modes. A Option is not active
     * only if it has state 'inactive' or 'partiallyActive'.
     *
     * States are explained in js/search/facets/states.js
     *
     * @returns {boolean}
     */
    isActive: function () {
      var state = this.getState();
      return (state != states_enum.inactive && state != states_enum.partiallyActive);
    },

    /**
     * Activates filter to a given state - 'active' or 'partiallyActive'.
     * Doesn't affect other options.
     *
     * @param new_state
     * @returns {boolean} True if the state was changed otherwise False
     * @private
     */
    _activate: function(new_state) {

      if (this.getState() == new_state)
        return false;

      this._setState(new_state);
      this.options.on_activated(this.$element);

      // propagate to set children active
      $.each(this.$suboptions, function() {
        $(this).data('facet-option')._activate(new_state);
        // if expandable -> propagate
      });

      return true;
    },

    /**
     * Activates filter to a given state - 'active' or 'partiallyActive'.
     *
     * @param new_state
     */
    activate: function(new_state) {

      var previous_state = this.getState();

      if (!this._activate(new_state))
        return;

      this.informFilter(previous_state, new_state);

      this.$element.trigger($.Event(this.events.activated, {
        filter_option_id: this.id,
        action: new_state
      }));
    },

    /**
     * Deactivates filter option.
     * Doesn't affect other options.
     *
     * @param new_state
     * @returns {boolean} True if the state was changed otherwise False
     * @private
     */
    _deactivate: function() {
      if (this.getState() == states_enum.inactive)
        return false;

      this.options.on_deactivated(this.$element);

      this._setState(states_enum.inactive);

      // propagate to set children active
      $.each(this.$suboptions, function() {
        $(this).data('facet-option')._deactivate(states_enum.inactive)
        // if expandable -> propagate
      });

      return true;
    },

    /**
     * Deactivates filter option.
     *
     * @param new_state
     */
    deactivate: function() {

      var previous_state = this.getState();

      if (!this._deactivate()) {
        return;
      }

      this.informFilter(previous_state, states_enum.inactive);

      this.$element.trigger($.Event(this.events.deactivated, {
        filter_option_id: this.id
      }));
    },

    /**
     * Sets partiallyActive state
     */
    setPartiallyActivated: function() {
      if (this.getState() == states_enum.partiallyActive)
        return;
      this._setState(states_enum.partiallyActive);
      this.options.on_partially_activated(this.$element);
    },

    /**
     * Gets actions list for filter, containing the order
     * to remove all children filters
     *
     * @returns {Array}
     */
    getActions_removeAllChildren: function() {
      var to_remove = [];
      $.each(this.$suboptions, function() {
        var option = $(this).data('facet-option');
        if (option.isActive()) {
          to_remove.push(option);
        } else if (option.getState() == states_enum.partiallyActive) {
          to_remove.concat(option.getActions_removeAllChildren());
        }
      });
      return to_remove;
    },

    /**
     * Gets add actions with action 'activate_action' for all the children
     * except the one passed in 'except_this'. 'except_this' might be
     * the children which sent the signal initially
     *
     * @param except_this
     * @param activate_action
     * @returns {Array}
     */
    getActions_activateAllOtherChildren: function(except_this, activate_action) {
      var to_add = [];

      $.each(this.$suboptions, function() {
        var option = $(this).data('facet-option');
        if (option == except_this)
          return true; // like 'continue'
        to_add.push({filter: option, action: activate_action});

      });
      return to_add;
    },

    /**
     * Checks if all the children have the same state,
     * and the state is equal model state
     *
     * @param model_state model state
     * @returns {boolean}
     */
    haveChildrenSameState: function haveChildrenSameState(model_state) {
      var have_same_state = true;
      $.each(this.$suboptions, function() {
        if (model_state != $(this).attr('data-filter-state')) {
          have_same_state = false;
          return false; // break the loop
        }
      });
      return have_same_state;
    },

    /**
     * Propagates changes either to parent option if available
     * or the filter.
     *
     * @param update_actions actions gathered from children options
     */
    propagateChanges: function propagateChanges(update_actions) {
      if (this.parent)
        this.parent.onChildStatusChanged(update_actions, this);
      else
        this.filter.update(update_actions)
    },

    /**
     * Updates state and propagates the event when status of
     * a child was changed
     *
     * @param update_actions
     * @param child child option
     */
    onChildStatusChanged: function(update_actions, child) {
      var state = this.getState(); // before changes
      var child_state = child.getState();
      // parent was active but child status changed
      if (state != states_enum.inactive && state != states_enum.partiallyActive) { // active
        update_actions.to_delete.push(this);
        this.setPartiallyActivated();
        update_actions.to_add = update_actions.to_add.concat(
          this.getActions_activateAllOtherChildren(child, state));
        // add all other children with parent status
      }
      // parent was inactive, but child status changed
      if (state == states_enum.inactive)
        this.setPartiallyActivated();

      // child status changed and all the children have the same state now
      // make parent have this state
      if (child_state != states_enum.partiallyActive &&
        this.haveChildrenSameState(child_state)) {
          if (child_state == states_enum.inactive) {
            this._deactivate();
          } else {
            this._activate(child_state)
            update_actions.to_add = [{
              filter: this,
              action: child_state
            }];
            update_actions.to_delete = this.getActions_removeAllChildren();
          }
        }

      this.propagateChanges(update_actions);
    },

    /**
     * Informs backend facet filter about the changes
     * made by user at this option.
     *
     * @param previous_state
     * @param new_state
     */
    informFilter: function(previous_state, new_state) {

      var update_actions = {
        to_add: [],
        to_delete: []
      };

      // clean

      if (previous_state == states_enum.partiallyActive) {
        update_actions.to_delete = this.getActions_removeAllChildren();
      }

      if (new_state == states_enum.inactive)
        update_actions.to_delete.push(this);
      else
        update_actions.to_add.push({
          filter: this,
          action: new_state
        });

      this.propagateChanges(update_actions);
    },

    /**
     * Builds sub-list of options
     * @private
     * @returns {jQuery.Deferred} promise of loaded sub-list
     */
    _buildSubsection: function() {

      var that = this;

      this.$sublist.on('list_loaded', function(event) {
        that.$suboptions = that.$element.find(that.options.row_selector);
      });

      var promise = this.$sublist.facet_options_list(
        $.extend({}, this.options.list_details, {

          option_details: this.options.option_details,
          list_details: this.options.list_details,

          facet_engine: this.facet_engine,
          filter: this.filter,
          parent: this,
          activate_modifier_keys: this.options.activate_modifier_keys
        })
      )[0].loadedPromise;

      this.is_sublist_built = true;

      return promise;
    },

    /**
     * Expands the option to show sub-options.
     *
     * @returns {jQuery.Deferred} promise of loaded sub-list, resolved
     *  on success, and rejected on fail
     */
    expand: function () {
      var promise = new $.Deferred();
      if (!this.is_expandable || this.is_expanded) {
        return promise.reject();
      }
      if (!this.is_sublist_built) {
        promise = this._buildSubsection()
      } else {
        promise.resolve();
      }
      return promise.then((function onLoadingSuccess() {
        this.$sublist.show();
        this.is_expanded = true;
        this.options.on_expanded(this.$element);
      }).bind(this));
    },

    /**
     * Collapses the option sub-list
     */
    collapse: function () {
      if (!this.is_expandable)
        return;
      this.is_expanded = false;
      this.$sublist.hide();
      this.options.on_collapsed(this.$element);
    },

    /**
     * Returns the unique name of the option
     * @returns {*}
     */
    getId: function () {
      return this.id;
    }
  };

  $.fn.facet_option = function (option) {

    var $elements = this;
    var dataLabel = 'facet-option';

    return $elements.map(function (idx, element) {
      var $element = $(element);
      var object = $element.data(dataLabel);
      var options = typeof option == 'object' && option;
      // attach jQuery plugin
      if (!object) {
        object = new Option($element, options);
        $element.data(dataLabel, object);
        object.init();
        object.connectEvents();
      }
      return object;
    });
  };

  $.fn.facet_option.defaults = {

    /**
     * Event triggering building of the sub-list
     *
     * @type {jQuery event}
     */
    expand_event: 'click',

    /**
     * Event triggering change of the option state
     * which affects in changing the state of the filter.
     *
     * @type {jQuery event}
     */
    toggle_filter_event: 'click',

    /**
     * Creates HTML code of the option - Mustache template
     *
     * @param ctx {{label: string, records_num: string, id: string}}
     *   label: human-readable,
     *   records_num: Integer
     *   number of records belonging to the filtered results, id: identifier
     */
    template: function (ctx) {
      return '<a class="expanision-button">&gt;</a>' +
        '<a class="toggle-filter-button">%LABEL (%RECNUM)</a>' +
        '<div class="list-content"></div>'
          .replace('%LABEL', ctx.label)
          .replace('%RECNUM', ctx.records_num);
    },

    /**
     * Selector of the element which triggers expansion event
     *
     * @type {jQuery selector}
     */
    expansion_button_selector: '.expansion-button',

    /**
     * Selector of the facet option with the sub-list.
     *
     * @type {jQuery selector}
     */
    row_selector: '.facet-option',

    /**
     * Selector of the facet option without the sub-list.
     *
     * @type {jQuery selector}
     */
    entry_selector: '.entry',

    /**
     * Selector of the button used to toggle the option state.
     *
     * @type {jQuery selector}
     */
    toggle_filter_button_selector: '.toggle-filter-button',

    /**
     * Selector of the place where sub-list shoulbe built.
     *
     * @type {jQuery selector}
     */
    sublist_place_selector: '.list-content',

    /**
     * Actions triggered on events with purpose of attaching code
     * which changes the visual state of facets - indicates changed state.
     *
     * Option element should be accessible inside these functions by
     * $facet_option.data('facet-option')
     *
     * @param $facet_option jQuery selector to an element with Option object
     *  built on top of it
     */
    on_activated: function($facet_option) {},
    on_deactivated: function($facet_option) {},
    on_partially_activated: function($facet_option) {},
    on_expanded: function($facet_option) {},
    on_collapsed: function($facet_option) {},

    /**
     * Function call on rows which are not expandable. Should hide visual elements
     * from HTML generated by rowTemplate which suggest that the element is expandable.
     *
     * @param $row jQuerySelector the element which selects all the option HTML geerated
     *  by rowTemplate
     */
    disable_expansion: function($row) {},

    /**
     * The state of option after initialization.
     *
     * @type {'limitTo' | 'exclude' | 'inactive'}
     */
    initial_state: states_enum.inactive,

    /**
     * identifier
     *
     * @type {String}
     */
    id: undefined,

    /**
     * Facet can be expanded so that a list of sub-options
     * appears.
     *
     * @type {boolean}
     */
    is_expandable: false,

    /**
     * Parent option if the facet is on a sub-list, otherwise undefined should stay here
     *
     * @type {Option}
     */
    parent: undefined,

    /**
     * Filter which receives and processes the option state
     *
     * @type {Filter}
     */
    filter: undefined,

    /**
     * Should modifier keys be used.
     *
     * Currently 'shift' changes the behaviour to 'exclude'.
     *
     * @type {boolean}
     */
    activate_modifier_keys: false,
  }

  return Option;
});
