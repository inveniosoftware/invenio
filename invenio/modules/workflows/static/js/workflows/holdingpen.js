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
    'flight/lib/component',
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
      this.attributes({
        // URLs
        load_url: "",
        page: 1,
        per_page: 10,
      });

      this.preparePayload = function (data) {
        var payload = data || {};

        if (payload && payload.page) {
          this.attr.page = payload.page;
        } else {
          payload.page = this.attr.page;
        }
        if (payload && payload.per_page) {
          this.attr.per_page = payload.per_page;
        } else {
          payload.per_page = this.attr.per_page;
        }
        return payload;
      };

      this.reloadTable = function (ev, data) {
        // $node is the list element this component is attached to.
        var $node = this.$node;
        var that = this;

        $.ajax({
            type: "GET",
            url: this.attr.load_url,
            data: this.preparePayload(data),
            success: function(result) {
                var table = $node.find("tbody");
                table.html(result.rendered_rows);
                that.trigger(document, "updatePagination", result.pagination);
            }
        });
      };

      this.rowSelectionTrigger = function(data) {
        // Need to use jquery directly as "this" (e.g. flight component) is
        // not in the context of the TableTools selection.
        $.event.trigger("rowSelected", data, document);
      }

      this.after('initialize', function() {
        this.on(document, "initHoldingPenTable", this.reloadTable);
        this.on(document, "reloadHoldingPenTable", this.reloadTable);
        console.log("HP init");
      });
    }
});
