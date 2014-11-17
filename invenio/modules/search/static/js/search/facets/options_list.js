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
  'hogan',
  'js/search/facets/states',
  'js/search/facets/option',
], function($, Hogan, states) {

  "use strict";

  /**
   * List of selectable facet options.
   *
   * Takes care of generating the list and expanding/collapsing the list
   * using 'Show more...' and 'Show less..' buttons.
   *
   * Every option rendered inside the list is accessible by facet-option css
   * class selector.
   */
  function OptionsList(element, options) {

    this.$element = $(element);
    this.options = $.extend({}, $.fn.facet_options_list.defaults, {
      translations: $.extend(
        {}, $.fn.facet_options_list.defaults.translations, options.translations),
    }, options);
    this.name = options.id;
    this.facet_engine = this.options.facet_engine;
    this.parent = this.options.parent;

    this.split_by = this.options.split_by;
    this.template = this.options.template;

    this.option_wrapper = '<li class="facet-option"></li>';
    this.translations = this.options.translations;

    // render
    this.$element.append(this.template({
      lessLabel: this.translations.less,
      moreLabel: this.translations.more
    }));

    this.$list = this.$element.find(this.options.option_list_selector);
    this.$button_more = this.$element.find(this.options.moreButtonSelector);
    this.$button_less = this.$element.find(this.options.lessButtonSelector);

    this.connectEvents();
    this.loadedPromise = this.fetchContent();
    this.$button_less.hide();
  }

  /**
   * All events emitted by the class.
   */
  OptionsList.events = {
    /**
     * Triggered when the list content is loaded.
     */
    loaded: 'list_loaded',
  };

  OptionsList.prototype = {

    events: OptionsList.events,

    /**
     * Destructor
     */
    destroy: function() {
      this.$element.html('');
      this.$element.unbind();
      this.$element.removeData('facet-options-list');
    },

    connectEvents: function() {

      var that = this;

      this.$button_more.on('click', function() {
        that.showMore();
        return false;
      });

      this.$button_less.on('click', function() {
        that.showLess();
        return false;
      });
    },

    /**
     * Render the entries on the list.
     * @param entries
     */
    fillList: function(entries) {
      var that = this;
      /* Generate facet rows with checkboxes. */
      $.each(entries, function (index, entry) {
        that.addRow(entry);
      });

      this.$options = this.$element.find('.facet-option');

      // show first entries
      this.showMore();
    },

    /**
     * Make an ajax query to get the content.
     *
     * @returns {$.Deferred} P
     */
    fetchContent: function() {
      var query = {};

      if (this.parent) {
        var parent_id = this.parent.getId();
        if (parent_id) {
          query = $.extend(query, { parent: parent_id })
        }
      }

      var loadedPromise = $.ajax({
        url: this.options.filter.url,
        dataType : 'json',
        data: query,
        context: {
          optionList: this,
        },
        success: function(response) {
          this.optionList.fillList(response.facet);
          this.optionList.is_loaded = true;
          this.optionList.$element.trigger(this.optionList.events.loaded);
        },
      });

      return loadedPromise;
    },

    /**
     * Show more options. There are going to be added the number of options
     * defined by split_by parameter passed to the constructor inside options var.
     *
     * If the options number exceeds number stored in split_by variable
     * of the initial configuration not all the options are shown.
     *
     */
    showMore: function() {
      var $hiddenOptions = this.$options.filter("[style$='display: none;']");
      $($hiddenOptions.splice(0, this.split_by)).show();
      if ($hiddenOptions.length <= 0) {
        this.$button_more.hide();
      }
      if (this.$options.length - $hiddenOptions.length > this.split_by) {
        this.$button_less.show();
      }
    },

    /**
     * Shows less options. There are going to be removed the number of options
     * defined by split_by parameter passed to the constructor inside options var.
     *
     * If the options number exceeds number stored in split_by variable
     * of the initial configuration not all the options are shown.
     *
     */
    showLess: function() {
      var $visibleOptions = this.$options.filter("[style!='display: none;']");
      // number of the elements to hide
      // there should stay this.split_by number of the elements visible
      var toHideNum = Math.min(
          $visibleOptions.length - this.split_by, this.split_by);
      $($visibleOptions.splice(-toHideNum)).hide();
      if ($visibleOptions.length <= this.split_by) {
        this.$button_less.hide();
      }
      this.$button_more.show();
    },

    /**
     * Add a row in the list with a facet option.
     *
     * @param entry the facet option configuration
     */
    addRow: function (entry) {

      var $new_facet_option = $(this.option_wrapper);
      this.$list.append($new_facet_option);

      var initial_state = states.inactive;
      if (this.parent) {
        initial_state = this.parent.getState();
      }

      $new_facet_option.facet_option($.extend({}, this.options.option_details, {
        entry: entry,
        filter: this.options.filter,
        initial_state: initial_state,
        parent: this.parent,
        activate_modifier_keys: this.options.activate_modifier_keys,
        list_details: this.options.list_details,
        option_details: this.options.option_details,
        translations: this.translations,
      }));
      // All rows are hidden by default.
      // After the list is loaded first items are shown.
      // The number of items shown is determined by split_by configuration
      // option
      $new_facet_option.hide();
    }
  };

  $.fn.facet_options_list = function (option) {

    var $elements = this;
    var dataLabel = 'facet-options-list';

    return $elements.map(function (idx, element) {
      var $element = $(element);
      var object = $element.data(dataLabel);
      var options = typeof option == 'object' && option;
      // attach jQuery plugin
      if (!object) {
        object = new OptionsList($element, options);
        $element.data(dataLabel, object);
      }
      return object;
    });
  };

  var defaultTemplate = Hogan.compile(
    '<div class="option-list"></div>' +
    '<a class="facet-more-button"> {{moreLabel}} ...</a> ' +
    '<a class="facet-less-button pull-right"> {{lessLabel}} ...</a>'
  );

  $.fn.facet_options_list.defaults = {

    translations: {
      more: 'More',
      less: 'Less'
    },

    /**
     * Display by chunks of N elements
     *
     * @type {Integer}
     */
    split_by: 5,

    /**
     * The selector of the button used to expand the option list with the next
     * number of the options indicated by split_by parameter.
     *
     * @type {String}
     */
    moreButtonSelector: '.facet-more-button',

    /**
     * The selector of the button used to hide the number of options indicated
     * by split_by parameter. It always leaves at least split_by
     * number of options.
     *
     * @type {String}
     */
    lessButtonSelector: '.facet-less-button',

    /**
     * Selector of the place where the options should be loaded.
     *
     * @type {String}
     */
    option_list_selector: '.option-list',

    /**
     * Moustache template accepting a dict with following params:
     *
     * @param lessLabel
     * @param moreLabel
     */
    template: defaultTemplate.render.bind(defaultTemplate),
  };

  return OptionsList;
});
