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

var WORKFLOWS_HOLDINGPEN = (function ($) {
    var oTable,
        oSettings,
        selectedRow,
        rowList = [],
        rowIndexList = [],
        recordsToApprove = [],
        defaultcss = "#example tbody tr.even:hover, #example tbody tr.odd:hover {background-color: #FFFFCC;}",
        context = {},
        datatable = {},
        tag = {},
        utilities = {};

    return {
        oTable: oTable,
        oSettings: oSettings,
        selectedRow: selectedRow,
        rowList: rowList,
        rowIndexList: rowIndexList,
        recordsToApprove: recordsToApprove,
        defaultcss: defaultcss,
        context: context,
        datatable: datatable,
        tag: tag,
        utilities: utilities,

        init: function (data) {
            this.context = data;
            this.tag = window.WORKFLOWS_HP_TAGS;
            this.tag.init();
            this.datatable = window.WORKFLOWS_HP_SELECTION;
            this.utilities = window.WORKFLOWS_HP_UTILITIES;
            this.utilities.init();
            this.datatable.init(this.oTable, this.oSettings);
            this.utilities.autorefresh();
        },

        init_datatable: function (datatable) {
            oSettings = {
                "dom": '<"top"iflp<"clear">>rt<"bottom"iflp<"clear">>',
                "bFilter": false,
                "bJQueryUI": true,
                "bProcessing": true,
                "bServerSide": true,
                "bDestroy": true,
                "sAjaxSource": this.context.holdingpen.url_load,
                "oColVis": {
                    "buttonText": "Select Columns",
                    "bRestore": true,
                    "sAlign": "left",
                    "iOverlayFade": 1
                },
                "aoColumnDefs": [{'bSortable': false, 'aTargets': [1]},
                                 {'bSearchable': false, 'bVisible': false, 'aTargets': [0]},
                                 {'sWidth': "25%", 'aTargets': [2]},
                                 {'sWidth': "25%", 'aTargets': [3]}],
                "fnRowCallback": function (nRow, aData, iDisplayIndex, iDisplayIndexFull) {
                    var id = aData[0];
                    datatable.rememberSelected(nRow, id);
                    nRow.row_id = id;
                    nRow.checkbox = nRow.cells[0].firstChild;
                    $(nRow).on("click", "td", function (event) {
                        console.log(event);
                        if(event.target.nodeName != "INPUT") {
                            datatable.selectRow(nRow, event, oTable.fnSettings());
                        }
                    });
                },
                "fnDrawCallback": function () {
                    $('table#maintable td').bind('mouseenter', function () {
                        $(this).parent().children().each(function () {
                            $(this).addClass('maintablerowhover');
                        });
                    });
                    $('table#maintable td').bind('mouseleave', function () {
                        $(this).parent().children().each(function () {
                            $(this).removeClass('maintablerowhover');
                        });
                    });
                    $('#select-all')[0].checked = false;
                }
            };
            oTable = $('#maintable').dataTable(oSettings);
            $('.dropdown-toggle').dropdown();
            this.oSettings = oTable.fnSettings();
            this.oTable = oTable;

        }
    };
})(window.jQuery);

