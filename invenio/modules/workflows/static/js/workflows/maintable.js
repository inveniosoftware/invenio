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

define(
  [
    "js/workflows/common",
    "js/workflows/holdingpen",
    "js/workflows/pagination",
    "js/workflows/perpage_menu",
    "js/workflows/sort_menu",
    "js/workflows/tags",
    "js/workflows/tags_menu",
    "js/workflows/selection"
  ],
  function(
    HoldingPenCommon,
    HoldingPen,
    HoldingPenPagination,
    HoldingPenPerPage,
    HoldingPenSort,
    HoldingPenTags,
    HoldingPenTagsMenu,
    HoldingPenSelection) {

    "use strict";

    function initialize(context) {
      HoldingPenCommon.attachTo(document);
      HoldingPen.attachTo("#list", {
        load_url: context.load_table_url,
        page: context.page,
        per_page: context.per_page
      });
      HoldingPenPagination.attachTo("#pagination");
      HoldingPenPerPage.attachTo("#perpage-menu");
      HoldingPenSort.attachTo("#sort-menu");
      HoldingPenTags.attachTo("#tags", {
        tags: context.tags
      });
      HoldingPenTagsMenu.attachTo("#tags-menu", {
        menuitemSelector: "#tags-menu a",
        valuePrefix: ""
      });
      HoldingPenTagsMenu.attachTo("#type-menu", {
        menuitemSelector: "#type-menu a",
        valuePrefix: "type:"
      });
      HoldingPenTagsMenu.attachTo("#filter-menu", {
        menuitemSelector: "#filter-menu a",
        valuePrefix: "f:"
      });
      HoldingPenSelection.attachTo(document);
    }

    return initialize;
  }
);
