/*
 * This file is part of Invenio.
 * Copyright (C) 2012 CERN.
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

$(function() {
  /*
   * DOM is ready. Initialize all components.
   */
  initFileList();
});

function createReq(data, onSuccess, dataType, url, type) {
  /*
   * Create Ajax request.
   */
    if (dataType === undefined) {
        dataType = 'json';
    }

    if (url === undefined) {
        url = '/info/manage';
    }

    $.ajax({data: {jsondata: JSON.stringify(data)},
           success: function(json){
                        onAjaxSuccess(json, onSuccess);
                    },
            dataType: dataType,
            url: url,
            type: type
    });
}

function onAjaxSuccess(json, onSuccess) {
    if (json["status"] === "timeout") {
            alert("The session has timed-out, please login again");
    }
    if (onSuccess) {
        // No critical errors; call onSuccess function.
        onSuccess(json);
    }
}

function onSaveClick() {
    /*
     * Handler for the save button. Sends filename and content to the server
     * to be written in the appropriate file
     */
    $("#status_msg").hide();
    createReq({action: "saveContent",
                filename:  $("body").data('openfilename'),
                filecontent: $("#editor").val()},
                function(json){
                    if (json['status'] === "save_success") {
                        $("#status_msg").html("<div class='success'>Save succesful!</div>").fadeIn().delay(3000).fadeOut();
                    }
                    else if ( json['status'] === "error_file_not_writable" ) {
                        $("#status_msg").html("<div class='error'>There was a problem while saving the file. Try again or contact an admin</div>").fadeIn().delay(3000).fadeOut();
                    }
                    else if ( json['status'] === "error_forbidden_path" ) {
                        $("#status_msg").html("<div class='error'>There was a problem while saving the file. Path not allowed</div>").fadeIn().delay(3000).fadeOut();
                    }
            }, 'json', undefined, 'POST');
}

function initFileList() {
    /*
     * Gets the file list for the info space and displays it using FileTree
     * jQuery plugin
     */
    $('#InfoFilesList').fileTree({
            script: '/info/explorer'
        }, function(file) {
                $("body").data('openfilename', file);
                if ( $("#editor").length !== 0 ) {
                    /* There is already an instance of ckeditor, destroy it to
                    prevent an error */
                    $('#editor').ckeditorGet().destroy();
                }
            createReq({action: "listFiles", filename: file}, function(json) {
                if ( json["status"] === "error_file_not_readable" ) {
                    $("#editor_div").html("");
                    $("#status_msg").html("<div class='error'>The file is not editable</div>").fadeIn().delay(3000).fadeOut();
                }
                else if ( json["status"] === "error_forbidden_path" ) {
                    $("#editor_div").html("");
                    $("#status_msg").html("<div class='error'>Path not allowed</div>").fadeIn().delay(3000).fadeOut();
                }
                else {
                    $("#editor_div").html(json["html_content"]);
                    $('#editor').ckeditor({width: 900, height: 500});
                    $("#savebtn").click(onSaveClick);
                }
            }, 'json');
    });
}
