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

//Utility functions
//***********************************
define(['jquery', 'js/workflows/hp_maintable'], function($, holdingpen) {

    $.fn.exists = function () {
        return this.length !== 0;
    };

    var _requestNewObjects = function () {
        my_data = JSON.stringify({'tags': holdingpen.tag.tagList()});
        $.ajax({
            type : "POST",
            url : holdingpen.context.holdingpen.url_load,
            data: my_data,
            contentType: "application/json;charset=UTF-8",
            traditional: true,
            success: function(result) {
                holdingpen.oTable.fnDraw(false);
            }
        });
    };

    var utilities =  {
        requestNewObjects: _requestNewObjects,

        fnGetSelected: function (oTableLocal) {
            var aReturn = [],
                aTrs = oTableLocal.fnGetNodes(),
                i;

            for (i = 0; i < aTrs.length; i++) {
                if ($(aTrs[i]).hasClass("row_selected")) {
                    aReturn.push(aTrs[i]);
                }
            }
            return aReturn;
        },

        isInt: function (n) {
            return typeof n === "number" && n % 1 === 0;
        },

        emptyLists: function () {
            holdingpen.rowList = [];
            holdingpen.rowIndexList = [];
        },

        autorefresh: function () {
            window.setInterval( function() {
                if($('#option-autorefresh').hasClass("btn-danger")) {
                    _requestNewObjects.requestNewObjects();
                }}, 3000);
        },

        bootstrap_alert: function (message, category) {
            $("#alert-message").html(
                '<div class="alert alert-' + category + ' alert-dismissable">' +
                '<button type="button" class="close" data-dismiss="alert" aria-hidden="true">&times;</button>' +
                '<span>' + message + '</span></div>'
            );
        },
    };

    return utilities;
});
