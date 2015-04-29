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
    'hgn!js/workflows/templates/pagination'
  ],
  function(
    $,
    defineComponent,
    tpl_pagination) {

    'use strict';

    return defineComponent(HoldingPenPagination);

    /**
    * .. js:class:: HoldingPen()
    *
    * Holding Pen table using DataTables (+ plugins)
    *
    *
    */
    function HoldingPenPagination() {
      this.attributes({
        paginationButtonSelector: ".pagination a"
      });

      this.updatePagination = function(ev, data) {
          if (data.total_count > 0) {
            var pagination_data = {
                "has_prev": data.page > 1,
                "has_next": data.page < data.pages,
                "next": data.page + 1,
                "prev": data.page - 1,
                "iter_pages": data.iter_pages
            };
            this.$node.html(tpl_pagination(pagination_data));
          } else {
            this.$node.html("");
          }
      };

      this.changePage = function(ev, data) {
        console.log($(data.el).data("page"));
        // Check that the pagination button is not disabled.
        var parentClasses = $(data.el.parentElement).attr("class");
        if (parentClasses && parentClasses.indexOf("disabled") >= 0) {
          return;
        } else {
          var page = $(data.el).data("page");
          this.trigger(document, "reloadHoldingPenTable", {"page": page});
        }
      };

      this.after('initialize', function() {
        this.on("click", {
          paginationButtonSelector: this.changePage
        });
        this.on(document, "updatePagination", this.updatePagination);

        // Hotkeys pagination
        this.on(document, "hotkeysPagination", this.changePage);

        console.log("Pagination init");
      });
    }
});
