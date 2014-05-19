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


// DataTables row selection functions
//***********************************
var WORKFLOWS_HP_SELECTION = function ($, holdingpen) {
    var oTable = {},
        oSettings = {},
        hoveredRow = -1;

    function init(_oTable, _oSettings) {
        oTable = _oTable;
        oSettings = _oSettings;
    }

    function selectAll() {
        var fromPos = holdingpen.oSettings._iDisplayStart,
            toPos = holdingpen.oSettings._iDisplayLength - 1 + fromPos,
            current_row,
            j,
            i;

        current_row = null;
        for (i = fromPos; i <= toPos; i++) {
            j = i % holdingpen.oSettings._iDisplayLength;
            current_row = holdingpen.oSettings.aoData[holdingpen.oSettings.aiDisplay[j]].nTr;
            if ($.inArray(current_row.row_id, holdingpen.rowList) <= -1) {
                holdingpen.rowIndexList.push(i);
                holdingpen.rowList.push(current_row.row_id);
                current_row.style.background = "#ffa";
                current_row.cells[0].firstChild.checked = true;
            }
        }
    }

    function selectCellByTitle(row, title) {
        var i,
            text_to_process,
            trimmed_title;
        for (i = 0; i < holdingpen.oSettings.aoHeader[0].length; i++) {
            text_to_process = holdingpen.oSettings.aoHeader[0][i].cell.textContent || holdingpen.oSettings.aoHeader[0][i].cell.innerText;
            trimmed_title = $.trim(text_to_process);
            if (trimmed_title === title) {
                return $(row).children()[i - 1];
            }
        }
    }

    function selectCellByTitle_content(row, title) {
        var A = selectCellByTitle(row, title);
        A = A.innerText || A.textContent;
        return A;
    }

    function deselectAllFromPage(event) {
        var fromPos = holdingpen.oSettings._iDisplayStart,
            toPos = holdingpen.oSettings._iDisplayLength - 1 + fromPos,
            j,
            i,
            current_row = null,
            widget_name;

        for (i = fromPos; i <= toPos; i++) {
            j = i % holdingpen.oSettings._iDisplayLength;
            current_row = holdingpen.oSettings.aoData[holdingpen.oSettings.aiDisplay[j]].nTr;
            if ($.inArray(current_row.row_id, holdingpen.rowList) > -1) {
                holdingpen.rowList.splice(holdingpen.rowList.indexOf(current_row.row_id), 1);
                holdingpen.rowIndexList.splice(holdingpen.rowIndexList.indexOf(current_row._DT_RowIndex + holdingpen.oSettings._iDisplayStart), 1);
                current_row.style.background = "white";
                widget_name = selectCellByTitle_content(current_row, 'Actions');
                if (widget_name !== 'N/A') {
                    if (widget_name === 'Approve Record') {
                        holdingpen.recordsToApprove.splice(holdingpen.recordsToApprove.indexOf(current_row.row_id), 1);
                    }
                }
                current_row.checkbox.checked = false;
            }
        }
    }

    function selectRow(row, e, oSettings) {
        var selectedRow = row,
            widget_name;

        if (e.shiftKey === true) {

            this.selectRange(row);
        } else {
            if (selectCellByTitle(row, 'Actions').childNodes[0].id === 'submitButtonMini') {
                widget_name = 'Approve Record';
            }
            if ($.inArray(row.row_id, holdingpen.rowList) <= -1) {
                // Select row
                holdingpen.rowList.push(row.row_id);
                holdingpen.rowIndexList.push(row._DT_RowIndex + oSettings._iDisplayStart);
                row.style.background = "#ffa";
                if (selectCellByTitle_content(row, 'Actions') !== 'N/A') {
                    if (widget_name === 'Approve Record') {
                        holdingpen.recordsToApprove.push(row.row_id);
                    }
                }
                row.checkbox.checked = true;
            } else {
                $('#select-all')[0].checked = false;
                // De-Select
                holdingpen.rowList.splice(holdingpen.rowList.indexOf(row.row_id), 1);
                holdingpen.rowIndexList.splice(holdingpen.rowIndexList.indexOf(row._DT_RowIndex + holdingpen.oSettings._iDisplayStart), 1);
                row.style.background = "white";
                if (selectCellByTitle_content(row, 'Actions') !== 'N/A') {
                    if (widget_name === 'Approve Record') {
                        holdingpen.recordsToApprove.splice(holdingpen.recordsToApprove.indexOf(row.row_id), 1);
                    }
                }
                row.checkbox.checked = false;
            }
        }
        window['approval'].checkRecordsToApprove();
    }

    function removeSelection() {
        var range;
        if (window.getSelection) {  // all browsers, except IE before version 9
            var selection = window.getSelection();
            selection.removeAllRanges();
        } else {
            if (document.selection.createRange) {        // Internet Explorer
                range = document.selection.createRange();
                document.selection.empty();
            }
        }
    }

    function deselectAll() {
        holdingpen.rowList = [];
        holdingpen.rowIndexList = [];
        holdingpen.oTable.fnDraw(false);
        window.getSelection().removeAllRanges();
    }

    function hoverRow(row) {
        row.style.background = "#FFFFEE";
    }

    function unhoverRow (row) {
        if ($.inArray(row.row_id, holdingpen.rowList) > -1) {
            row.style.background = "#ffa";
        } else {
            row.style.cssText = defaultcss;
        }
    }

    $("#select-all").on("click", function (event) {
        if ($(this)[0].checked === true) {
            selectAll();
        } else {
            deselectAllFromPage(event.originalEvent);
        }
    });

    window.addEventListener("keydown", function (e) {
        var currentRowIndex,
            current_row,
            row_index,
            rowToAdd,
            rowList_out;

        if ([37, 38, 39, 40].indexOf(e.keyCode) > -1) {
            e.preventDefault();
        }
        if (e.keyCode === 40) {
            if (e.shiftKey === true) {
                currentRowIndex =  holdingpen.rowIndexList[holdingpen.rowIndexList.length - 1];
                if (currentRowIndex < 9) {
                    row_index = currentRowIndex + 1;
                    current_row = holdingpen.oSettings.aoData[holdingpen.oSettings.aiDisplay[row_index]].nTr;
                    if ($.inArray(current_row.row_id, holdingpen.rowList) <= -1) {
                        holdingpen.rowIndexList.push(row_index);
                        holdingpen.rowList.push(current_row.row_id);
                        current_row.style.background = "#ffa";
                        current_row.checkbox.checked = true;
                    }
                }
            } else {
                if (hoveredRow < 9) {
                    if (hoveredRow !== -1) {
                        unhoverRow(holdingpen.oSettings.aoData[holdingpen.oSettings.aiDisplay[hoveredRow]].nTr);
                    }
                    hoveredRow++;
                    hoverRow(holdingpen.oSettings.aoData[holdingpen.oSettings.aiDisplay[hoveredRow]].nTr);
                }
            }
        } else if (e.keyCode === 38) {
            if (e.shiftKey === true) {
                currentRowIndex = holdingpen.rowIndexList[holdingpen.rowIndexList.length - 1];
                if (currentRowIndex > 0) {
                    rowToAdd = currentRowIndex - 1;
                    current_row = holdingpen.oSettings.aoData[holdingpen.oSettings.aiDisplay[rowToAdd]].nTr;
                    if ($.inArray(current_row.row_id, holdingpen.rowList) <= -1) {
                        holdingpen.rowIndexList.push(rowToAdd);
                        holdingpen.rowList.push(current_row.row_id);
                        current_row.style.background = "#ffa";
                        current_row.checkbox.checked = true;
                    }
                }
            } else {
                if (hoveredRow > 0) {
                    unhoverRow(holdingpen.oSettings.aoData[holdingpen.oSettings.aiDisplay[hoveredRow]].nTr);
                    hoveredRow--;
                    hoverRow(holdingpen.oSettings.aoData[holdingpen.oSettings.aiDisplay[hoveredRow]].nTr);
                }
            }
        } else if (e.keyCode === 37) {
            holdingpen.oTable.fnPageChange('previous');
        } else if (e.keyCode === 39) {
            holdingpen.oTable.fnPageChange('next');
        } else if (e.keyCode === 65 && e.ctrlKey === true) {
            $("#select-all").click();
            e.preventDefault();
        } else if (e.keyCode === 13 && hoveredRow !== -1) {
            selectCellByTitle(holdingpen.oSettings.aoData[holdingpen.oSettings.aiDisplay[hoveredRow]].nTr, 'Details').click();
        } else if (e.keyCode === 46) {
            if (holdingpen.rowList.length >= 1) {
                rowList_out = JSON.stringify(holdingpen.rowList);
                deleteRecords(rowList_out);
                holdingpen.rowList = [];
                holdingpen.rowIndexList = [];
            }
        }
    });

    $(document).keyup(function (e) {
        if (e.keyCode === 27) {  // esc
            deselectAll();
        }
    });



    return {
        init: init,
        selectRow: selectRow,
        deselectAll: deselectAll,
        hoverRow: hoverRow,
        unhoverRow: unhoverRow,
        removeSelection : removeSelection,

        selectRange: function (row) {
            var toPos = holdingpen.oTable.fnGetPosition(row) + holdingpen.oSettings._iDisplayStart,
                fromPos = holdingpen.rowIndexList[holdingpen.rowIndexList.length - 1],
                i,
                j,
                current_row = null;

            if ((fromPos !== undefined) && (toPos !== undefined) && (row.checkbox.checked)) {
                if (toPos > fromPos) {
                    for (i = fromPos + 1; i <= toPos; i++) {
                        j = i % holdingpen.oSettings._iDisplayLength;
                        if ($.inArray(i, holdingpen.rowIndexList) <= -1) {
                            current_row = holdingpen.oSettings.aoData[holdingpen.oSettings.aiDisplay[j]].nTr;
                            holdingpen.rowIndexList.push(i);
                            holdingpen.rowList.push(current_row.row_id);
                            current_row.style.background = "#ffa";
                            current_row.checkbox.checked = true;
                        }
                    }
                } else {
                    for (i = fromPos - 1; i >= toPos; i--) {
                        j = i % holdingpen.oSettings._iDisplayLength;
                        if ($.inArray(i, holdingpen.rowIndexList) <= -1) {
                            current_row = holdingpen.oSettings.aoData[holdingpen.oSettings.aiDisplay[j]].nTr;
                            holdingpen.rowIndexList.push(i);
                            holdingpen.rowList.push(current_row.row_id);
                            current_row.style.background = "#ffa";
                            current_row.checkbox.checked = true;
                        }
                    }
                }
                document.getSelection().removeAllRanges();
            } else {
                if ($.inArray(holdingpen.oTable.fnGetPosition(row), holdingpen.rowIndexList) <= -1) {
                    holdingpen.rowIndexList.push(holdingpen.oTable.fnGetPosition(row));
                    holdingpen.rowList.push(row.row_id);
                    row.style.background = "#ffa";
                    row.checkbox.checked = true;
                } else {
                    $('#select-all')[0].checked = false;
                    holdingpen.rowList.splice(holdingpen.rowList.indexOf(row.row_id), 1);
                    holdingpen.rowIndexList.splice( holdingpen.rowIndexList.indexOf(row._DT_RowIndex + holdingpen.oSettings._iDisplayStart), 1);
                    row.style.background = "white";
                    row.checkbox.checked = false;
                }
            }
        },

        rememberSelected: function (row, id) {
            if ($.inArray(id, holdingpen.rowList) > -1) {
                row.style.background = "#ffa";
                row.cells[0].firstChild.checked = true;
            }
        },

        getCellIndex: function (row, title) {
            var i,
                temp_cell,
                temp_cell_value,
                trimmed_title;
            for (i = 0; i < holdingpen.oSettings.aoHeader[0].length; i++) {
                temp_cell =  holdingpen.oSettings.aoHeader[0][i].cell;
                temp_cell_value = temp_cell.innerText || temp_cell.textContent;
                trimmed_title = $.trim(temp_cell_value);
                if (trimmed_title === title) {
                    return i;
                }
            }
        }
    };
}($, WORKFLOWS_HOLDINGPEN);
//***********************************
