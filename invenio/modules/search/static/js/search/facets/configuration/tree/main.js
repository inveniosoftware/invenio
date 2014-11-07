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

define(function(require, exports, module) {

  module.exports = {

    stylesheet: require.toUrl("./style.css"),

    option_details: {

      template: require('hgn!./option'),

      disable_expansion: function ($row) {
        $row.find('.expansion-button').css('visibility', 'hidden');
      },
      on_activated: function ($facet_option) {
        $facet_option.data('facet-option').$toggle_filter_button
          .prop("checked", true)
          .prop("indeterminate", false);
      },
      on_deactivated: function ($facet_option) {
        $facet_option.data('facet-option').$toggle_filter_button
          .prop('checked', false)
          .prop("indeterminate", false);
      },
      on_partially_activated: function ($facet_option) {
        $facet_option.data('facet-option').$toggle_filter_button
          .prop('checked', false)
          .prop("indeterminate", true);
      },
      on_expanded: function ($facet_option) {
        $facet_option.data('facet-option').$entry.find('.glyphicon')
          .removeClass('glyphicon-chevron-right')
          .addClass('glyphicon-chevron-down');
      },
      on_collapsed: function ($facet_option) {
        $facet_option.data('facet-option').$entry.find('.glyphicon')
          .removeClass('glyphicon-chevron-down')
          .addClass('glyphicon-chevron-right');
      }
    },

    filter_details: {

      template: require('hgn!./filter'),

      on_deactivated: function ($filter) {
        $filter.data('facet-filter').$reset_button
          .prop("checked", true)
          .attr("disabled", true);
      },

      on_activated: function ($filter) {
        $filter.data('facet-filter').$reset_button
          .prop("checked", false)
          .removeAttr("disabled");
      }
    },
  };
});
