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


/*
 * Plupload
 */

 function unique_ID(){
    return Math.round(new Date().getTime() + (Math.random() * 100));
 }

function webdeposit_init_plupload(selector, url, delete_url, get_file_url, db_files) {

    uploader = new plupload.Uploader({
        // General settings
        runtimes : 'html5',
        url : url,
        max_file_size : '460mb',
        chunk_size : '1mb',
        //unique_names : true,
        browse_button : 'pickfiles',
        drop_element : 'filebox'

        // Specify what files to browse for
        //filters : [
        //    {title : "Image files", extensions : "jpg,gif,png,tif"},
        //    {title : "Compressed files", extensions : "rar,zip,tar,gz"},
        //    {title : "PDF files", extensions : "pdf"}
        //]
    });

    uploader.init();

    $(function() {
        if (!jQuery.isEmptyObject(db_files)){
            $('#file-table').show('slow');

            $.each(db_files, function(i, file) {
                // Simulate a plupload file object
                id = unique_ID();
                var plfile = new plupload.File({
                    id: id,
                    name: file.name,
                    size: file.size
                });
                // Dont touch it!
                // For some reason the constructor doesn't initialize
                // the data members
                plfile.id = id,
                plfile.name = file.name;
                plfile.size = file.size;
                plfile.loaded = file.size;
                plfile.status = 5;
                plfile.percent = 100;
                plfile.unique_filename = file.unique_filename;
                ///////
                uploader.files.push(plfile);
                $('#filelist').append(
                    '<tr id="' + plfile.id + '" style="display:none;">' +
                        '<td><a href="' + get_file_url + "?filename=" + plfile.unique_filename + '">' + plfile.name + '</a></td>' +
                        '<td>' + plupload.formatSize(plfile.size) + '</td>' +
                        '<td width="30%"><div class="progress active"><div class="bar" style="width: 100%;"></div></div></td>' +
                        '<td><a id="' + plfile.id + '_rm" class="rmlink"><i class="icon-trash"></i></a></td>' +
                    '</tr>');
                $('#filelist #' + plfile.id).show('fast');
                $("#" + plfile.id + "_rm").on("click", function(event){
                    uploader.removeFile(plfile);
                });
            });
        }
    });

    $('#uploadfiles').click(function(e) {
        uploader.start();
        $('#uploadfiles').hide();
        $('#stopupload').show();
        e.preventDefault();
    });

    $('#stopupload').click(function(d){
        uploader.stop();
        $('#stopupload').hide();
        $('#uploadfiles').show();
        $.each(uploader.files, function(i, file) {
            if (file.loaded < file.size){
                $("#" + file.id + "_rm").show();
                $('#' + file.id + " .bar").css('width', "0%");
            }
        });
    });

    uploader.bind('FilesRemoved', function(up, files) {
        $.each(files, function(i, file) {
            $('#filelist #' + file.id).hide('fast');
            if (file.loaded == file.size) {
                $.ajax({
                    type: "POST",
                    url: delete_url,
                    data: $.param({
                        filename: file.unique_filename
                    })
                });
            }
        });
        if(uploader.files.length === 0){
            $('#uploadfiles').addClass("disabled");
            $('#file-table').hide('slow');
        }
    });

    uploader.bind('UploadProgress', function(up, file) {
        $('#' + file.id + " .bar").css('width', file.percent + "%");
        console.log("Progress " + file.name + " - " + file.percent);
    });

    uploader.bind('UploadFile', function(up, file) {
        $('#' + file.id + "_rm").hide();
    });


    uploader.bind('FilesAdded', function(up, files) {
        $('#uploadfiles').removeClass("disabled");
        $('#file-table').show('slow');
        $.each(files, function(i, file) {
            $('#filelist').append(
                '<tr id="' + file.id + '" style="display:none;z-index:-100;">' +
                '<td id="' + file.id + '_link">' + file.name + '</td>' +
                '<td>' + plupload.formatSize(file.size) + '</td>' +
                '<td width="30%"><div class="progress progress-stri´ped active"><div class="bar" style="width: 0%;"></div></div></td>' +
                '<td><a id="' + file.id + '_rm" class="rmlink"><i class="icon-trash"></i></a></td>' +
                '</tr>');
            $('#filelist #' + file.id).show('fast');
            $('#' + file.id + '_rm').on("click", function(event){
                uploader.removeFile(file);
            });
        });
    });

    uploader.bind('FileUploaded', function(up, file, responseObj) {
        console.log("Done " + file.name);
        $('#' + file.id + " .progress").removeClass("progress-striped");
        $('#' + file.id + " .bar").css('width', "100%");
        $('#' + file.id + '_rm').show();
        $('#' + file.id + '_link').html('<a href="' + get_file_url + "?filename=" + responseObj.response + '">' + file.name + '</a>');
        file.unique_filename = responseObj.response;
        if (uploader.total.queued === 0)
            $('#stopupload').hide();

        $('#uploadfiles').addClass('disabled');
        $('#uploadfiles').show();

    });
}


/* Error checking */
var errors = 0;
var oldJournal;


function webdeposit_handle_field_data(name, value, data, url, required_fields) {
    // handles a response from the server for the field
    if (data.error == 1) {
        errorMsg = data.error_message;
        $('#error-' + name).html(errorMsg);
        $('.error-list-' + name).hide('slow');
        $('#error-' + name).show('slow');
        $("#error-group-" + name).addClass('error');
        errors++;
    } else {
        $('#error-' + name).hide('slow');
        $('.error-list-' + name).hide('slow');
        $("#error-group-" + name).removeClass('error');
        if (errors > 0)
            errors--;
        emptyForm = checkEmptyFields(false, name, required_fields);
        if (emptyForm[0] === 0) {
            $('#empty-fields-error').hide('slow');
        }
        else {
            $('#empty-fields-error').html("These fields are required!</br>" + emptyForm[1]);
            $('#empty-fields-error').show();
        }
    }

    dismiss = '<button type="button" class="close" data-dismiss="alert">&times;</button>';

    if (data.success == 1) {
        success = '<div class="alert alert-success help-inline" id="success-' + name + '" style="display:none;">' +
                  dismiss + data.success_message +
                  '</div>';
        $('#success-' + name).remove();
        $('#field-' + name).append(success);
        $('#success-' + name).show('slow');
    }
    else {
      $('#success-' + name).remove();
    }

    if (data.info == 1) {
        info = '<div class="alert alert-info help-inline" id="info-' + name + '" style="display:none;">' +
               dismiss + data.info_message +
               '</div>';
        $('#info-' + name).remove();
        $('#field-' + name).append(info);
        $('#info-' + name).css('margin-top', '10px');
        $('#info-' + name).css('clear', 'both');
        $('#info-' + name).css('float', 'left');
        $('#info-' + name).show('slow');
    }
    else {
      $('#info-' + name).remove();
    }

    if (data.fields) {
        $.each(data.fields, function(name, value) {
            $('#error-' + name).hide('slow');
            errors--;
            old_value = $('[name=' + name + ']').val();
            if (old_value != value) {
                if (typeof ckeditor === 'undefined')
                    $('[name=' + name + ']').val(value);
                else if (ckeditor.name == name)
                        ckeditor.setData(value);
                webdeposit_handle_new_value(name, value, url, required_fields);
            }
        });
    }
  }

function webdeposit_handle_new_value(name, value, url, required_fields) {
  // sends an ajax request with the data
  $.getJSON(url, {
      name: name,
      attribute: value
  }, function(data){
        webdeposit_handle_field_data(name, value, data, url, required_fields);
  });
}

function webdeposit_input_error_check(selector, url, required_fields) {
  $(selector).change( function() {
        name = this.name;
        value = this.value;
        $.getJSON(url, {
            name: name,
            attribute: value
        }, function(data){
            webdeposit_handle_field_data(name, value, data, url, required_fields);
        });
    return false;
  });
}


/*
 * CKEditor
 */

function webdeposit_ckeditor_init(selector, url, required_fields) {
    CKEDITOR.replace(selector);

    ckeditor = CKEDITOR.instances[selector];
    ckeditor.on('blur',function(event){
        webdeposit_handle_new_value(selector, ckeditor.getData(), url, required_fields);
    });
}

/********************************************************/


function checkEmptyFields(all_fields, field, required_fields) {
    var emptyFields = "";
    var empty = 0;
    $(":text, :file, :checkbox, select, textarea").each(function() {
      // Run the checks only for fields that are required
      if ($.inArray(this.name, required_fields) > -1) {
        if(($(this).val() === "") || ($(this).val() === null)) {
            emptyFields += "- " + $("label[for='"+this.name+"']").html() + "</br>";
            if ( (all_fields === true) || (field == this.name)) {
                $('#error-'+this.name).html($("label[for='"+this.name+"']").html() + " field is required!");
                $('#error-'+this.name).show('slow');
            }
            empty = 1;
        } else {
          $('#error-'+this.name).hide('slow');
        }
      }
    });
    // Return the text only if all fields where requested
    if ( (empty == 1) && all_fields)
        return [1, emptyFields];
    else
        return [0, emptyFields];
}

var autocomplete_request = $.ajax();

function webdeposit_field_autocomplete(selector, url) {

    var source = function(query) {
      $(selector).addClass('ui-autocomplete-loading');
      var typeahead = this;
      autocomplete_request.abort();
      autocomplete_request = $.ajax({
        type: 'GET',
        url: url,
        data: $.param({
          term: query
        })
      }).done(function(data) {
        typeahead.process(data.results);
        $(selector).removeClass('ui-autocomplete-loading');
      }).fail(function(data) {
        typeahead.process([query]);
        $(selector).removeClass('ui-autocomplete-loading');
      });
    };

    // FIXME: typeahead doesn't support a delay option
    //        so for every change an ajax request is
    //        being sent to the server.
    $(selector).typeahead({
      source: source,
      minLength: 5,
      items: 50
    });
}


function webdeposit_check_status(url){
    setInterval(function() {
        $.ajax({
            type: 'GET',
            url: url
        }).done(function(data) {
            if (data.status == 1)
                location.reload();
        });
    }, 10000);
}
