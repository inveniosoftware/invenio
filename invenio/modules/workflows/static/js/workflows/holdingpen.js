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

'use strict';

define(
  [
    'jquery',
    'flight/lib/component',
    'datatables',
    'datatables-plugins',
    'datatables-tabletools'
  ],
  function(
    $,
    defineComponent) {

    return defineComponent(HoldingPen);

    /**
    * .. js:class:: HoldingPen()
    *
    * Holding Pen table using DataTables (+ plugins)
    *
    * :param string load_url: URL to asynchronously load table rows.
    * :param object oSettings: configuration of DataTables.
    *
    */
    function HoldingPen() {
      this.attributes({
        // URLs
        load_url: "",
        oSettings: {
          dom: 'T<"clear">lfrtip',
          bFilter: false,
          bProcessing: true,
          bServerSide: true,
          bDestroy: true,
          aoColumnDefs: [
            {'bSortable': false, 'defaultContent': "", 'aTargets': [0]},
            {'bSearchable': false, 'bVisible': false, 'aTargets': [1]},
            {'sWidth': "25%", 'aTargets': [2]},
            {'sWidth': "25%", 'aTargets': [3]}
          ],
          order: [[ 4, "desc" ]],  // Default sort by modified date "newest first"
          tableTools: {
            "sRowSelect": "multi",
            "sRowSelector": 'td:first-child',
            "aButtons": [
              {
                "sExtends": "select_all",
                "sButtonClass": "btn btn-default"
              },
              {
                "sExtends": "select_none",
                "sButtonClass": "btn btn-danger"
              }
            ]
          },
          deferRender: true,
        }
      });

      this.init_datatables = function(ev, data) {
        // DataTables ajax settings
        this.attr.oSettings["sAjaxSource"] = this.attr.load_url;
        this.$node.DataTable(this.attr.oSettings);
        // Bootstrap TableTools
        var tt = $.fn.dataTable.TableTools.fnGetInstance(this.$node.attr("id"));
        $(tt.fnContainer()).insertBefore('div.dataTables_wrapper');
      }

      this.reloadTable = function (ev, data) {
        var $node = this.$node;
        $.ajax({
            type: "POST",
            url: this.attr.load_url,
            data: JSON.stringify(data),
            contentType: "application/json;charset=UTF-8",
            traditional: true,
            success: function(result) {
                $node.dataTable().fnDraw(false);
            }
        });
      };

      this.holdingPenKeyCodes = function(ev) {
        var keycodes = {
          escape: 27,
        }

        console.log(ev.keyCode);
        console.log(keycodes.escape);
      }

      this.after('initialize', function() {
        this.on(document, "initHoldingPenTable", this.init_datatables);
        this.on(document, "reloadHoldingPenTable", this.reloadTable);
        this.on(document, "keyup", this.holdingPenKeyCodes);
        console.log("HP init");
      });
    }
});
