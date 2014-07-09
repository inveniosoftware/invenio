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
var WORKFLOWS_HP_UTILITIES = function ($, holdingpen) {

    var tagList = holdingpen.tag.tagList,
        version_showing = [holdingpen.context.version_showing];

    $.fn.exists = function () {
        return this.length !== 0;
    };

    var _requestNewObjects = function () {
        var version_showing = [],
            i,
            search_tags = [];
            console.log(holdingpen);
        var tempTagList = holdingpen.tag.tagList();
        for(i = 0 ; i< tempTagList.length; i++)
        {
            if ("Completed" == tempTagList[i]) {
                version_showing.push("final");
            } else if ("Halted" == tempTagList[i]) {
                version_showing.push("halted")
            } else if ("Running" ==  tempTagList[i]) {
                version_showing.push("running")
            } else if ("Initial" ==  tempTagList[i]){
                version_showing.push("initial");
            } else {
                search_tags.push(tempTagList[i]);
            }
        }
        my_data = JSON.stringify({'version':version_showing, 'tags':search_tags});
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

    var _init = function () {
        var i;
        if (version_showing) {
            for (i = 0; i < version_showing.length; i++) {
                if (version_showing[i] === 1) {
                    if ($.inArray('Completed', tagList) <= -1) {
                        tagList.push('Completed');
                    }
                    $('#version-completed').click();
                } else if (version_showing[i] === 2) {
                    if ($.inArray('Halted', tagList) <= -1) {
                        tagList.push('Halted');
                    }
                    $('#version-halted').click();
                } else if (version_showing[i] === 3) {
                    if ($.inArray("Running", tagList) <= -1) {
                        tagList.push("Running");
                    }
                    $("#version-running").click();
                }
            }
        }
    };

    var utilities =  {
        init: _init,
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
                    WORKFLOWS_HP_UTILITIES.requestNewObjects();
                }}, 3000);
        },
    };

    return utilities;
}($, WORKFLOWS_HOLDINGPEN);
//***********************************
