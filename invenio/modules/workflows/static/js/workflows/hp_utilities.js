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
var WORKFLOWS_HP_UTILITIES = function ( $, holdingpen ) {

    var tagList = holdingpen.tag.tagList;
    var version_showing = [holdingpen.context.version_showing];

    $.fn.exists = function () {
        return this.length !== 0;
    };

    var _requestNewObjects = function() {
        var version_showing = {};
        ($.inArray("Completed", holdingpen.tag.tagList()) <= -1) ? null:  version_showing["final"] = true;
        ($.inArray("Halted", holdingpen.tag.tagList()) <= -1) ? null : version_showing["halted"] = true;
        ($.inArray("Running", holdingpen.tag.tagList()) <= -1) ? null : version_showing["running"] = true;
        ($.inArray("Initial", holdingpen.tag.tagList()) <= -1) ? null : version_showing["initial"] = true;
        $.ajax({
            type : "POST",
            url : holdingpen.context.holdingpen.url_load,
            data: JSON.stringify(version_showing),
            contentType: "application/json;charset=UTF-8",
            traditional: true,
            success: function(result) {
                holdingpen.oTable.fnDraw(false);
            }
        });
    };

    var _init = function() {
        if(version_showing){
            for(var i=0; i<version_showing.length; i++){
                if(version_showing[i] == 1){
                    if ($.inArray('Completed', tagList) <= -1){
                        tagList.push('Completed');
                    } 
                    $('#version-completed').click();
                }
                else if(version_showing[i] == 2){
                    if ($.inArray('Halted', tagList) <= -1){
                        tagList.push('Halted');  
                    } 
                    $('#version-halted').click();  
                }
                else if(version_showing[i] == 3){
                    if ($.inArray("Running", tagList) <= -1){
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

        fnGetSelected: function ( oTableLocal ){
            var aReturn = [];
            var aTrs = oTableLocal.fnGetNodes();
            
            for ( var i=0 ; i<aTrs.length ; i++ ){
                if ($(aTrs[i]).hasClass("row_selected")){
                    aReturn.push( aTrs[i] );
                }
            }
            return aReturn;
        },

        isInt: function (n) {
           return typeof n === "number" && n % 1 === 0;
        },

        emptyLists: function (){
            holdingpen.rowList = [];
            holdingpen.rowIndexList = [];
        },
    };

    return utilities;
}($, WORKFLOWS_HOLDINGPEN);
//***********************************
