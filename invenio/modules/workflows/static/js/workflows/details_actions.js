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

    "use strict";

    return defineComponent(DetailsActions);

    /**
    * .. js:class:: DetailsActions()
    *
    * UI component for handling the buttons for restarting/deleting an object.
    *
    * :param string previewMenuItemSelector: DOM selector for each menu item
    *
    */
    function DetailsActions() {
      this.attributes({
        // URLs
        delete_url: "",
        restart_url: "",

        // BibWorkflowObject id
        id_object: "",
      });

      this.handleDetailsButton = function(ev, data) {
        var url;
        var alert_message;
        if (data.action === "delete") {
          url = this.attr.delete_url;
        } else if (data.action === "restart") {
          url = this.attr.restart_url;
        }
        var $this = this;
        var payload = {
          objectid: this.attr.id_object
        };

        $.ajax({
          type: "POST",
          url: url,
          data: payload,
          success: function(data) {
            $this.trigger(document, "updateAlertMessage", {
              category: data.category,
              message: data.message
            });
          }
        });

      };

      this.after('initialize', function() {
        this.on(document, "detailsButtonClick", this.handleDetailsButton)
        console.log("Details actions init");
      });
    }
});
