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


// DataTables row selection functions
//***********************************
var datatable = function ( $, holdingpen ){
    var oTable = holdingpen.oTable;
    var oSettings = holdingpen.oSettings;
    var rowList = holdingpen.rowList;
    var rowIndexList = holdingpen.rowIndexList;
    var hoveredRow = -1;

    function selectAll(){
        var fromPos = oSettings._iDisplayStart;
        var toPos = oSettings._iDisplayLength-1 + fromPos;
        var j;

        var current_row = null;
        for (var i=fromPos; i<=toPos; i++){
            j = i%10;
            current_row = oSettings.aoData[oSettings.aiDisplay[j]].nTr;
            console.log(current_row);
            if($.inArray(current_row.row_id, rowList) <= -1){
                if (selectCellByTitle(current_row, 'Actions').innerText != 'N/A'){
                    rowIndexList.push(i);
                    rowList.push(current_row.row_id);
                    current_row.style.background = "#ffa";
                    current_row.cells[0].firstChild.checked = true;
                }
            }
        }
    }

    function selectCellByTitle (row, title){
        for(var i=0; i<oSettings.aoHeader[0].length; i++){
            var trimmed_title = $.trim(oSettings.aoHeader[0][i].cell.innerText);
            if(trimmed_title === title){
                return $(row).children()[i - 1];
            }
        }
    }

    function deselectAllFromPage (){
        var fromPos = oSettings._iDisplayStart;
        var toPos = oSettings._iDisplayLength-1 + fromPos;

        for (i=fromPos; i<=toPos; i++){
            j = i % 10;
            if($.inArray(i, rowIndexList) > -1){
                current_row = oSettings.aoData[oSettings.aiDisplay[j]].nTr;
                selectRow(current_row, event, oSettings);
            }
        }
    }

    function selectRow (row, e, oSettings) {
        selectedRow = row;
        var widget_name;
        if( e.shiftKey === true ){
            selectRange(row);
        }
        else{
            if(selectCellByTitle(row, 'Actions').childNodes[0].id === 'submitButtonMini'){
                widget_name = 'Approve Record';
            }
            if($.inArray(row.row_id, rowList) <= -1){
                // Select row
                rowList.push(row.row_id);
                rowIndexList.push(row._DT_RowIndex+oSettings._iDisplayStart);
                row.style.background = "#ffa";

                if (selectCellByTitle(row, 'Actions').innerText != 'N/A'){                    
                    if(widget_name === 'Approve Record'){
                        recordsToApprove.push(row.row_id);
                        console.log(recordsToApprove);
                    }
                }   
                row.checkbox.checked = true;
            }   
            else{
                // De-Select
                rowList.splice(rowList.indexOf(row.row_id), 1);
                rowIndexList.splice(rowIndexList.indexOf(row._DT_RowIndex+oSettings._iDisplayStart), 1);
                row.style.background = "white";
                
                if(widget_name === 'Approve Record'){
                    recordsToApprove.splice(recordsToApprove.indexOf(row.row_id), 1);
                }
                row.checkbox.checked = false;
            }
        }
        checkRecordsToApprove();
    }

     function deselectAll (){
        holdingpen.rowList = [];
        holdingpen.rowIndexList = [];
        oTable.fnDraw(false);
        window.getSelection().removeAllRanges();
    } 

    function hoverRow (row) {
        row.style.background = "#FFFFEE";
    }

    function unhoverRow (row) {
        console.log(row.row_id);
        if($.inArray(row.row_id, holdingpen.rowList) > -1){
            row.style.background = "#ffa";
        }
        else{
            row.style.cssText = defaultcss;
        }
    }

    $("#select-all").on("click", function(){
        if($(this)[0].checked == true){
            selectAll();
        }
        else{
            deselectAllFromPage();
        }
    });

    window.addEventListener("keydown", function(e){
        var currentRowIndex;
        var current_row;
        if([32, 37, 38, 39, 40].indexOf(e.keyCode) > -1) {
            e.preventDefault();
        }
        if (e.keyCode == 40) {
            if (e.shiftKey === true){
                currentRowIndex = rowIndexList[rowIndexList.length-1];
                if (currentRowIndex < 9){
                    row_index = currentRowIndex + 1;
                    current_row = oSettings.aoData[oSettings.aiDisplay[row_index]].nTr;
                    if($.inArray(current_row.row_id, rowList) <= -1){
                        holdingpen.rowIndexList.push(row_index);
                        holdingpen.rowList.push(current_row.row_id);
                        current_row.style.background = "#ffa";
                    }
                }
            }
            else{
                if (hoveredRow < 9){
                    if (hoveredRow != -1){
                        unhoverRow(oSettings.aoData[oSettings.aiDisplay[hoveredRow]].nTr);
                    }
                    hoveredRow++;
                    hoverRow(oSettings.aoData[oSettings.aiDisplay[hoveredRow]].nTr);
                }
            }
        }
        else if (e.keyCode == 38) {
            if (e.shiftKey === true){
                currentRowIndex = holdingpen.rowIndexList[holdingpen.rowIndexList.length-1];
                if (currentRowIndex > 0){
                    rowToAdd = currentRowIndex - 1;
                    var current_row = oSettings.aoData[oSettings.aiDisplay[rowToAdd]].nTr;
                    if($.inArray(current_row.row_id, holdingpen.rowList) <= -1){
                        holdingpen.rowIndexList.push(rowToAdd);
                        holdingpen.rowList.push(current_row.row_id);
                        current_row.style.background = "#ffa";
                    }
                }
            }
            else{
                if (hoveredRow > 0){
                    unhoverRow(oSettings.aoData[oSettings.aiDisplay[hoveredRow]].nTr);
                    hoveredRow--;
                    hoverRow(oSettings.aoData[oSettings.aiDisplay[hoveredRow]].nTr);
                }
            }
        }
        else if (e.keyCode == 37){
            oTable.fnPageChange('previous');
        }
        else if( e.keyCode == 39){
            oTable.fnPageChange('next');
        }
        else if (e.keyCode == 65 && e.ctrlKey === true){
            selectAll();
            removeSelection();
        }
        else if (e.keyCode == 13 && hoveredRow != -1){
            selectCellByTitle(oSettings.aoData[oSettings.aiDisplay[hoveredRow]].nTr, 'Details').click();
        }
        else if(e.keyCode == 46){
            if (holdingpen.rowList.length >= 1){
                var rowList_out = JSON.stringify(holdingpen.rowList);
                deleteRecords(rowList_out);
                holdingpen.rowList = [];
                holdingpen.rowIndexList = [];
            }
        }
    });

    $(document).keyup(function(e){
        if (e.keyCode == 27) {  // esc           
            deselectAll();
            console.log($('#select-all'));
        }   
    });

    return{
        selectRow: selectRow,
        deselectAll: deselectAll,
        hoverRow: hoverRow,
        unhoverRow: unhoverRow,

        removeSelection: function () {
            if (window.getSelection) {  // all browsers, except IE before version 9
                var selection = window.getSelection ();                                        
                selection.removeAllRanges ();
            }
            else {
                if (document.selection.createRange) {        // Internet Explorer
                    var range = document.selection.createRange ();
                    document.selection.empty ();
                }
            }
        },

        selectRange: function (row){
            var toPos = oTable.fnGetPosition(row) + oSettings._iDisplayStart;
            var fromPos = holdingpen.rowIndexList[holdingpen.rowIndexList.length-1];
            var i;
            var current_row = null;

            if (toPos > fromPos){
                for (i=fromPos; i<=toPos; i++){
                    j = i % 10;
                    if($.inArray(i, rowIndexList) <= -1){
                        current_row = oSettings.aoData[oSettings.aiDisplay[j]].nTr;
                        if (selectCellByTitle(current_row, 'Actions').innerText != 'N/A'){
                            holdingpen.rowIndexList.push(i);
                            holdingpen.rowList.push(current_row.row_id);
                            current_row.style.background = "#ffa";
                            current_row.checkbox.checked = true;
                        }
                    }
                }
            }
            else{
                for (i=fromPos; i>=toPos; i--){
                    j = i % 10;
                    if($.inArray(i, holdingpen.rowIndexList) <= -1){
                        current_row = oSettings.aoData[oSettings.aiDisplay[j]].nTr
                        if (selectCellByTitle(current_row, 'Actions').innerText != 'N/A'){
                            holdingpen.rowIndexList.push(i);
                            holdingpen.rowList.push(current_row.row_id);
                            current_row.style.background = "#ffa";
                            current_row.checkbox.checked = false;
                        }
                    }
                }
            }
            document.getSelection().removeAllRanges();
        },

        rememberSelected: function (row, id) {
            if($.inArray(id, holdingpen.rowList) > -1){
                row.style.background = "#ffa";
                row.cells[0].firstChild.checked = true;
            }
        },

        getCellIndex: function (row, title){
            for(var i=0; i<oSettings.aoHeader[0].length; i++){
                var trimmed_title = $.trim(oSettings.aoHeader[0][i].cell.innerText);
                if(trimmed_title === title){
                    return i
                }
            }   
        }       
    };
}
//***********************************