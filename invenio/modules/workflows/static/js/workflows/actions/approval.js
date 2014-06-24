/*
 * This file is part of Invenio.
 * Copyright (C) 2013, 2014 CERN.
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

var approval = (function ($, holdingpen, utilities) {
    "use strict";

    $(document).ready(function(){
        subscribe();
    });


    var get_action_values = function(elem) {
        return {
            "url": elem.attr("data-url"),
            "value": elem.attr("data-value"),
            "objectid": elem.attr("data-objectid"),
        }
    };

    var post_request = function(data) {
        utilities.bootstrap_alert(data.message, data.category)
    };

    var subscribe = function () {

        /*
        * Approval action click event for mini maintable view.
        *
        * Binds the click event to every element with class
        * "approval-action" to handle the resolution of the
        * action..
        */
        $("#maintable").on("click", ".approval-action", function (event) {
            var data = get_action_values($(this));

            jQuery.ajax({
                type: "POST",
                url: data.url,
                data: {"objectid": data.objectid,
                       "value": data.value},
                success: function(data) {
                    post_request(data);
                    holdingpen.oTable.fnDraw(false);
                }
            });
        });

        /*
        * Approval action click event details page view.
        *
        * Binds the click event to every element with class
        * "approval-action" to handle the resolution of the
        * action..
        */
        $("#approval-widget").on("click", ".approval-action", function (event) {
            var data = get_action_values($(this));

            jQuery.ajax({
                type: "POST",
                url: data.url,
                data: {"objectid": data.objectid,
                       "value": data.value},
                success: post_request,
            });
        });


    };

    return {
        subscribe: subscribe,
    };
})(window.jQuery, window.WORKFLOWS_HOLDINGPEN, window.WORKFLOWS_UTILITIES);

