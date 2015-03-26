/*
 * This file is part of Invenio.
 * Copyright (C) 2015 CERN.
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
    'jquery',
    'flight/lib/component',
  ],
  function(
    $,
    defineComponent) {

    'use strict';

    return defineComponent(DetailsActionsButtons);

    /**
    * .. js:class:: DetailsActionsButtons()
    *
    * UI component for handling the buttons for restarting/deleting an object.
    *
    * :param string previewMenuItemSelector: DOM selector for each menu item
    *
    */
    function DetailsActionsButtons() {
      this.attributes({
        actionButtonSelector: ".details-action"
      });

      this.triggerActionButton = function(ev, data) {
        this.trigger(document, "detailsButtonClick", {
          action: $(data.el).data("action"),
        });
      };

      this.after('initialize', function() {
        this.on("click", {
          actionButtonSelector: this.triggerActionButton,
        });
        console.log("Details preview menu init");
      });
    }
});
