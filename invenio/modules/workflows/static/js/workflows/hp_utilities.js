/*
 * This file is part of Invenio.
 * Copyright (C) 2013 CERN.
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
var utilities = function ( $, holdingpen ) {
    var rowList = holdingpen.rowList;
    var rowIndexList = holdingpen.rowIndexList;
    var tagList = holdingpen.tag.tagList;
    var oTable = holdingpen.oTable;
    console.log(holdingpen);

    $.fn.exists = function () {
        return this.length !== 0;
    }

    return {
        initialize_versions: function ( version_showing ){
            if(version_showing){
                for(var i=0; i<version_showing.length; i++){
                    if(version_showing[i] == 1){
                        if ($.inArray('Final', tagList) <= -1){
                            tagList.push('Final');  
                        } 
                        $('#version-final').click();
                    }
                    else if(version_showing[i] == 2){
                        // tagList.push('Halted');
                        $('#version-halted').click();  
                    }
                    else if(version_showing[i] == 3){
                        if ($.inArray('Halted', tagList) <= -1){
                            tagList.push('Running');
                        } 
                        $('#version-running').click();  
                    }
                }
            }
        },

        fnGetSelected: function ( oTableLocal ){
            var aReturn = [];
            var aTrs = oTableLocal.fnGetNodes();
            
            for ( var i=0 ; i<aTrs.length ; i++ ){
                if ($(aTrs[i]).hasClass('row_selected')){
                    aReturn.push( aTrs[i] );
                }
            }
            return aReturn;
        },

        requestNewObjects: function (){
            var version_showing = new Object;
            // var widget_showing = new Object;

            version_showing['final'] = ($.inArray('Final', tagList) <= -1) ? false : true;
            version_showing['halted'] = ($.inArray('Halted', tagList) <= -1) ? false : true;
            version_showing['running'] = ($.inArray('Running', tagList) <= -1) ? false : true;

            $.ajax({
                type : "POST",
                url : url.load_table,
                data: JSON.stringify(version_showing),
                contentType: 'application/json;charset=UTF-8',
                traditional: true,
                success: function(result) {
                    oTable.fnDraw(false);
                }
            });
        },

        isInt: function (n) {
           return typeof n === 'number' && n % 1 === 0;
        },

        emptyLists: function (){
            rowList = [];
            rowIndexList = [];
        },

        bootstrap_alert: function (message) {
            $('#alert-message').html('<span class="alert"><a class="close" data-dismiss="alert"> ×</a><span>'+message+'</span></span>');
        }
    };
}
//***********************************
