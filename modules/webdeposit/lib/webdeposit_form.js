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


/* Helpers */

function unique_id() {
    return Math.round(new Date().getTime() + (Math.random() * 100));
}

/*
 * Get settings for performing an AJAX request with $.ajax
 * that will POST a JSON object to the given URL
 *
 * @param settings: A hash with the keys: url, data.
 */
function json_options(settings){
    // Perform AJAX request with JSON data.
    return {
        url: settings['url'],
        type: 'POST',
        cache: false,
        data: JSON.stringify(settings['data']),
        contentType: "application/json; charset=utf-8",
        dataType: 'json'
    };
}

/*
 * Serialize a form into JSON
 */
function serialize_object(selector){
    var o = {};
    var a = $(selector).serializeArray();
    $.each(a, function() {
        if (o[this.name] !== undefined) {
            if (!o[this.name].push) {
                o[this.name] = [o[this.name]];
            }
            o[this.name].push(this.value || '');
        } else {
            o[this.name] = this.value || '';
        }
    });
    return o;
}

function getBytesWithUnit(bytes){
	if( isNaN( bytes ) ){
        return '';
    }
	var units = [' bytes', ' KB', ' MB', ' GB'];
	var amountOf2s = Math.floor( Math.log( +bytes )/Math.log(2) );
	if( amountOf2s < 1 ){
		amountOf2s = 0;
	}
	var i = Math.floor( amountOf2s / 10 );
	bytes = +bytes / Math.pow( 2, 10*i );

	// Rounds to 2 decimals places.
    bytes_to_fixed = bytes.toFixed(2);
    if( bytes.toString().length > bytes_to_fixed.toString().length ){
        bytes = bytes_to_fixed;
    }
	return bytes + units[i];
}

/*
 * Initialize PLUpload
 */
function webdeposit_init_plupload(selector, url, delete_url, get_file_url, db_files, dropbox_url) {

    uploader = new plupload.Uploader({
        // General settings
        runtimes : 'html5',
        url : url,
        max_file_size : '460mb',
        chunk_size : '1mb',
        //unique_names : true,
        browse_button : 'pickfiles',
        drop_element : 'field-plupload_file'

        // Specify what files to browse for
        //filters : [
        //    {title : "Image files", extensions : "jpg,gif,png,tif"},
        //    {title : "Compressed files", extensions : "rar,zip,tar,gz"},
        //    {title : "PDF files", extensions : "pdf"}
        //]
    });

    queue_progress = new plupload.QueueProgress();

    uploader.init();

    $(function() {
        if (!jQuery.isEmptyObject(db_files)) {
            $('#file-table').show('slow');

            $.each(db_files, function(i, file) {
                // Simulate a plupload file object
                id = unique_id();
                var plfile = new plupload.File({
                    id: id,
                    name: file.name,
                    size: file.size
                });
                // Dont touch it!
                // For some reason the constructor doesn't initialize
                // the data members
                plfile.id = id;
                plfile.name = file.name;
                plfile.size = file.size;
                // loaded is set to 0 as a temporary fix plupload's  bug in
                // calculating current upload speed. For checking if a file
                // has been uploaded, check file.status
                plfile.loaded = 0; //file.size;
                plfile.status = 5; //status = plupload.DONE
                plfile.percent = 100;
                plfile.unique_filename = file.unique_filename;
                ///////
                uploader.files.push(plfile);
                $('#filelist').append(
                    '<tr id="' + plfile.id + '" style="display:none;">' +
                        '<td><a href="' + get_file_url + "?filename=" + plfile.unique_filename + '">' + plfile.name + '</a></td>' +
                        '<td>' +  getBytesWithUnit(plfile.size) + '</td>' +
                        '<td width="30%"><div class="progress active"><div class="bar" style="width: 100%;"></div></div></td>' +
                        '<td><a id="' + plfile.id + '_rm" class="rmlink"><i class="icon-trash"></i></a></td>' +
                    '</tr>');
                $('#filelist #' + plfile.id).show('fast');
                $("#" + plfile.id + "_rm").on("click", function(event) {
                    uploader.removeFile(plfile);
                });
            });
        }
    });

    $('#uploadfiles').click(function(e) {
        $('#uploadfiles').addClass('disabled');
        $('#stopupload').show();
        uploader.start();
        e.preventDefault();

        $.each(dropbox_files, function(i, file){
            $.ajax({
                type: 'POST',
                url: dropbox_url,
                data: $.param({
                    name: file.name,
                    size: file.size,
                    url: file.url
                })
            }).done(function(data){
                $('#' + file.id + " .progress").removeClass("progress-striped");
                $('#' + file.id + " .bar").css('width', "100%");
                $('#' + file.id + '_link').html('<a href="' + get_file_url + "?filename=" + data + '">' + file.name + '</a>');
            });
        });
        dropbox_files = [];
    });

    $('#stopupload').click(function(d){
        uploader.stop();
        $('#stopupload').hide();
        $('#uploadfiles').removeClass('disabled');
        $.each(uploader.files, function(i, file) {
            if (file.loaded < file.size) {
                $("#" + file.id + "_rm").show();
                //$('#' + file.id + " .bar").css('width', "0%");
            }
        });
        $('#upload_speed').html('');
        uploader.total.reset();
    });

    uploader.bind('FilesRemoved', function(up, files) {
        $.each(files, function(i, file) {
            $('#filelist #' + file.id).hide('fast');
            if (file.status === plupload.DONE) { //If file has been successfully uploaded
                $.ajax({
                    type: "POST",
                    url: delete_url,
                    data: $.param({
                        filename: file.unique_filename
                    })
                });
            }
        });
        if(uploader.files.length === 0) {
            $('#uploadfiles').addClass("disabled");
            $('#file-table').hide('slow');
        }
    });

    uploader.bind('UploadProgress', function(up, file) {
        $('#' + file.id + " .bar").css('width', file.percent + "%");
        upload_speed = getBytesWithUnit(up.total.bytesPerSec) + " per sec";
        console.log("Progress " + file.name + " - " + file.percent);
        $('#upload_speed').html(upload_speed);
        up.total.reset();
    });



    uploader.bind('UploadFile', function(up, file) {
        $('#' + file.id + "_rm").hide();
    });


    uploader.bind('FilesAdded', function(up, files) {
        $('#uploadfiles').removeClass("disabled");
        $('#file-table').show('slow');
        up.total.reset();
        $.each(files, function(i, file) {
            $('#filelist').append(
                '<tr id="' + file.id + '" style="display:none;z-index:-100;">' +
                '<td id="' + file.id + '_link">' + file.name + '</td>' +
                '<td>' + getBytesWithUnit(file.size) + '</td>' +
                '<td width="30%"><div class="progress progress-striped active"><div class="bar" style="width: 0%;"></div></div></td>' +
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

        file.loaded = 0;
        $('#upload_speed').html('');
        $('#uploadfiles').addClass('disabled');
        $('#uploadfiles').show();
        up.total.reset();
    });

    $("#filelist").sortable();
    $("#filelist").disableSelection();
}

/*
 * Initialize save-button
 */
function webdeposit_init_save(url, selector, form_selector) {
    $(selector).click(function(e){
        // Stop propagation of event to prevent form submission
        e.preventDefault();

        webdeposit_set_status(tpl_webdeposit_status_saving, {name: null, value: null});

        $.ajax(
            json_options({url: url, data: serialize_object(form_selector)})
        ).done(function(data) {
            var errors = false;
            // FIXME- get errors from response
            webdeposit_handle_response(data);
            webdeposit_set_status(tpl_webdeposit_status_saved, {name: name, value: null});
            if(errors) {
                webdeposit_set_status(tpl_webdeposit_status_saved_with_errors, {name: name, value: null});
                webdeposit_flash_message({state:'warning', message: tpl_message_errors.render({})});
            } else {
                webdeposit_set_status(tpl_webdeposit_status_saved, {name: name, value: value});
                webdeposit_flash_message({state:'success', message: tpl_message_success.render({})});
            }
        }).fail(function() {
            webdeposit_flash_message({state:'error', message: tpl_message_server_error.render({})});
            check_empty_fields(name);
            webdeposit_set_status(tpl_webdeposit_status_error, {name: name, value: value});
        });

        return false;
    });
}


/*
 * Initialize submit-button
 */
function webdeposit_init_submit(url, selector, form_selector) {
    $(selector).click(function(e){
        e.preventDefault();
        // webdeposit_set_status(tpl_webdeposit_status_saving, {});
        // //emptyForm = checkEmptyFields(null);
        // if (emptyForm[0] == 0){
        //     $('#empty-fields-error').hide('slow');
        //     webdeposit_set_status(tpl_webdeposit_status_saved, {});
        // }
        // else {
        //     $('#empty-fields-error').html("<a class='close' data-dismiss='alert' href='#'>×</a>These fields are required:<ul>" + emptyForm[1] + "</ul>" );
        //     $('#empty-fields-error').show('slow');
        //     webdeposit_set_status(tpl_webdeposit_status_saved_with_errors, {});
        // }
    });
}


/* Error checking */
var errors = 0;
var oldJournal;


/*
 * Handle update of field message box.
 *
 * @return: True if message was set, False if no message was set.
 */
function webdeposit_handle_field_msg(name, data) {
    if(!data) {
        return false;
    }

    state = '';
    if(data.state) {
        state = data.state;
    }

    if(data.messages && data.messages.length !== 0) {
        $('#state-' + name).html(
            tpl_field_message.render({
                name: name,
                state: state,
                messages: data.messages
            })
        );

        ['info','warning','error','success'].map(function(s){
            $("#state-group-" + name).removeClass(s);
            $("#state-" + name).removeClass('alert-'+s);
            if(s == state) {
                $("#state-group-" + name).addClass(state);
                $("#state-" + name).addClass('alert-'+state);
            }
        });

        $('#state-' + name).show('fast');
        return true;
    } else {
        webdeposit_clear_error(name);
        return false;
    }
}

function webdeposit_clear_error(name){
    $('#state-' + name).hide();
    $('#state-' + name).html("");
    ['info','warning','error','success'].map(function(s){
        $("#state-group-" + name).removeClass(s);
        $("#state-" + name).removeClass('alert-'+s);
    });
}

function webdeposit_handle_field_values(name, value) {
    if (name == 'files'){
        $.each(value, function(i, file){
            id = unique_id();

            new_file = {
                id: id,
                name: file.name,
                size: file.size
            };

            $('#filelist').append(
                '<tr id="' + id + '" style="display:none;">' +
                    '<td id="' + id + '_link">' + file.name + '</td>' +
                    '<td>' + getBytesWithUnit(file.size) + '</td>' +
                    '<td width="30%"><div class="progress active"><div class="bar" style="width: 100%;"></div></div></td>' +
                '</tr>');
            $('#filelist #' + id).show('fast');
        });
        $('#file-table').show('slow');
    } else {
        webdeposit_clear_error(name);
        errors--;
        old_value = $('[name=' + name + ']').val();
        if (old_value != value) {
            if (typeof ckeditor === 'undefined')
                $('[name=' + name + ']').val(value);
            else if (ckeditor.name == name)
                    ckeditor.setData(value);
            //webdeposit_handle_new_value(name, value, url);
        }
    }
}

/*
 * Handle server response for multiple fields.
 */
function webdeposit_handle_response(data) {
    if('messages' in data) {
        $.each(data['messages'], webdeposit_handle_field_msg);
    }
    if('values' in data) {
        $.each(data['values'], webdeposit_handle_field_values);
    }
    if('hidden_on' in data) {
        $.each(data['hidden_on'], function(idx, field){
            $('#state-group-'+field).hide("slow");
        });
    }
    if('hidden_off' in data) {
        $.each(data['hidden_off'], function(idx, field){
            $('#state-group-'+field).show("slow");
        });
    }
    if('disabled_on' in data) {
        $.each(data['disabled_on'], function(idx, field){
            $('#'+field).attr('disabled','disabled');
        });
    }
    if('disabled_off' in data) {
        $.each(data['disabled_off'], function(idx, field){
            $('#'+field).removeAttr('disabled');
        });
    }
}

/*
 * Set value of status indicator in form (e.g. saving, saved, ...)
 */
function webdeposit_set_status(tpl, ctx) {
    $('.status-indicator').show();
    $('.status-indicator').html(tpl.render(ctx));
}

function webdeposit_set_loader(selector, tpl, ctx) {
    $(selector).show();
    $(selector).html(tpl.render(ctx));
}

/*
 * Flash a message in the top.
 */
function webdeposit_flash_message(ctx) {
    $('#flash-message').html(tpl_flash_message.render(ctx));
    $('#flash-message').show();
}

function webdeposit_handle_new_value(name, value, url) {
  // sends an ajax request with the data
  $.getJSON(url, {
      name: name,
      attribute: value
  }, function(data){
        webdeposit_handle_field_data(name, value, data, url);
        webdeposit_set_status(tpl_webdeposit_status_saved, {name: name, value: value});
  });
}


/*
 * Save and check field values for errors.
 */
function webdeposit_input_error_check(selector, url) {
    $(selector).change( function() {
        name = this.name;
        value = this.value;

        webdeposit_set_status(tpl_webdeposit_status_saving, {name: name, value: value});

        request_data = {};
        request_data[name] = value;

        $.ajax(
            json_options({url: url, data: request_data})
        ).done(function(data) {
            webdeposit_handle_response(data);
            webdeposit_set_status(tpl_webdeposit_status_saved, {name: name, value: value});
        }).fail(function() {
            check_empty_fields(name);
            webdeposit_set_status(tpl_webdeposit_status_error, {name: name, value: value});
        });

        return false;
    });
}

/*
 * Click form-button
 */
function webdeposit_button_click(selector, url) {
    $(selector).click( function() {
        name = this.name;
        loader_selector = '#' + name + '-loader';

        webdeposit_set_loader(loader_selector, tpl_loader, {name: name});

        request_data = {};
        request_data[name] = true;

        $.ajax(
            json_options({url: url, data: request_data})
        ).done(function(data) {
            webdeposit_handle_response(data);
            webdeposit_set_loader(loader_selector, tpl_loader_success, {name: name});
        }).fail(function() {
            webdeposit_set_loader(loader_selector, tpl_loader_failed, {name: name});
        });

        return false;
    });
}




/*
 * CKEditor
 */

function webdeposit_ckeditor_init(selector, url) {
    CKEDITOR.replace(selector);

    ckeditor = CKEDITOR.instances[selector];
    ckeditor.on('blur',function(event){
        webdeposit_handle_new_value(selector, ckeditor.getData(), url);
    });
}

/********************************************************/
/*
 * Check if required field is empty
 *
 * @param field: Name of field, or null to check all fields.
 */
function check_empty_fields(field) {
    check_fields = [];
    empty_fields = [];

    if (field && $.inArray(field, required_fields)) {
        check_fields = [field];
    } else if (field === undefined) {
        check_fields = required_fields;
    }

    check_fields.map(function(f){
        label = $("label[for='"+f+"']").html() || '';
        value = $('#'+f).val();

        if(value === "" || value === null) {
            webdeposit_handle_field_msg(field, {state: 'error', message: tpl_required_field_message.render({label: label.toString().trim(), value: value})});
            empty_fields.push(f);
        } else {
            webdeposit_handle_field_msg(field, {state: '', message: ''});
        }
    });

    return empty_fields;
}

// function checkEmptyFields(all_fields, field, required_fields) {
//     var emptyFields = "";
//     var empty = 0;
//     $(":text, :file, :checkbox, select, textarea").each(function() {
//       // Run the checks only for fields that are required
//       if ($.inArray(this.name, required_fields) > -1) {
//         if(($(this).val() === "") || ($(this).val() === null)) {
//             emptyFields += "<li>" + $("label[for='"+this.name+"']").html() + "</li>";
//             if ( (all_fields === true) || (field == this.name)) {
//                 $('#error-'+this.name).html($("label[for='"+this.name+"']").html() + " field is required!");
//                 $("#error-group-" + this.name).addClass('error');
//                 $('#error-'+this.name).show('slow');
//             }
//             empty = 1;
//         } else {
//           $('#error-'+this.name).hide('slow');
//         }
//       }
//     });
//     // Return the text only if all fields where requested
//     if ( (empty == 1) && all_fields)
//         return [1, emptyFields];
//     else
//         return [0, emptyFields];
// }

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


var dropbox_files = [];

if (document.getElementById("db-chooser") !== null) {
    document.getElementById("db-chooser").addEventListener("DbxChooserSuccess",
        function(e) {
            $('#file-table').show('slow');
            $.each(e.files, function(i, file){
                id = unique_id();

                dbfile = {
                    id: id,
                    name: file.name,
                    size: file.bytes,
                    url: file.link
                };

                $('#filelist').append(
                    '<tr id="' + id + '" style="display:none;">' +
                        '<td id="' + id + '_link">' + file.name + '</td>' +
                        '<td>' + getBytesWithUnit(file.bytes) + '</td>' +
                        '<td width="30%"><div class="progress active"><div class="bar" style="width: 0%;"></div></div></td>' +
                        '<td><a id="' + id + '_rm" class="rmlink"><i class="icon-trash"></i></a></td>' +
                    '</tr>');
                $('#filelist #' + id).show('fast');
                $('#uploadfiles').removeClass("disabled");
                $('#' + dbfile.id + '_rm').on("click", function(event){
                    $('#' + dbfile.id).hide('fast');
                });

                dropbox_files.push(dbfile);
            });
        }, false);
}


