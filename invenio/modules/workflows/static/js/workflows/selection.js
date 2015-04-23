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
          rowSelector: "*[data-href]",

          // Batch Buttons
          batchButtons: "#batch-action-buttons",
          batchButtonSelector: ".batch-button"
      });


      // Batch Actions functions
      this.batchCheck = function (ev) {

        // if it was already checked then the selectedIDs array has elements
        // that we need to remove AND uncheck
        // ELSE
        // the opposite (empty, so we need to add to the array)
        if ($(this.attr.selectAllSelector).prop('checked') == false) {
          this.deselectAll();
        } else {
          this.selectAll();
        }
      };

      this.batchActions = function(ev, data) {
        data.selectedIDs = this.attr.selectedIDs;

        this.trigger(document, "return_data_for_exec", data);
        $.event.trigger("deselectAll", document);
      };

      this.batchActionButtons = function(ev, data) {
        this.trigger(document, "execute", {"value": $(data.el).attr('data-value')});
      };


      // Selection/Deselection
      this.selectAll = function() {
        var $this = this;

        $(this.attr.selectAllSelector).prop('checked', true);
        $(this.attr.checkboxSelector).each(function() {
          var id = $(this).val();
          if ($.inArray(id, $this.attr.selectedIDs) == -1) {

            // Add to the array
            $this.attr.selectedIDs.push(id);
            // Check the box
            $("input[value=" + id +"]").prop('checked', true);
          }
          $(this).checked = true;
        });

        console.log("Array: " + this.attr.selectedIDs);
        this.checkIfBatchActionButtonsAppear();
      };

      this.deselectAll = function() {

        // Uncheck every box...
        $(this.attr.selectAllSelector).prop('checked', false);
        this.attr.selectedIDs.forEach(function(id) {
          $("input[value=" + id +"]").prop('checked', false);
        });
        // And empty the array
        this.attr.selectedIDs = [];

        console.log("Array: " + this.attr.selectedIDs);
        this.checkIfBatchActionButtonsAppear();
      };

      this.selectCheckbox = function (ev, data) {
        var row = $(data.el);
        if (row.prop('checked') == false) {
          this.removeElementFromIDs(row.val());
        } else {
          this.attr.selectedIDs.push(row.val());
        }

        console.log("Array: " + this.attr.selectedIDs);
        this.checkIfBatchActionButtonsAppear();
      };

      this.selectOrDeselectAll = function (ev) {
        $(this.attr.selectAllSelector).click();
        this.checkIfBatchActionButtonsAppear();
      };

      // "Utility" functions
      this.checkIfBatchActionButtonsAppear = function() {
        if (this.attr.selectedIDs.length > 0) {
          $(this.attr.batchButtons).removeClass("hidden");
        } else {
          $(this.attr.batchButtons).addClass("hidden");
        }
      };

      this.removeElementFromIDs = function(id) {
        var idArray = this.attr.selectedIDs;
        if (idArray.length > 0) {
          var index = idArray.indexOf(id);
          idArray.splice(index, 1);
        }
      };


      this.after('initialize', function() {
        this.on(document, "selectAll", this.selectAll);
        this.on(document, "deselectAll", this.deselectAll);

        this.on(document, "execute", this.batchActions);
        this.on(document, "hotkeysPagination", this.deselectAll);

        this.on("click", {
          selectAllSelector: this.batchCheck,
          checkboxSelector: this.selectCheckbox,
          batchButtonSelector: this.batchActionButtons
        });
        console.log("Selection init");
      });
    }
  }
);
