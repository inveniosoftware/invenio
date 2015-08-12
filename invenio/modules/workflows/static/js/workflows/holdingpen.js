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
    'jquery',
    'flight/lib/component'
  ],
  function(
    $,
    defineComponent) {

    'use strict';

    return defineComponent(HoldingPen);

    /**
    * .. js:class:: HoldingPen()
    *
    * Holding Pen table rendering. Trigger "reloadTable" event to render table.
    *
    * :param string load_url: URL to asynchronously load table rows.
    *
    */
    function HoldingPen() {
      var request = false;

      this.attributes({
        // Selectors
        totalSelector: "#total_found",
        nextSelector: "a[aria-label='Next']",
        previousSelector: "a[aria-label='Previous']",

        // URLs
        load_url: "",

        // Data
        page: 1,
      });

      this.preparePayload = function (data) {
        // We consider current attributes as default and then override.
        var payload = this.attr;
        for (var attrname in data || {}) {
          payload[attrname] = data[attrname];
        }
        return payload;
      };

      this.reloadTable = function (ev, data) {
        // $node is the list element this component is attached to.
        var $node = this.$node;
        var that = this;

        if (this.request && this.request.readyState !== 4) {
          console.log("Abort");
          this.request.abort();
        }

        this.request = $.ajax({
          type: "GET",
          url: this.attr.load_url,
          data: this.preparePayload(data),
          beforeSend: function() {
            console.log("Starting");
            $("#list-loading").show();
          },
          success: function(result) {
            var table = $node.find("tbody");
            table.html(result.rendered_rows);
            $(that.attr.totalSelector).html(result.pagination.total_count);
            that.trigger(document, "tableReloaded", result);
          },
          complete: function() {
            console.log("Ending request");
            $("#list-loading").hide();
          }
        });
      };

      this.holdingPenKeyCodes = function(event) {
        var keyCodes = {
          escKey: 27,
          aKey: 65,
          wKey: 87,
          qKey: 81
        };

        var data = {};

        if (event.ctrlKey && event.keyCode === keyCodes.aKey) {
          this.trigger(document, "selectAll");
          event.preventDefault();
        }
        if (event.keyCode === keyCodes.escKey) {
          this.trigger(document, "deselectAll");
          event.preventDefault();
        }
        if (event.altKey && event.keyCode === keyCodes.wKey) {
          data.el = $(this.attr.nextSelector);

          this.trigger(document,"hotkeysPagination", data);
          event.preventDefault();
        }
        if (event.altKey && event.keyCode === keyCodes.qKey) {
          data.el = $(this.attr.previousSelector);

          this.trigger(document,"hotkeysPagination", data);
          event.preventDefault();
        }
      };

      this.after('initialize', function() {
        this.on(document, "reloadHoldingPenTable", this.reloadTable);
        this.on(document, "keydown", this.holdingPenKeyCodes);
        console.log("HP init");
      });
    }
});
