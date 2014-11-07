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

      on_activated: function($facet_option) {
        var facet_option = $facet_option.data('facet-option');
        facet_option.$toggle_filter_button.addClass('option-active');
        // expansion state synchronisation
        facet_option.is_expanded = !facet_option.isActive();
      },
      on_deactivated: function($facet_option) {
        var facet_option = $facet_option.data('facet-option');
        $facet_option.data('facet-option').$toggle_filter_button
          .removeClass('option-active');
        // expansion state synchronisation
        facet_option.is_expanded = facet_option.isActive();
      },
      on_partially_activated: function($facet_option) {
        $facet_option.data('facet-option').$toggle_filter_button
          .removeClass('option-active');
      },
    },
    filter_details: {
      template: require('hgn!./filter'),
    }
  };
});
