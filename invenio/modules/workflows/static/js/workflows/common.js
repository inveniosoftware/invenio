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
    'hgn!js/workflows/templates/alert'
  ],
  function(
    $,
    defineComponent,
    tpl_alert) {

    "use strict";

    return defineComponent(HoldingPenCommon);

    /**
    * .. js:class:: HoldingPenCommon()
    *
    * Common utilities throughout Holding Pen.
    *
    * :param string alertSelector:
    *
    */
    function HoldingPenCommon() {
      this.attributes({
        // URL
        alertSelector: "#alert-message",
      });

      this.setAlertMessage = function (ev, data) {
        $(this.attr.alertSelector).append(tpl_alert({
          category: data.category,
          message: data.message
        }));
      };

      this.after('initialize', function() {
        this.on(document, "updateAlertMessage", this.setAlertMessage);
        console.log("Common init");
      });
    }
  }
);
