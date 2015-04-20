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
    'flight/lib/component'
  ],
  function(
    $,
    defineComponent) {

    "use strict";

    return defineComponent(HoldingPenSelection);

    /**
    * .. js:class:: HoldingPenSelection()
    *
    * Selection utilities throughout Holding Pen.
    *
    * :param string alertSelector:
    *
    */
    function HoldingPenSelection() {

      this.attributes({
          selectedIDs: [],
          selectAllSelector: "#list-select-all",
          checkboxSelector: ".row-checkbox input[type=checkbox]",
          rowSelector: "*[data-href]"
      });

      this.selection = function (ev, data) {
        for (var i = 0; i < data.data.length; i++) {
          var selectedID = this.$node.dataTable().fnGetData(data.data[i])[1];
          var selectedIDsArray = this.attr.selectedIDs;

          if ($.inArray(selectedID, selectedIDsArray) == -1) {
            selectedIDsArray.push(selectedID);
          }
        }

        console.log("Array after sel. = " + this.attr.selectedIDs);
      };

      this.deselection = function (ev, data) {
        for (var i = 0; i < data.data.length; i++) {
          var deselectedID = this.$node.dataTable().fnGetData(data.data[i])[1];
          var selectedIDsArray = this.attr.selectedIDs;

          if (selectedIDsArray.length > 0) {
            var index = selectedIDsArray.indexOf(deselectedID);
            if (index > -1) {
              selectedIDsArray.splice(index, 1);
            }
          }
        }

        console.log("Array after desel. = " + this.attr.selectedIDs);
      };


      this.selectAll = function (ev, data) {
        console.log("Selected all");
        var that = this;
        $(this.attr.checkboxSelector).each(function() {
          console.log($(this).val());
          var selectedID = $(this).val();
          if ($.inArray(selectedID, that.attr.selectedIDs) == -1) {
            that.attr.selectedIDs.push(selectedID);
          }
          $(this).checked = true;
        });
        console.log("Array: " + this.attr.selectedIDs);
      };

      this.selectOne = function (ev, data) {
        console.log("Selected one");
        console.log($(data.el).val());
      };

      this.selectRow = function (ev, data) {
        console.log("Selected row");
      };

      this.deselectAll = function (ev) {
        $("#ToolTables_maintable_1").click();
      };


      this.batchHEPActions = function(ev, data) {
        data.selectedIDs = this.attr.selectedIDs;

        $.event.trigger("return_data_for_exec", data);
        $.event.trigger("deselectAll", document);
      };


      this.nextPage = function(ev) {
        $("#maintable_next").click();
        $.event.trigger("deselectAll", document);
      };

      this.previousPage = function(ev) {
        $("#maintable_previous").click();
        $.event.trigger("deselectAll", document);
      };

      this.after('initialize', function() {
        this.on(document, "rowSelected", this.selection);
        this.on(document, "rowDeselected", this.deselection);

        this.on(document, "selectAll", this.selectAll);
        this.on(document, "deselectAll", this.deselectAll);

        this.on(document, "execute", this.batchHEPActions);

        this.on(document, "nextPage", this.nextPage);
        this.on(document, "previousPage", this.previousPage);

        this.on("click", {
          selectAllSelector: this.selectAll,
          checkboxSelector: this.selectOne,
          rowSelector: this.selectRow
        });
        console.log("Selection init");
      });
    }
  }
);
