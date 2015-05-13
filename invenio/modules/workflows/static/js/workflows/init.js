/*
 * This file is part of Invenio.
 * Copyright (C) 2014, 2015 CERN.
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

require(
  [
    "jquery",
    "bootstrap-tagsinput",
    "prism",
    "js/workflows/common",
    "js/workflows/maintable",
    "js/workflows/holdingpen",
    "js/workflows/pagination",
    "js/workflows/perpage_menu",
    "js/workflows/sort_menu",
    "js/workflows/selection",
    "js/workflows/tags",
    "js/workflows/tags_menu",
    "js/workflows/details",
    "js/workflows/details_actions",
    "js/workflows/details_actions_buttons",
    "js/workflows/details_preview",
    "js/workflows/details_preview_menu",
    "js/workflows/details_page",
    "js/workflows/actions/init"
  ],
  function() {
    // This file is simply here to make sure the above dependencies are
    // properly loaded and ready to be used by inline scripts.
    //
    // Without it, we have to rely on non-anonymous modules.
    console.info("js/workflows/init is loaded");
  }
);
