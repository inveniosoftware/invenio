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

var oTable;
var selectedRow;
var rowList = [];
var rowIndexList = [];
var hoveredRow = -1;
var tagList = [];
var recordsToApprove = [];
var defaultcss='#example tbody tr.even:hover, #example tbody tr.odd:hover {background-color: #FFFFCC;}';

var url_load_table;
var url_batch_widget;
var url_resolve_widget;
var url_delete_single;
var url_refresh;
var url_widget;
var url_details;


function init_maintable(url_load_table_, url_batch_widget_, url_resolve_widget_, url_delete_single_,
                        url_refresh_, url_widget_, url_details_) {
    url_load_table = url_load_table_;
    url_batch_widget = url_batch_widget_;
    url_resolve_widget = url_resolve_widget_;
    url_delete_single = url_delete_single_;
    url_refresh = url_refresh_;
    url_widget = url_widget_;
    url_details = url_details_;

    init_datatable();
}

function init_datatable(){
    oTable = $('#example').dataTable( {
        "sDom": 'lfC<"clear">rtip',
        "bJQueryUI": true,
        "bProcessing": true,
        "bServerSide": true,
        "bDestroy": true,
        "sAjaxSource": url_load_table,
        "oColVis": {
            "buttonText": "Select Columns",
            "bRestore": true,
            "sAlign": "left",
            "iOverlayFade": 1
        },
        "aoColumnDefs": [
            {"mRender": function (data) {return '<abbr class="timeago" title="'+data.substring(data.indexOf('#')+1)+'">'+data.substring(0,data.indexOf('#'))+'</abbr>';}, "aTargets": [6]},
            {"mRender": function (data) {if (data == 1) {return '<span class="label label-success">Final</span>';}
                                         else if (data == 2) {return '<span class="label label-warning">Halted</span>';}
                                         else if (data == 3) {return '<span class="label label-info">Running</span>';}}, "aTargets": [7]},
            {"mRender": function (data) {return '<a href=' + url_details + '?bwobject_id=' + data + '>'
                                                 + 'Details' + '</a>';}, "aTargets": [8]},
            {"mRender": function (data, type, full) {var w_name = data.substring(0,data.indexOf('#'));
                                                     if ( w_name != 'None'){
                                                        var widget_link = '<a href=' + url_widget + '?bwobject_id='
                                                            + full[0] + '&widget=' + data.substring(0,data.indexOf('#')) + '>' + data.substring(data.indexOf('#')+1) + '</a>';
                                                        if (w_name == 'approval_widget'){
                                                                widget_link += '</br>' +
                                                                '<button type="button" class="btn btn-danger btn-mini"><a id="reject-mini" href="javascript:void(0)" class="mini-approval-btn" onclick="mini_approval(this.id,'+full[0]+')">Reject</a></button>' +
                                                                '<button type="button" class="btn btn-success btn-mini"><a id="accept-mini" href="javascript:void(0)" class="mini-approval-btn" onclick="mini_approval(this.id,'+full[0]+')">Accept</a></button>';
                                                        }
                                                        return widget_link;
                                                     }
                                                     else
                                                        {return 'N/A';}}, "aTargets": [9]}
        ],
        "fnRowCallback": function( nRow, aData, iDisplayIndex, iDisplayIndexFull ) {
            rememberSelected(nRow);
            oSettings = oTable.fnSettings();
            nRow.addEventListener("click", function(e) {
                selectRow(nRow, e, oSettings);
            });
        }
    } );
}

$('#batch_btn').on('click', function() {
    if (rowList.length >= 1){
        var rowList_out = JSON.stringify(rowList);
        console.log(rowList_out);
        window.location = url_batch_widget + "?bwolist=" + rowList_out;
        $(this).prop("disabled", true);
        return false;
    }
});

$('#refresh_button').on('click', function() {
    jQuery.ajax({
        url: url_refresh,
        success: function(json){

        }
    });
    oTable.fnDraw(false);
});

// DataTables row selection functions
//***********************************
function hoverRow(row) {
    row.style.background = "#FFFFEE";
}

function unhoverRow(row) {
    if($.inArray(row.cells[0].innerText, rowList) > -1){
        row.style.background = "#ffa";
    }
    else{
        row.style.cssText = defaultcss;
    }
}

function removeSelection () {
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
}

function selectRange(row){
    var toPos = oTable.fnGetPosition(row) + oSettings._iDisplayStart;
    var fromPos = rowIndexList[rowIndexList.length-1];
    var i;

    if (toPos > fromPos){
        for (i=fromPos; i<=toPos; i++){
            j = i % 10;
            if($.inArray(i, rowIndexList) <= -1){
                if (oSettings.aoData[oSettings.aiDisplay[j]].nTr.cells[9].innerText != 'N/A'){
                    rowIndexList.push(i);
                    rowList.push(oSettings.aoData[oSettings.aiDisplay[j]].nTr.cells[0].innerText);
                    oSettings.aoData[oSettings.aiDisplay[j]].nTr.style.background = "#ffa";
                }
            }
        }
    }
    else{
        for (i=fromPos; i>=toPos; i--){
            j = i % 10;
            if($.inArray(i, rowIndexList) <= -1){
                if (oSettings.aoData[oSettings.aiDisplay[j]].nTr.cells[9].innerText != 'N/A'){
                    rowIndexList.push(i);
                    rowList.push(oSettings.aoData[oSettings.aiDisplay[j]].nTr.cells[0].innerText);
                    oSettings.aoData[oSettings.aiDisplay[j]].nTr.style.background = "#ffa";
                }
            }
        }
    }
    document.getSelection().removeAllRanges();
}

function selectAll(){
    var toPos = oSettings._iDisplayLength - 1;
    var fromPos = 0;

    for (var i=fromPos; i<=toPos; i++){
        if($.inArray(oSettings.aoData[oSettings.aiDisplay[i]].nTr.cells[0].innerText, rowList) <= -1){
            if (oSettings.aoData[oSettings.aiDisplay[i]].nTr.cells[9].innerText != 'N/A'){
                rowIndexList.push(i);
                rowList.push(oSettings.aoData[oSettings.aiDisplay[i]].nTr.cells[0].innerText);
                oSettings.aoData[oSettings.aiDisplay[i]].nTr.style.background = "#ffa";
            }
        }
    }
}

function rememberSelected(row) {
    selectedRow = row;
    if($.inArray(row.cells[0].innerText, rowList) > -1){
        selectedRow.style.background = "#ffa";
    }
}

window.addEventListener("keydown", function(e){
    var currentRowIndex;
    if([32, 37, 38, 39, 40].indexOf(e.keyCode) > -1) {
        e.preventDefault();
    }
    if (e.keyCode == 40) {
        if (e.shiftKey === true){
            currentRowIndex = rowIndexList[rowIndexList.length-1];
            if (currentRowIndex < 9){
                rowToAdd = currentRowIndex + 1;
                if($.inArray(oSettings.aoData[oSettings.aiDisplay[rowToAdd]].nTr.cells[0].innerText, rowList) <= -1){
                    rowIndexList.push(rowToAdd);
                    rowList.push(oSettings.aoData[oSettings.aiDisplay[rowToAdd]].nTr.cells[0].innerText);
                    oSettings.aoData[oSettings.aiDisplay[rowToAdd]].nTr.style.background = "#ffa";
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
            currentRowIndex = rowIndexList[rowIndexList.length-1];
            if (currentRowIndex > 0){
                rowToAdd = currentRowIndex - 1;
                if($.inArray(oSettings.aoData[oSettings.aiDisplay[rowToAdd]].nTr.cells[0].innerText, rowList) <= -1){
                    rowIndexList.push(rowToAdd);
                    rowList.push(oSettings.aoData[oSettings.aiDisplay[rowToAdd]].nTr.cells[0].innerText);
                    oSettings.aoData[oSettings.aiDisplay[rowToAdd]].nTr.style.background = "#ffa";
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
        oSettings.aoData[oSettings.aiDisplay[hoveredRow]].nTr.cells[8].click();
    }
    else if(e.keyCode == 46){
        if (rowList.length >= 1){
            var rowList_out = JSON.stringify(rowList);
            deleteRecords(rowList_out);
            rowList = [];
            rowIndexList = [];
        }
    }
});

function selectRow(row, e, oSettings) {
    selectedRow = row;
    if( e.shiftKey === true ){
        selectRange(row);
    }
    else{
        if($.inArray(row.cells[0].innerText, rowList) <= -1){
            if (row.cells[9].innerText != 'N/A'){
                rowList.push(row.cells[0].innerText);
                rowIndexList.push(row._DT_RowIndex+oSettings._iDisplayStart);
                selectedRow.style.background = "#ffa";
                if(row.cells[9].childNodes[0].innerText === 'Approve Record'){
                    recordsToApprove.push(row.cells[0].innerText);
                }
            }
        }
        else{
            rowList.splice(rowList.indexOf(row.cells[0].innerText), 1);
            rowIndexList.splice(rowIndexList.indexOf(row._DT_RowIndex+oSettings._iDisplayStart), 1);
            selectedRow.style.background = "white";
            if(row.cells[9].childNodes[0].innerText === 'Approve Record'){
                recordsToApprove.splice(recordsToApprove.indexOf(row.cells[0].innerText), 1);
            }
        }
    }
    checkRecordsToApprove();

    console.log(rowList);
    console.log(rowIndexList);
    console.log(recordsToApprove);
}

function deselectAll(){
    rowList = [];
    rowIndexList = [];
    oTable.fnDraw(false);
    window.getSelection().removeAllRanges();
}

$(document).keyup(function(e){
    if (e.keyCode == 27) {  // esc
        deselectAll();
    }
});
//***********************************

// Tags functions
//***********************************
$('.task-btn').on('click', function(){
    if($.inArray($(this)[0].name, tagList) <= -1){
        var widget_name = $(this)[0].name;
        $('.tag-area').html('');
        $('.tag-area').append('<div class="alert alert-info tag-alert span1">'+widget_name+'<a class="close-btn" data-dismiss="alert" name='+widget_name+' onclick="closeTag(this)">&times;</a></div>');
        tagList = [];

        tagList.push($(this)[0].name);
    }
    oTable.fnFilter($(this)[0].name);
});

function closeTag(obj){
    tagList = [];
    $('.tag-area').html('');
    oTable.fnFilter('');
    // tagList.splice(tagList.indexOf(obj.name), 1);
    console.log(tagList);
};
//***********************************

//Utility functions
//***********************************
function fnGetSelected( oTableLocal ){
    var aReturn = [];
    var aTrs = oTableLocal.fnGetNodes();
    
    for ( var i=0 ; i<aTrs.length ; i++ ){
        if ($(aTrs[i]).hasClass('row_selected')){
            aReturn.push( aTrs[i] );
        }
    }
    return aReturn;
}

function isInt(n) {
   return typeof n === 'number' && n % 1 === 0;
}

function emptyLists(){
    rowList = [];
    rowIndexList = [];
}

function bootstrap_alert(message) {
    $('#alert-message').html('<span class="alert"><a class="close" data-dismiss="alert"> ×</a><span>'+message+'</span></span>');
}
//***********************************