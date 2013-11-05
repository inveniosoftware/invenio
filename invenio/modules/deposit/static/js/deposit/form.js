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


//
// Helpers
//
function unique_id() {
    return Math.round(new Date().getTime() + (Math.random() * 100));
}

/**
 * Get settings for performing an AJAX request with $.ajax
 * that will POST a JSON object to the given URL
 *
 * @param {} settings: A hash with the keys: url, data.
 */
function json_options(settings){
    // Perform AJAX request with JSON data.
    return {
        url: settings.url,
        type: 'POST',
        cache: false,
        data: JSON.stringify(settings.data),
        contentType: "application/json; charset=utf-8",
        dataType: 'json'
    };
}

function serialize_files(selector) {
    var ids, files, result;

    // Extract ids
    ids = $(selector).find('tr[id]').map(function(){ return $(this).attr('id');});
    // Build search dict
    files = {};
    $.each(uploader.files, function(idx, elem){
        files[elem.id] = elem;
    });
    // Build ordered list of server ids.
    result = [];
    $.each(ids, function(idx, id){
        var file = files[id];
        if(file !== undefined && file.status == 5) {
            result.push(file.server_id);
        }
    });
    return result;
}

/**
 * Serialize a form
 */
function serialize_form(selector){
    // Sync CKEditor before serializing
    for(var instance in CKEDITOR.instances){
        var editor = CKEDITOR.instances[instance];
        $('#'+instance).val(editor.getData());
    }
    fields = $(selector).serializeArray();
    fields.push({name: 'files', value: serialize_files('#filelist')});
    return serialize_object(fields);
}

/**
 * Serialize an array of name/value-pairs into a dictionary, taking
 * the name structure into account.
 */
function serialize_object(a){
    var o = {};
    $.each(a, function() {
        var sub_o = o;
        var names = this.name.split("-");

        if(names.indexOf("__last_index__") != -1 ||
           names.indexOf("__index__") != -1 ||
           names.indexOf("__input__") != -1) {
            return;
        }

        for(var i = 0; i < names.length; i++){
            var thisname = names[i];
            var thisint = parseInt(thisname, 10);
            var thiskey = isNaN(thisint) ? thisname : thisint;

            if(i == names.length-1) {
                if (sub_o[thiskey] !== undefined) {
                    if(!sub_o[thiskey].push) {
                        sub_o[thiskey] = [sub_o[thiskey]];
                    }
                    sub_o[thiskey].push(this.value || '');
                } else {
                    sub_o[thiskey] = this.value || '';
                }
            } else {
                var nextname = names[i+1];
                var nextint = parseInt(names[i+1], 10);
                if(sub_o[thiskey] === undefined){
                    if(isNaN(nextint)){
                        sub_o[thiskey] = {};
                    } else {
                        sub_o[thiskey] = [];
                    }
                }
                sub_o = sub_o[thiskey];
            }
        }
    });
    return o;
}

/**
 * jQuery plugin to serialize an DOM element
 */
$.fn.serialize_object = function(){
    var inputs = $(this).find(':input');
    var o = [];
    $.each(inputs, function() {
        if(this.name && !this.disabled && ((this.checked && this.type =='radio') || this.type != 'radio')) {
            o.push( { name: this.name, value: $(this).val() } );
        }
    });
    return serialize_object(o);
};

/**
 * Create a new workflow
 */
function create_deposition(url){
    var uuid;
    $.ajax({
        url: url,
        async: false,
        type: 'POST',
        cache: false
    }).done(function(data) {
        uuid = data;
    }).fail(function() {
        uuid = null;
    });
    return uuid;
}

/**
 */
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

//
// Response handlers
//


/**
 * Handle update of field message box.
 *
 * @return: True if message was set, False if no message was set.
 */
function webdeposit_handle_field_msg(name, data) {
    var has_error = false;

    if(!data) {
        return false;
    }

    var state = '';
    if(data.state) {
        state = data.state;
    }

    if(data.messages && data.messages.length !== 0) {
        // if(!$('#state-' + name)){
        //     alert("Problem");
        // }
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
                if(s == 'error') {
                    has_error = true;
                }
                $("#state-group-" + name).addClass(state);
                $("#state-" + name).addClass('alert-'+state);
            }
        });

        $('#state-' + name).show('fast');
        return has_error;
    } else {
        webdeposit_clear_error(name);
        return has_error;
    }
}

/**
 */
function webdeposit_clear_error(name){
    $('#state-' + name).hide();
    $('#state-' + name).html("");
    ['info','warning','error','success'].map(function(s){
        $("#state-group-" + name).removeClass(s);
        $("#state-" + name).removeClass('alert-'+s);
    });
}

/**
 * Update the value of a field to a new one.
 */
function webdeposit_handle_field_values(name, value) {
    if (name == 'files'){
        $.each(value, function(i, file){
            id = unique_id();

            new_file = {
                id: id,
                name: file.name,
                size: file.size
            };

            $('#filelist').append(tpl_file_entry.render({
                id: id,
                filename: file.name,
                filesize: getBytesWithUnit(file.size)
            }));
            $('#filelist #' + id).show('fast');
        });
        $('#file-table').show('fast');
    } else {
        webdeposit_clear_error(name);
        has_ckeditor = $('[name=' + name + ']').data('ckeditor');
        if( has_ckeditor === 1) {
            if(CKEDITOR.instances[name].getData(value) != value) {
                CKEDITOR.instances[name].setData(value);
            }
        } else {
            if($('[name=' + name + ']').val() != value) {
                $('[name=' + name + ']').val(value);
            }
        }
    }
}

/**
 * Handle server response for multiple fields.
 */
function webdeposit_handle_response(data) {
    var errors = 0;

    if('messages' in data) {
        $.each(data.messages, function(name, data) {
            if(webdeposit_handle_field_msg(name, data)){
                errors++;
            }
        });
    }
    if('values' in data) {
        $.each(data.values, webdeposit_handle_field_values);
    }
    if('hidden_on' in data) {
        $.each(data.hidden_on, function(idx, field){
            $('#state-group-'+field).hide("slow");
        });
    }
    if('hidden_off' in data) {
        $.each(data.hidden_off, function(idx, field){
            $('#state-group-'+field).show("slow");
        });
    }
    if('disabled_on' in data) {
        $.each(data.disabled_on, function(idx, field){
            $('#'+field).attr('disabled','disabled');
        });
    }
    if('disabled_off' in data) {
        $.each(data.disabled_off, function(idx, field){
            $('#'+field).removeAttr('disabled');
        });
    }

    return errors;
}

/**
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

/**
 * Flash a message in the top.
 */
function webdeposit_flash_message(ctx) {
    $('#flash-message').html(tpl_flash_message.render(ctx));
    $('#flash-message').show('fast');
}

/**
 * Save field value value
 */
function webdeposit_save_field(url, name, value) {
    request_data = {};
    request_data[name] = value;
    webdeposit_save_data(url, request_data);
}
/**
 * Save field value value
 */
function webdeposit_save_data(url, request_data, flash_message, success_callback, failure_callback) {
    loader_selector = '#' + name + '-loader';

    if(flash_message === undefined){
        flash_message = false;
    }

    webdeposit_set_status(tpl_webdeposit_status_saving, request_data);
    webdeposit_set_loader(loader_selector, tpl_loader, request_data);

    $.ajax(
        json_options({url: url, data: request_data})
    ).done(function(data) {
        var errors = webdeposit_handle_response(data);
        webdeposit_set_loader(loader_selector, tpl_loader_success, request_data);
        if(errors) {
            webdeposit_set_status(tpl_webdeposit_status_saved_with_errors, request_data);
            if(flash_message) {
                webdeposit_flash_message({state:'warning', message: tpl_message_errors.render({})});
            }
            if(failure_callback !== undefined){
                failure_callback();
            }
        } else {
            webdeposit_set_status(tpl_webdeposit_status_saved, request_data);
            if(flash_message) {
                webdeposit_flash_message({state:'success', message: tpl_message_success.render({})});
            }
            if(success_callback !== undefined){
                success_callback();
            }
        }

    }).fail(function() {
        webdeposit_set_status(tpl_webdeposit_status_error, request_data);
        webdeposit_set_loader(loader_selector, tpl_loader_success, request_data);
    });
}

/**
 */
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


/**
 * Initialize PLUpload
 */
function webdeposit_init_plupload(max_size, selector, save_url, url, delete_url, get_file_url, db_files, dropbox_url, uuid, newdep_url, continue_url) {
    var had_error = false;
    uploader = new plupload.Uploader({
        // General settings
        runtimes : 'html5',
        url : url,
        max_file_size : max_size,
        chunk_size : '10mb',
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

    function init_uuid(){
        if(uuid === null){
            uuid = create_deposition(newdep_url);
            url = url.replace("__UUID__", uuid);
            uploader.settings.url = url.replace("__UUID__", uuid);
            delete_url = delete_url.replace("__UUID__", uuid);
            get_file_url = get_file_url.replace("__UUID__", uuid);
            dropbox_url = dropbox_url.replace("__UUID__", uuid);
            continue_url = continue_url.replace("__UUID__", uuid);
        }
    }

    queue_progress = new plupload.QueueProgress();

    uploader.init();

    function fake_file(file){
        var plfile = new plupload.File({
            id: file.id,
            name: file.name,
            size: file.size
        });
        // Dont touch it!
        // For some reason the constructor doesn't initialize
        // the data members
        plfile.id = file.id;
        plfile.server_id = file.server_id || file.id;
        plfile.name = file.name;
        plfile.size = file.size;
        // loaded is set to 0 as a temporary fix plupload's bug in
        // calculating current upload speed. For checking if a file
        // has been uploaded, check file.status
        plfile.loaded = 0; //file.size;
        plfile.status = 5; //status = plupload.DONE
        plfile.percent = 100;
        return plfile;
    }

    $(function() {
        if (!jQuery.isEmptyObject(db_files)) {
            $('#file-table').show('slow');

            $.each(db_files, function(i, file) {
                // Simulate a plupload file object
                var plfile = fake_file(file);

                uploader.files.push(plfile);
                $('#filelist').append(tpl_file_entry.render({
                    id: plfile.id,
                    filename: plfile.name,
                    filesize: getBytesWithUnit(plfile.size),
                    download_url: get_file_url + "?file_id=" + plfile.id,
                    removeable: true,
                    completed: true,
                }));
                $('#filelist #' + plfile.id).show('fast');
                $("#" + plfile.id + " .rmlink").on("click", function(event) {
                    uploader.removeFile(plfile);
                });
            });
        }
    });

    function init_button_states(){
        $('#uploadfiles').addClass("disabled");
        $('#stopupload').hide();
        $('#uploadfiles').show();
        $('#upload_speed').html('');
        had_error = false;
    }

    function redirect(){
        if(continue_url){
            if( window.location != continue_url ){
                window.location = continue_url;
            }
        }
    }

    function upload_dropbox_finished() {
        dropbox_files = [];
        redirect();
        init_button_states();
    }

    function upload_dropbox_file(i) {
        var file = dropbox_files[i];

        $('#' + file.id + " .progress").hide();
        $('#' + file.id + " .bar").css('width', "100%");
        $('#' + file.id + " .progress").addClass("progress-striped");
        $('#' + file.id + " .progress").show();

        $.ajax({
            type: 'POST',
            url: dropbox_url,
            data: $.param({
                name: file.name,
                size: file.size,
                url: file.url
            }),
            dataType: "json"
        }).done(function(data){
            file.server_id = data['id'];

            $('#' + file.id + " .progress").removeClass("progress-striped");
            $('#' + file.id + " .progress").hide();
            $('#' + file.id + " .bar").css('width', "100%");
            $('#' + file.id + '_link').html(tpl_file_link.render({
                filename: file.name,
                download_url: get_file_url + "?file_id=" + data['id']
            }));

            var plfile = fake_file(file);
            uploader.files.push(plfile);

            i++;
            if(i < dropbox_files.length){
                upload_dropbox_file(i);
            } else {
                upload_dropbox_finished();
            }
        });
    }

    function start_dropbox_upload() {
        init_uuid();

        if(dropbox_files.length > 0) {
            upload_dropbox_file(0);
        } else {
            init_button_states();
        }
    }

    $('#uploadfiles').click(function(e) {
        e.preventDefault();

        $('#uploadfiles').addClass('disabled');
        $('#uploadfiles').hide();
        $('#stopupload').show();

        if(uploader.files.length > 0){
            uploader.start();
        } else if (dropbox_files.length > 0) {
            start_dropbox_upload();
        }
    });

    $('#stopupload').click(function(d){
        uploader.stop();
        $('#stopupload').hide();
        $('#uploadfiles').show();
        $('#uploadfiles').removeClass('disabled');
        $.each(uploader.files, function(i, file) {
            if (file.loaded < file.size) {
                $("#" + file.id + " .rmlink").show();
                //$('#' + file.id + " .bar").css('width', "0%");
            }
        });
        $('#upload_speed').html('');
        uploader.total.reset();
    });

    uploader.bind('FilesRemoved', function(up, files) {
        $.each(files, function(i, file) {
            $('#filelist #' + file.id).hide('fast', function(){
                $('#filelist #' + file.id).remove();
                if($('#filelist').children().length === 0){
                    $('#uploadfiles').addClass("disabled");
                }
            });
            if (file.status === plupload.DONE) { //If file has been successfully uploaded
                $.ajax({
                    type: "POST",
                    url: delete_url,
                    data: $.param({
                        file_id: file.id
                    })
                });
            }

        });
    });

    uploader.bind('UploadProgress', function(up, file) {
        $('#' + file.id + " .bar").css('width', file.percent + "%");
        upload_speed = getBytesWithUnit(up.total.bytesPerSec) + " per sec";
        console.log("Progress " + file.name + " - " + file.percent);
        $('#upload_speed').html(upload_speed);
        up.total.reset();
    });

    uploader.bind('BeforeUpload', function(up, file) {
        init_uuid();
    });

    uploader.bind('UploadFile', function(up, file) {
        $('#' + file.id + " .rmlink").hide();
    });

    uploader.bind('FilesAdded', function(up, files) {
        $(selector).show();
        $('#uploadfiles').removeClass("disabled");
        $('#file-table').show('slow');
        up.total.reset();
        $.each(files, function(i, file) {
            $('#filelist').append(tpl_file_entry.render({
                    id: file.id,
                    filename: file.name,
                    filesize: getBytesWithUnit(file.size),
                    removeable: true,
                    progress: 0
            }));
            $('#filelist #' + file.id).show('fast');
            $('#' + file.id + ' .rmlink').on("click", function(event){
                uploader.removeFile(file);
            });
        });
    });

    uploader.bind('FileUploaded', function(up, file, responseObj) {
        try{
            res_data = JSON.parse(responseObj.response);
        } catch (err) {}

        file.server_id = res_data.id;

        $('#' + file.id + " .progress").removeClass("progress-striped");
        $('#' + file.id + " .bar").css('width', "100%");
        $('#' + file.id + ' .rmlink').show();
        $('#' + file.id + " .progress").hide();
        $('#' + file.id + '_link').html(tpl_file_link.render({
            filename: file.name,
            download_url: get_file_url + "?file_id=" + res_data['id']
        }));
        if (uploader.total.queued === 0)
            $('#stopupload').hide();

        file.loaded = 0;
        $('#upload_speed').html('');
        up.total.reset();
    });

    function error_message(err) {
        var error_messages = {}, message, http_errors;

        error_messages[plupload.FILE_EXTENSION_ERROR] = "the file extensions is not allowed.";
        error_messages[plupload.FILE_SIZE_ERROR] = "the file is too big.";
        error_messages[plupload.GENERIC_ERROR] = "an unknown error.";
        error_messages[plupload.IO_ERROR] = "problems reading the file on disk.";
        error_messages[plupload.SECURITY_ERROR] = "problems reading the file on disk.";

        message = error_messages[err.code];

        if (message !== undefined) {
            return message;
        }

        if (err.code == plupload.HTTP_ERROR) {
            http_errors = {};
            http_errors[401] = "an authentication error. Please login first.";
            http_errors[403] = "lack of permissions.";
            http_errors[404] = "a server error.";
            http_errors[500] = "a server error.";

            message = http_errors[err.status];

            if (message !== undefined) {
               return message;
            }
        }

        return "an unknown error occurred";
    }

    uploader.bind('Error', function(up, err) {
        had_error = true;
        var message = error_message(err);
        $('#upload-errors').hide();
        if (err.file){
            $('#' + err.file.id + " .progress").removeClass("progress-striped").addClass("progress-danger");
            $('#upload-errors').append('<div class="alert alert-danger"><strong>Error:</strong> Could not upload ' + err.file.name +" due to " + message + "</div>");
        } else {
            $('#upload-errors').append('<div class="alert alert-danger"><strong>Error:</strong> ' + message + "</div>");
        }
        $('#upload-errors').show('fast');
        $('#uploadfiles').addClass("disabled");
        $('#stopupload').hide();
        $('#uploadfiles').show();
        up.refresh(); // Reposition Flash/Silverlight
    });

    uploader.bind('UploadComplete', function(up, files) {
        if(dropbox_files.length > 0 && !had_error) {
            start_dropbox_upload();
        } else {
            if(!had_error) {
                redirect();
            }
            init_button_states();
        }
    });

    $("#filelist").sortable({
        forcePlaceholderSize: true,
        forceHelperSizeType: true,
        handle: ".sortlink",
        start: function(event, ui) {
            $(ui.placeholder).show();
            $(ui.placeholder).html("<td></td><td></td><td></td><td></td>");
            $(ui.placeholder).css("visibility", "");
            header_ths = $("#file-table thead th");
            item_tds = $(ui.helper).find("td");
            placeholder_tds = $(ui.placeholder).find("td");
            for(var i = 0; i < header_ths.length; i++){
                $(item_tds[i]).width($(header_ths[i]).width());
                $(placeholder_tds[i]).width($(header_ths[i]).width());
            }
        },
        update: function(event, ui){
            if(save_url) {
                webdeposit_save_field(save_url, 'files', serialize_files("#filelist"));
            }
        }
    });
    $("#filelist").disableSelection();
}

/**
 * Initialize save-button
 */
function webdeposit_init_save(url, selector, form_selector) {
    $(selector).click(function(e){
        e.preventDefault();
        webdeposit_save_data(url, serialize_form(form_selector), true);
        return false;
    });
}


/**
 * Initialize submit-button
 */
function webdeposit_init_submit(url, selector, form_selector, dialog) {
    $(selector).click(function(e){
        e.preventDefault();
        webdeposit_submit(url, form_selector, dialog);
    });
}

function webdeposit_submit(url, form_selector, dialog){
    if(dialog !== undefined){
        $(dialog).modal({
            backdrop: false,
            keyboard: false,
            show: true,
        });
    }
    webdeposit_save_data(
         url,
         serialize_form(form_selector),
         true,
         function success_callback() {
            window.location.reload();
         },
         function failure_callback() {
            if(dialog !== undefined){
                $(dialog).modal('hide');
            }
         }
    );

}

/**
 * Initialize dynamic field lists
 */
 var field_lists = {};
 function webdeposit_init_field_lists(selector, url, autocomplete_selector, url_autocomplete) {
    function serialize_and_save(options) {
        // Save list on remove element, sorting and paste of list
        data = $('#'+options.prefix).serialize_object();
        if($.isEmptyObject(data)){
            data[options.prefix] = [];
        }
        webdeposit_save_data(url, data);

    }

    function install_handler(options, element) {
        // Install save handler when adding new elements
        $(element).find(":input").change( function() {
            webdeposit_save_field(url, this.name, this.value);
        });
        $(element).find(autocomplete_selector).each(function (){
            webdeposit_init_autocomplete(this, url, url_autocomplete);
        });
    }

    var opts = {
        updated: serialize_and_save,
        removed: serialize_and_save,
        added: install_handler,
        pasted: serialize_and_save,
    };

    $(selector).each(function(){
        field_lists[$(this).attr('id')] = {
            append_element: $(this).fieldlist(opts)
        };
    });
}


/**
 * Save and check field values for errors.
 */
function webdeposit_init_inputs(selector, url) {
    $(selector).change( function() {
        if(this.name.indexOf('__input__') == -1){
            webdeposit_save_field(url, this.name, this.value);
        }
    });
}

/**
 * Click form-button
 */
function webdeposit_init_buttons(selector, url) {
    $(selector).click( function() {
        webdeposit_save_field(url, this.name, true);
        return false;
    });
}


/**
 * CKEditor initialization
 */
function webdeposit_init_ckeditor(selector, url) {
    $(selector).each(function(){
        var options = $(this).data('ckeditorConfig');
        if(options ===  undefined){
            CKEDITOR.replace(this);
        } else {
            CKEDITOR.replace(this, options);
        }
        ckeditor = CKEDITOR.instances[$(this).attr('name')];
        ckeditor.on('blur',function(e){
            webdeposit_save_field(url, e.editor.name, e.editor.getData());
        });
    });
}


/**
 * Autocomplete initialization
 */
function webdeposit_init_autocomplete(selector, save_url, url_template, handle_selection) {
    $(selector).each(function(){
        var item = this;
        var url = url_template.replace("__FIELDNAME__", item.name);

        if(handle_selection === undefined){
            handle_selection = webdeposit_typeahead_selection;
        }

        if($(item).attr('type') != 'hidden') {
            try {
                webdeposit_init_bootstrap_typeahead(item, url, save_url, handle_selection);
            } catch (err) {
                webdeposit_init_typeaheadjs(item, url, save_url, handle_selection);
            }
        }
    });
}

/**
 * Bootstrap standard typeahead
 */
function webdeposit_init_bootstrap_typeahead(item, url, save_url, handle_selection) {
    var autocomplete_request = null;

    function source(query, process) {
        $(item).addClass('ui-autocomplete-loading');
        var typeahead = this;

        if(autocomplete_request !== null){
            autocomplete_request.abort();
        }
        autocomplete_request = $.ajax({
            type: 'GET',
            url: url,
            data: $.param({term: query})
        }).done(function(data) {
            process(data);
            $(item).removeClass('ui-autocomplete-loading');
        }).fail(function(data) {
            process([query]);
            $(item).removeClass('ui-autocomplete-loading');
        });
    }

    function updater(datum) {
        handle_selection(save_url, this.$element, datum, $(this.$element).attr('name'));
    }

    $(item).typeahead({
        source: source,
        minLength: 5,
        items: 50,
        updater: updater
    });
}

/**
 * Twitter typeahead.js support for autocompletion
 */
function webdeposit_init_typeaheadjs(item, url, save_url, handle_selection) {
    $(item).typeahead({
        name: item.name,
        remote: url + "?term=%QUERY",
    });
    $(item).on('typeahead:selected', function(e, datum, name){
        handle_selection(save_url, item, datum, name);
    });
}

/**
 * Handle selection of an autocomplete option
 */
function webdeposit_typeahead_selection(save_url, item, datum, name) {
    if(typeof datum == 'string') {
        var value = datum;
        datum = {value: value, fields: {}};
        datum.fields = value;
    }
    if(datum.fields !== undefined) {
        if(field_lists !== undefined){
            var input_index = '__input__';
            var item_id = $(item).attr('id');
            var offset = item_id.indexOf(input_index);
            var field_list_name = item_id.slice(0,offset-1);
            if(field_lists[field_list_name] !== undefined){
                field_lists[field_list_name].append_element(datum.fields, input_index);
                // Clear typeahead field
                try {
                   $(item).typeahead('setQuery', "");
                } catch (error) {} //Suppress error
                $(item).val("");
                // Save list
                data = $('#'+field_list_name).serialize_object();
                if($.isEmptyObject(data)){
                    data[options.prefix] = [];
                }
                webdeposit_save_data(save_url, data);
                return;
            }
        }

        for(var field_name in datum.fields) {
            webdeposit_handle_field_values(field_name, datum.fields[field_name]);
            if(field_name == name) {
                try {
                   $(item).typeahead('setQuery', datum.fields[field_name]);
                } catch (error) {} //Suppress error
            }
        }
        //FIXME: sends wrong field names
        webdeposit_save_data(save_url, datum.fields);
    }
}


var dropbox_files = [];

if (document.getElementById("db-chooser") !== null) {
    document.getElementById("db-chooser").addEventListener("DbxChooserSuccess",
        function(e) {
            $('.pluploader').show();
            $('#file-table').show('fast');
            $.each(e.files, function(i, file){
                id = unique_id();

                dbfile = {
                    id: id,
                    name: file.name,
                    size: file.bytes,
                    url: file.link
                };

                $('#filelist').append(tpl_file_entry.render({
                    id: dbfile.id,
                    filename: file.name,
                    filesize: getBytesWithUnit(file.bytes),
                    removeable: true
                }));
                $('#filelist #' + id).show('fast');
                $('#uploadfiles').removeClass("disabled");
                $('#' + dbfile.id + ' .rmlink').on("click", function(event){
                    $('#' + dbfile.id).hide('fast', function() {
                        $('#' + dbfile.id).remove();
                        if($('#filelist').children().length === 0){
                           $('#uploadfiles').addClass("disabled");
                        }
                    });
                    dropbox_files = dropbox_files.filter(function(element){
                        return element.id != dbfile.id;
                    });
                });

                dropbox_files.push(dbfile);
            });
        }, false);
}



/**
 * Split paste text into multiple fields and elements.
 */
function paste_newline_splitter(field, data){
    return data.split("\n").filter(function (item, idx, array){
        return item.trim() !== "";
    }).map(function (value){
        r = {};
        r[field] = value.trim();
        return r;
    });
}


/**
 *
 */
$.fn.fieldlist = function(opts) {
    var options = $.extend({}, $.fn.fieldlist.defaults, opts);
    if (options.prefix === null) {
        options.prefix = this.attr('id');
    }
    var template = this.find('.' + options.empty_cssclass);
    var last_index = $("#" + options.prefix + options.sep +  options.last_index);
    var field_regex = new RegExp("(" + options.prefix + options.sep + "(\\d+|" + options.index_suffix + "))"+ options.sep +"(.+)");
    // Get template name from options or the empty elements data attribute
    var tag_template = Hogan.compile($(this).data('tagTemplate') || '');

    /**
     * Get next index
     */
    var get_next_index = function(){
        return parseInt(last_index.val(), 10) + 1;
    };

    /**
     * Set value of last index
     */
    var set_last_index = function(idx){
        return last_index.val(idx);
    };

    /**
     * Update attributes in a single tag
     */
    var update_attr_index = function(tag, idx) {
        var id_regex = new RegExp("(" + options.prefix + options.sep + "(\\d+|" + options.index_suffix + "))");
        var new_id = options.prefix + options.sep + idx;
        ['for', 'id', 'name'].forEach(function(attr_name){
            if($(tag).attr(attr_name)){
               $(tag).attr(attr_name, $(tag).attr(attr_name).replace(id_regex, new_id));
            }
        });
    };

    /**
     * Update index in attributes for a single element (i.e all tags inside
     * element)
     */
    var update_element_index = function(element, idx) {
        update_attr_index(element, idx);
        $(element).find('*').each(function(){
            update_attr_index(this, idx);
        });
    };

    /**
     * Update indexes of all elements
     */
    var update_elements_indexes = function(){
        // Update elements indexes of all other elements
        var all_elements = $('#' + options.prefix + " ." + options.element_css_class);
        var num_elements = all_elements.length;
        for (var i=0; i<num_elements; i++) {
            update_element_index(all_elements[i], i);
        }
        set_last_index(num_elements-1);
    };

    /**
     * Update values of fields for an element
     */
    var update_element_values = function (root, data, field_prefix_index, selector_prefix){
        var field_prefix, newdata;

        if(selector_prefix ===undefined){
            selector_prefix = '#'+options.prefix+options.sep+options.index_suffix+options.sep;
        }

        if(field_prefix_index === undefined){
            field_prefix = options.prefix+options.sep+options.index_suffix+options.sep;
        } else {
            field_prefix = options.prefix+options.sep+field_prefix_index+options.sep;
        }
        if(root === null) {
            root = $(document);
        }

        //Update field values if data exists
        if(data !== null){
            // Remove prefix from field name
            newdata = {};
            if (typeof data == 'object'){
                for(var field in data) {
                    if(field.indexOf(field_prefix) === 0){
                        newdata[field.slice(field_prefix.length)] = data[field];
                    } else {
                        newdata[field] = data[field];
                    }
                }
                // Update value for each field.
                $.each(newdata, function(field, value){
                    var input = root.find(selector_prefix+field);
                    if(input.length !== 0) {
                        // Keep old value
                        if(input.is(":focus")){
                            console.log(selector_prefix+field + " has focus");
                        }
                        input.val(input.val()+value);
                    }
                });
            } else {
                newdata['value'] = data;
                var input = root.find('#'+options.prefix+options.sep+options.index_suffix);
                if(input.length !== 0) {
                    // Keep old value
                    input.val(input.val()+data);
                }
            }

            root.find("."+options.tag_title_cssclass).html(
                tag_template.render(newdata)
            );
        }
    };

    var get_field_name = function(name_or_id) {
        result = field_regex.exec(name_or_id);
        if(result !== null){
            return result[3];
        }
        return null;
    };

    var get_field_prefix = function(name_or_id) {
        result = field_regex.exec(name_or_id);
        if(result !== null){
            return result[1];
        }
        return null;
    };

    /**
     * Handler for remove element events
     */
    var remove_element = function(e){
        //
        // Delete action
        //
        e.preventDefault();

        // Find and remove element
        var old_element = $(this).parents("." + options.element_css_class);
        old_element.hide('fast', function(){
            // Give hide animation time to complete
            old_element.remove();
            update_elements_indexes();

            // Callback
            if (options.removed) {
                options.removed(options, old_element);
            }
        });
    };

    /**
     * Handler for sort element events
     */
    var sort_element = function (e, ui) {
        update_elements_indexes();
        // Callback
        if (options.updated) {
            options.updated(options, ui.item);
        }
    };

    /**
     * Handler for add new element events
     */
    var append_element = function (data, field_prefix_index){
        //
        // Append action
        //
        var new_element = template.clone();
        var next_index = get_next_index();
        // Remove class
        new_element.removeClass(options.empty_cssclass);
        new_element.addClass(options.element_css_class);
        new_element.addClass("input-group");
        // Pre-populate field values
        update_element_values(new_element, data, field_prefix_index);
        // Update ids
        update_element_index(new_element, next_index);
        // Insert before template element
        new_element.hide();
        new_element.insertBefore($(template));
        new_element.show('fast');
        // Update last_index
        set_last_index(next_index);
        // Add delete button handler
        new_element.find('.' + options.remove_cssclass).click(remove_element);
        // Add paste handler for some fields
        if( options.on_paste !== null && options.on_paste_elements !== null) {
            new_element.find(options.on_paste_elements).on('paste', on_paste);
        }
        // Callback
        if (options.added) {
            options.added(options, new_element);
        }
    };

    /**
     * On paste event handler, wrapping the user-defined paste handler to
     * for ease of use.
     */
    var on_paste = function (e){
        var element = $(e.target);
        var root_element = element.parents("." + options.element_css_class);
        var data = e.originalEvent.clipboardData.getData("text/plain");
        var field_name = get_field_name(element.attr("id"));
        var prefix = "#" + get_field_prefix(element.attr("id")) + options.sep;

        if(options.on_paste !== null && data !== null) {
            if(options.on_paste(root_element, element, prefix, field_name, data, append_element)) {
                e.preventDefault();
            }
        }
    };

    /**
     * Factory method for creating on paste event handlers. Allow handlers to
     * only care about splitting string into data elements.
     */
    var create_paste_handler = function (splitter){
        var on_paste_handler = function(root_element, element, selector_prefix, field, clipboard_data, append_element){
            var elements_values = splitter(field, clipboard_data);
            if(elements_values.length > 0) {
                $.each(elements_values, function(idx, clipboard_data){
                    if(idx === 0) {
                        update_element_values(root_element, clipboard_data, undefined, selector_prefix);
                    } else {
                        append_element(clipboard_data);
                    }
                });
                // Callback
                if (options.pasted) {
                    options.pasted(options);
                }
                return true;
            } else {
                return false;
            }
        };

        return on_paste_handler;
    };

    var create = function(item){
        // Hook add/remove buttons on already rendered elements
        $('#' + options.prefix + " ." + options.element_css_class + " ." + options.remove_cssclass).click(remove_element);
        $('#' + options.prefix + " ." + options.add_cssclass).click(append_element);

        // Hook for detecting on paste events
        if( options.on_paste !== null && options.on_paste_elements !== null) {
            options.on_paste = create_paste_handler(options.on_paste);
            $('#' + options.prefix + " " + options.on_paste_elements).on('paste', on_paste);
        }

        // Make list sortable
        if(options.sortable){
            var sortable_options = {
                items: "." + options.element_css_class,
                update: sort_element,
            };

            if($(item).find("."+options.sort_cssclass).length !== 0){
                sortable_options.handle = "." + options.sort_cssclass;
            }

            $(item).sortable(sortable_options);
        }

        return item;
    };

    create(this);

    return append_element;
};

/** Field list plugin defaults */
$.fn.fieldlist.defaults = {
    prefix: null,
    sep: '-',
    last_index: "__last_index__",
    index_suffix: "__index__",
    empty_cssclass: "empty-element",
    element_css_class: "field-list-element",
    remove_cssclass: "remove-element",
    add_cssclass: "add-element",
    sort_cssclass: "sort-element",
    tag_title_cssclass: "tag-title",
    added: null,
    removed: null,
    updated: null,
    pasted: null,
    on_paste_elements: "input",
    on_paste: null, //paste_newline_splitter,
    sortable: true,
    js_template: null,
};
