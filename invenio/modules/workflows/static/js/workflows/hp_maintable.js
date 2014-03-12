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

var holdingpen = (function ( $ ){
    var oTable;
    var oSettings;
    var selectedRow;
    var rowList = [];
    var rowIndexList = [];
    var recordsToApprove = [];
    var defaultcss='#example tbody tr.even:hover, #example tbody tr.odd:hover {background-color: #FFFFCC;}';     

    url = new Object();

    return { 
        oTable: oTable,
        oSettings: oSettings,
        selectedRow: selectedRow,
        rowList: rowList,
        rowIndexList: rowIndexList,
        recordsToApprove: recordsToApprove,
        defaultcss: defaultcss,

        init_urls: function (url_) {
            url.load_table = url_.load_table;
            url.batch_widget = url_.batch_widget;
            url.resolve_widget = url_.resolve_widget;
            url.delete_single = url_.delete_single;
            url.refresh = url_.refresh;
            url.widget = url_.widget;
            url.details = url_.details;
        },

        init_datatable: function (version_showing){
            oSettings = {
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
                "aoColumnDefs":[{'bSortable': false, 'aTargets': [1]},
                                {'bSearchable': false, 'bVisible': false, 'aTargets': [0]},
                                {'sWidth': "25%", 'aTargets': [2]},
                                {'sWidth': "15%", 'aTargets': [4]}],
                "fnRowCallback": function( nRow, aData, iDisplayIndex, iDisplayIndexFull ) {
                    var id = aData[0];
                    holdingpen.datatable.rememberSelected(nRow, id);
                    oSettings = oTable.fnSettings();
                    nRow.row_id = id;
                    nRow.checkbox = nRow.cells[0].firstChild;
                    nRow.addEventListener("click", function(e) {
                        holdingpen.datatable.selectRow(nRow, e, oSettings);
                    });
                },
                "fnDrawCallback": function(){
                    $('table#maintable td').bind('mouseenter', function () {
                        $(this).parent().children().each(function() {
                            $(this).addClass('maintablerowhover');
                        });
                    });
                    $('table#maintable td').bind('mouseleave', function () {
                        $(this).parent().children().each(function() {
                            $(this).removeClass('maintablerowhover');
                        });
                    });
                }
            };
            oTable = $('#maintable').dataTable(oSettings);
            oTable.on('page', function( e, o) {
                $('#select-all')[0].checked = false;
            });
            $('.dropdown-toggle').dropdown();
            return [oTable, oTable.fnSettings()];
        }
    }
})( window.jQuery );

