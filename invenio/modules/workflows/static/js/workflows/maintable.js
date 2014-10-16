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

'use strict';

define(
  [
    "js/workflows/holdingpen",
    "js/workflows/tags",
    "js/workflows/tags_menu",
    "js/workflows/actions/approval"
  ],
  function(
    HoldingPen,
    HoldingPenTags,
    HoldingPenTagsMenu,
    ApprovalAction) {

    function initialize(context) {
      HoldingPen.attachTo("#maintable", {
        load_url: context.load_table_url,
      });
      HoldingPenTags.attachTo("#tags", {
        tags: context.tags,
      });
      HoldingPenTagsMenu.attachTo("#tags-menu");

      // Actions init
      ApprovalAction.attachTo("#maintable", {
        action_url: context.action_url
      });
    }

    return initialize;
  }
);
