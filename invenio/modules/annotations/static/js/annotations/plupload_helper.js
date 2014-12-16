/**
This file is part of Invenio.
Copyright (C) 2014 CERN.

Invenio is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License as
published by the Free Software Foundation; either version 2 of the
License, or (at your option) any later version.

Invenio is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License
along with Invenio; if not, write to the Free Software Foundation, Inc.,
59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
**/

'use strict';

/* global plupload */
/* global Hogan */

/* exported PLUPLOAD_HELPER */

var PLUPLOAD_HELPER = (function($) {

    var T = 'plupload';

    var _UPLOADER;

    var tpl_file_entry = Hogan.compile('<tr id="{{id}}" class="ahide">' +
        '<td id="{{id}}_link">{{#download_url}}<a href="{{download_url}}">{{filename}}</a>{{/download_url}}{{^download_url}}{{filename}}{{/download_url}}</td>' +
        '<td>{{filesize}}</td>' +
        '<td width="30%">{{^completed}}<div class="progress{{#striped}} progress-striped{{/striped}} active"><div class="bar" style="width: {{progress}}%;">{{/completed}}</div></div></td>' +
        '<td><a id="{{id_sort}}" class="sortlink text-muted" rel="tooltip" title="Re-order files"><i class="glyphicon glyphicon-reorder"></i></a>&nbsp;{{#removeable}}<a class="rmlink" rel="tooltip" title="Delete file"><i class="glyphicon glyphicon-trash"></i></a>{{/removeable}}</td>' +
        '</tr>');

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
        var bytes_to_fixed = bytes.toFixed(2);
        if( bytes.toString().length > bytes_to_fixed.toString().length ){
            bytes = bytes_to_fixed;
        }
        return bytes + units[i];
    }

    function _init() {
        var selector = '.pluploader';


        var had_error = false;
        _UPLOADER = new plupload.Uploader({
            runtimes : 'html5',
            url : '/annotation/attach',
            max_file_size : '10mb',
            chunk_size : '10mb',
            browse_button : 'pickfiles',
            drop_element : 'filebox' //FIXME filebox id was removed from Invenio
        });

        // var queue_progress = new plupload.QueueProgress();

        _UPLOADER.init();

        _UPLOADER.bind('BeforeUpload', function(instance, file) {
            L.i(T, 'BeforeUpload', {instance:instance, file:file});
        });

        // function fake_file(file){
        //     var plfile = new plupload.File({
        //         id: file.id,
        //         name: file.name,
        //         size: file.size
        //     });
        //     // Dont touch it!
        //     // For some reason the constructor doesn't initialize
        //     // the data members
        //     plfile.id = file.id;
        //     plfile.server_id = file.server_id || file.id;
        //     plfile.name = file.name;
        //     plfile.size = file.size;
        //     // loaded is set to 0 as a temporary fix plupload's bug in
        //     // calculating current upload speed. For checking if a file
        //     // has been uploaded, check file.status
        //     plfile.loaded = 0; //file.size;
        //     plfile.status = 5; //status = plupload.DONE
        //     plfile.percent = 100;
        //     return plfile;
        // }

        // $(function() {
        //     if (!$.isEmptyObject(db_files)) {
        //         $('#file-table').show('slow');

        //         $.each(db_files, function(i, file) {
        //             // Simulate a plupload file object
        //             var plfile = fake_file(file);

        //             _UPLOADER.files.push(plfile);
        //             $('#filelist').append(tpl_file_entry.render({
        //                 id: plfile.id,
        //                 filename: plfile.name,
        //                 filesize: getBytesWithUnit(plfile.size),
        //                 download_url: get_file_url + "?file_id=" + plfile.id,
        //                 removeable: true,
        //                 completed: true,
        //             }));
        //             $('#filelist #' + plfile.id).show('fast');
        //             $("#" + plfile.id + " .rmlink").on("click", function(event) {
        //                 _UPLOADER.removeFile(plfile);
        //             });
        //         });
        //     }
        // });

        function init_button_states(){
            $('#uploadfiles').addClass('disabled');
            $('#stopupload').hide();
            $('#uploadfiles').show();
            $('#upload_speed').html('');
            had_error = false;
        }

        // function redirect(){
        //     if(continue_url){
        //         if( window.location != continue_url ){
        //             window.location = continue_url;
        //         }
        //     }
        // }

        $('#uploadfiles').click(function(e) {
            e.preventDefault();

            $('#uploadfiles').addClass('disabled');
            $('#uploadfiles').hide();
            $('#stopupload').show();

            if(_UPLOADER.files.length > 0){
                _UPLOADER.start();
            }
            // else if (dropbox_files.length > 0) {
            //     start_dropbox_upload();
            // }
        });

        $('#stopupload').click(function(){
            _UPLOADER.stop();
            $('#stopupload').hide();
            $('#uploadfiles').show();
            $('#uploadfiles').removeClass('disabled');
            $.each(_UPLOADER.files, function(i, file) {
                if (file.loaded < file.size) {
                    $('#' + file.id + ' .rmlink').show();
                    //$('#' + file.id + " .bar").css('width', "0%");
                }
            });
            $('#upload_speed').html('');
            _UPLOADER.total.reset();
        });

        _UPLOADER.bind('FilesRemoved', function(up, files) {
            $.each(files, function(i, file) {
                $('#filelist #' + file.id).hide('fast', function(){
                    $('#filelist #' + file.id).remove();
                    if($('#filelist').children().length === 0){
                        $('#uploadfiles').addClass('disabled');
                    }
                });
                if (file.status === plupload.DONE) { //If file has been successfully uploaded
                    $.ajax({
                        type: 'POST',
                        url: '/annotation/detach',
                        data: $.param({
                            file_id: file.id
                        })
                    });
                }

            });
        });

        _UPLOADER.bind('UploadProgress', function(up, file) {
            $('#' + file.id + ' .bar').css('width', file.percent + '%');
            var upload_speed = getBytesWithUnit(up.total.bytesPerSec) + ' per sec';
            L.i(T, 'Progress ' + file.name + ' - ' + file.percent);
            $('#upload_speed').html(upload_speed);
            up.total.reset();
        });


        _UPLOADER.bind('UploadFile', function(up, file) {
            $('#' + file.id + ' .rmlink').hide();
        });

        _UPLOADER.bind('FilesAdded', function(up, files) {
            // var remove_files = [];
            // $.each(up.files, function(i, file) {

            // });


            $(selector).show();
            $('#uploadfiles').removeClass('disabled');
            $('#file-table').show('slow');
            up.total.reset();
            var filename_already_exists = [];
            $.each(files, function(i, file) {
                // Check for existing file
                var removed = false;
                for(var j = 0; j<up.files.length; j++){
                    var existing_file = up.files[j];
                    if(existing_file.id != file.id && file.name == existing_file.name){
                        filename_already_exists.push(file.name);
                        up.removeFile(file);
                        removed = true;
                    }
                }

                if(!removed){
                    $('#filelist').append(tpl_file_entry.render({
                            id: file.id,
                            filename: file.name,
                            filesize: getBytesWithUnit(file.size),
                            removeable: true,
                            progress: 0
                    }));
                    $('#filelist #' + file.id).show('fast');
                    $('#' + file.id + ' .rmlink').on('click', function(){
                        _UPLOADER.removeFile(file);
                    });
                }
            });
            if(filename_already_exists.length > 0) {
                $('#upload-errors').hide();
                $('#upload-errors').append('<div class="alert alert-warning"><a class="close" data-dismiss="alert" href="#">&times;</a><strong>Warning:</strong>' + filename_already_exists.join(', ') + ' already exist.</div>');
                $('#upload-errors').show('fast');
            }
        });

        _UPLOADER.bind('FileUploaded', function(up, file, responseObj) {
            // try{
            //     res_data = JSON.parse(responseObj.response);
            // } catch (err) {}

            // file.server_id = res_data.id;
            L.i(T, 'FileUploaded', responseObj);

            $('#' + file.id + ' .progress').removeClass('progress-striped');
            $('#' + file.id + ' .bar').css('width', '100%');
            $('#' + file.id + ' .rmlink').show();
            $('#' + file.id + ' .progress').hide();
            // $('#' + file.id + '_link').html(tpl_file_link.render({
            //     filename: file.name,
            //     download_url: get_file_url + "?file_id=" + res_data['id']
            // }));
            if (_UPLOADER.total.queued === 0)
                $('#stopupload').hide();

            file.loaded = 0;
            $('#upload_speed').html('');
            up.total.reset();
        });

        function error_message(err) {
            var error_messages = {}, message, http_errors;

            error_messages[plupload.FILE_EXTENSION_ERROR] = 'the file extensions is not allowed.';
            error_messages[plupload.FILE_SIZE_ERROR] = 'the file is too big.';
            error_messages[plupload.GENERIC_ERROR] = 'an unknown error.';
            error_messages[plupload.IO_ERROR] = 'problems reading the file on disk.';
            error_messages[plupload.SECURITY_ERROR] = 'problems reading the file on disk.';

            message = error_messages[err.code];

            if (message !== undefined) {
                return message;
            }

            if (err.code == plupload.HTTP_ERROR) {
                http_errors = {};
                http_errors[401] = 'an authentication error. Please login first.';
                http_errors[403] = 'lack of permissions.';
                http_errors[404] = 'a server error.';
                http_errors[500] = 'a server error.';

                message = http_errors[err.status];

                if (message !== undefined) {
                   return message;
                }
            }

            return 'an unknown error occurred';
        }

        _UPLOADER.bind('Error', function(up, err) {
            had_error = true;
            var message = error_message(err);
            $('#upload-errors').hide();
            if (err.file){
                $('#' + err.file.id + ' .progress').removeClass('progress-striped').addClass('progress-danger');
                $('#upload-errors').append('<div class="alert alert-danger"><strong>Error:</strong> Could not upload ' + err.file.name +' due to ' + message + '</div>');
            } else {
                $('#upload-errors').append('<div class="alert alert-danger"><strong>Error:</strong> ' + message + '</div>');
            }
            $('#upload-errors').show('fast');
            $('#uploadfiles').addClass('disabled');
            $('#stopupload').hide();
            $('#uploadfiles').show();
            up.refresh(); // Reposition Flash/Silverlight
        });

        _UPLOADER.bind('UploadComplete', function() {
            // if(dropbox_files.length > 0 && !had_error) {
            //     start_dropbox_upload();
            // } else {
                // if(!had_error) {
                //     redirect();
                // }
                init_button_states();
            // }
        });
    }  // webdeposit_init_plupload

    // function _init() {
    //     _UPLOADER = new plupload.Uploader({
    //         // General settings
    //         runtimes : 'html5',
    //         url : '/annotation/attach',
    //         max_file_size : '10mb',
    //         chunk_size : '10mb',
    //         browse_button : 'pickfiles',
    //         drop_element : 'filebox'
    //     });
    //     // queue_progress = new plupload.QueueProgress();
    //     _UPLOADER.bind('FilesAdded', function(up, files) {
    //         console.log('file added');
    //         // var html = '';
    //         // plupload.each(files, function(file) {
    //         //     html += '<li id="' + file.id + '">' + file.name + ' (' + plupload.formatSize(file.size) + ') <b></b></li>';
    //         // });
    //         // document.getElementById('filelist').innerHTML += html;
    //     });
    //     _UPLOADER.init();
    // }

    $(document).on('anno_menu_tab_done', function(e, url) {
        if(url === '/annotation/add') {
            _init();
        }
    });

})(window.jQuery);

