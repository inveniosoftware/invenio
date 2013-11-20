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

url = new Object();

function init_urls(url_) {
    url.load_table = url_.load_table;
    url.batch_widget = url_.batch_widget;
    url.resolve_widget = url_.resolve_widget;
    url.delete_single = url_.delete_single;
    url.refresh = url_.refresh;
    url.widget = url_.widget;
    url.details = url_.details;

    init_datatable();
}
    
function init_datatable(){
    oTable = $('#example').dataTable({
        "sDom": 'lf<"clear">rtip',
        "bJQueryUI": true,
        "bProcessing": true,
        "bServerSide": true,
        "bDestroy": true,
        "sAjaxSource": url.load_table,
        "oColVis": {
            "buttonText": "Select Columns",
            "bRestore": true,
            "sAlign": "left",
            "iOverlayFade": 1
        },
        "aoColumnDefs":[{'bSortable': false, 'aTargets': [0]}],
        "fnRowCallback": function( nRow, aData, iDisplayIndex, iDisplayIndexFull ) {
            rememberSelected(nRow);
            oSettings = oTable.fnSettings();
            nRow.addEventListener("click", function(e) {
                selectRow(nRow, e, oSettings);
            });
        }
    });
    oSettings = oTable.fnSettings();
    return oTable;
    // $('#version-halted').click();
}

$('#batch_btn').on('click', function() {
    if (rowList.length >= 1){
        var rowList_out = JSON.stringify(rowList);
        console.log(rowList_out);
        window.location = url.batch_widget + "?bwolist=" + rowList_out;
        $(this).prop("disabled", true);
        return false;
    }
});

$('#refresh_button').on('click', function() {
    jQuery.ajax({
        url: url.refresh,
        success: function(json){
            
        }
    });
    oTable.fnDraw(false);
});

// DataTables row selection functions
//***********************************
$("#select-all").on("click", function(){
    selectAll();
})

function hoverRow(row) {
    row.style.background = "#FFFFEE";
}

function unhoverRow(row) {
    if($.inArray(selectCellByTitle(row, 'Id').innerText, rowList) > -1){
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
                if (selectCellByTitle(oSettings.aoData[oSettings.aiDisplay[j]].nTr, 'Actions').innerText != 'N/A'){
                    rowIndexList.push(i);
                    rowList.push(selectCellByTitle(oSettings.aoData[oSettings.aiDisplay[j]].nTr, 'Id').innerText);
                    oSettings.aoData[oSettings.aiDisplay[j]].nTr.style.background = "#ffa";
                    checkbox = selectCellByTitle(oSettings.aoData[oSettings.aiDisplay[j]].nTr, "").childNodes[1];
                    checkbox.checked = true;
                }
            }
        }
    }
    else{
        for (i=fromPos; i>=toPos; i--){
            j = i % 10;
            if($.inArray(i, rowIndexList) <= -1){
                console.log(oSettings.aoData[oSettings.aiDisplay[j]].nTr);
                if (selectCellByTitle(oSettings.aoData[oSettings.aiDisplay[j]].nTr, 'Actions').innerText != 'N/A'){
                    rowIndexList.push(i);
                    rowList.push(selectCellByTitle(oSettings.aoData[oSettings.aiDisplay[j]].nTr, 'Id').innerText);
                    oSettings.aoData[oSettings.aiDisplay[j]].nTr.style.background = "#ffa";
                    checkbox = selectCellByTitle(oSettings.aiDisplay[j].nTr, "").childNodes[1];
                    checkbox.checked = false;
                }
            }
        }
    }
    document.getSelection().removeAllRanges();
}

function selectAll(){
    console.log("selecting all");
    var toPos = oSettings._iDisplayEnd - 1;
    var fromPos = 0;

    for (var i=fromPos; i<=toPos; i++){
        if($.inArray(selectCellByTitle(oSettings.aoData[oSettings.aiDisplay[i]].nTr, 'Id').innerText, rowList) <= -1){
            if (selectCellByTitle(oSettings.aoData[oSettings.aiDisplay[i]].nTr, 'Actions').innerText != 'N/A'){
                rowIndexList.push(i);
                rowList.push(selectCellByTitle(oSettings.aoData[oSettings.aiDisplay[i]].nTr, 'Id').innerText);
                oSettings.aoData[oSettings.aiDisplay[i]].nTr.style.background = "#ffa";
            }
        }
    }
}

function rememberSelected(row) {
    selectedRow = row;
    if($.inArray($.trim(selectCellByTitle(row, 'Id').innerText), rowList) > -1){
        selectedRow.style.background = "#ffa";
        selectedRow.cells[0].childNodes[1].checked = true;
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
                if($.inArray(selectCellByTitle(oSettings.aoData[oSettings.aiDisplay[rowToAdd]].nTr, 'Id').innerText, rowList) <= -1){
                    rowIndexList.push(rowToAdd);
                    rowList.push(selectCellByTitle(oSettings.aoData[oSettings.aiDisplay[rowToAdd]].nTr, 'Id').innerText);
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
                if($.inArray(selectCellByTitle(oSettings.aoData[oSettings.aiDisplay[rowToAdd]].nTr, 'Id').innerText, rowList) <= -1){
                    rowIndexList.push(rowToAdd);
                    rowList.push(selectCellByTitle(oSettings.aoData[oSettings.aiDisplay[rowToAdd]].nTr, 'Id').innerText);
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
        selectCellByTitle(oSettings.aoData[oSettings.aiDisplay[hoveredRow]].nTr, 'Details').click();
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

function selectCellByTitle(row, title){
    for(var i=0; i<oSettings.aoHeader[0].length; i++){
        var trimmed_title = $.trim(oSettings.aoHeader[0][i].cell.innerText);
        if(trimmed_title === title){
            return row.cells[i];
        }
    }
}

function selectRow(row, e, oSettings) {
    selectedRow = row;
    if( e.shiftKey === true ){
        selectRange(row);
    }
    else{
        var widget_name = selectCellByTitle(row, 'Actions').innerText;    
        widget_name = widget_name.substring(0, widget_name.length-4);
        
        if($.inArray(selectCellByTitle(row, 'Id').innerText, rowList) <= -1){
            if (selectCellByTitle(row, 'Actions').innerText != 'N/A'){
                rowList.push(selectCellByTitle(row, 'Id').innerText);
                rowIndexList.push(row._DT_RowIndex+oSettings._iDisplayStart);
                selectedRow.style.background = "#ffa";
                
                if(widget_name === 'Approve Record'){
                    recordsToApprove.push(selectCellByTitle(row, 'Id').innerText);
                }
                checkbox = selectCellByTitle(row, "").childNodes[1];
                console.log(checkbox);
                checkbox.checked = true;
            }
        }
        else{
            rowList.splice(rowList.indexOf(selectCellByTitle(row, 'Id').innerText), 1);
            rowIndexList.splice(rowIndexList.indexOf(row._DT_RowIndex+oSettings._iDisplayStart), 1);
            selectedRow.style.background = "white";
            
            if(widget_name === 'Approve Record'){
                recordsToApprove.splice(recordsToApprove.indexOf(selectCellByTitle(row, 'Id').innerText), 1);
            }
            checkbox = selectCellByTitle(row, "").childNodes[1];
            checkbox.checked = false;
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
        $('#tag-area').append('<div class="alert alert-info tag-alert col-md-1">'+widget_name+'<a id="'+widget_name+'class="close-btn" data-dismiss="alert" name='+widget_name+' onclick="closeTag(this.parentElement)">&times;</a></div>');
        tagList.push($(this)[0].name);
        oTable.fnFilter($(this)[0].name);

    }
    else{
        closeTag($('#'+widget_name));
        oTable.fnFilter( '^$', 4, true, false );
        $('#refresh_button').click();
    }   
    // requestNewObjects();
});

$('.version-selection').on('click', function(){
    console.log($(this)[0].name);
    console.log(tagList);

    if($.inArray($(this)[0].name, tagList) <= -1){
        console.log("TAG NOT IN TAGLIST");
        $('#tag-area').append('<div id="tag-version-'+$(this)[0].name+'" name="'+$(this)[0].name+'" class="alert alert-info tag-alert col-md-1">'+$(this)[0].name+'<a class="close-btn pull-right" data-dismiss="alert" onclick="closeTag(this.parentElement)">&times;</a></div>');
        tagList.push($(this)[0].name);
    } 
    else{
        closeTag($('#tag-version-'+$(this)[0].name)[0]);
    }    
    requestNewObjects();
});

function closeTag(obj){
    // console.log(tagList);
    // console.log(obj);
    // console.log(obj.name);
    var tag_name = obj.innerText.substr(0,obj.innerText.length-1);
    console.log(tag_name);
    tagList.splice(tagList.indexOf(obj.name), 1);
    
    obj.remove();
    requestNewObjects();
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

function requestNewObjects(){
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
            $('#refresh_button').click();
        }
    });
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


