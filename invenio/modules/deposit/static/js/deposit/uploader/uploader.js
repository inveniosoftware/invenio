/*
 * This file is part of Invenio.
 * Copyright (C) 2014 CERN.
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
'use strict';

define(function(require) {

    var withUtil = require('js/deposit/uploader/mixins/util'),
        $ = require('jquery');

    return require('flight/lib/component')(Uploader, withUtil);

    function Uploader() {

        var Uploader,
            files = {};

        this.attributes({
            form_files: [],
            uploadersSelector: '.pluploader, .dropboxuploader',
            fileListSelector: '#uploader-filelist',
            errorListSelector: '#uploader-errorlist',
            uploadButtonSelector: '#uploader-upload',
            stopButtonSelector: '#uploader-stop',
            uploadsTableSelector: '#uploads-table',
            form_selector: null,
            delete_url: "http://httpbin.org/post",
            continue_url: null,
            get_file_url: null,
            resolve_uuid_url: null,
            resolve_uuid: false,
            autoupload: false,
            preupload_hooks: {}
        });

        /**
         * Events Handlers
         */

        this.handleFilesAdded = function(ev, data) {
            Uploader.select('uploadButtonSelector').removeAttr('disabled');
            Uploader.select('uploadsTableSelector').css('visibility', 'visible');
            Uploader.select('uploadButtonSelector').css('visibility', 'visible');
            var newFiles = {};

            data.files.forEach(function(file) {
                if (files[file.name] === undefined) {
                    files[file.name] = file
                    newFiles[file.name] = file
                } else {
                    Uploader.trigger('uploaderError', {
                        message: "The file already added to the list."
                    });
                }
            });

            Uploader.trigger(this.select('fileListSelector'), 'filesAddedToFileList', newFiles);
            if (Uploader.attr.autoupload === true) Uploader.handleUpload();
        }

        this.handleFileRemovedByUser = function(ev, data) {
            $.each(files, function(i, file) {
                if (file.id === data.fileId) {
                    data.server_id = file.server_id;
                    delete files[i];
                }
            });
            if (Uploader.getObjectSize(files) === 0) this.select('uploadButtonSelector').attr('disabled', true);
            $.each(this.select('uploadersSelector'), function(i, uploader) {
                Uploader.trigger(uploader, 'fileRemoved', data);
            });

            if (data.server_id) {
                $.ajax({
                    type: "POST",
                    url: this.attr.delete_url,
                    data: $.param({
                        file_id: data.server_id
                    })
                });
            }
        }

        this.handleUploadButtonClick = function(ev, data) {
            Uploader.select('uploadButtonSelector').hide();
            Uploader.select('stopButtonSelector').show();
            for (var key in Uploader.attr.preupload_hooks) {
                if (Uploader.attr.preupload_hooks.hasOwnProperty(key)) Uploader.attr.preupload_hooks[key](Uploader);
            }
            Uploader.handleUpload();
        }

        this.handleUpload = function(ev, data) {
            $.each(this.select('uploadersSelector'), function(i, uploader) {
                Uploader.trigger(uploader, 'uploadFiles');
            });
        }

        this.handleFileProgressUpdated = function(ev, data) {
            files[data.file.name].percent = data.file.percent;
            this.trigger(this.select('fileListSelector'), 'fileProgressUpdatedOnFileList', data)
        }

        this.handleUploadCompleted = function(ev, data) {
            var completedFiles = {};

            $.each(data.files, function(i, file) {
                files[file.name].status = file.status;
                files[file.name].percent = file.percent;
                completedFiles[file.name] = files[file.name];
            });

            var all_done = true;
            $.each(files, function(key, val) {
                if (val.status !== 5) {
                    all_done = false;
                }
            });

            if (all_done) {
                Uploader.select('stopButtonSelector').hide();
                Uploader.select('uploadButtonSelector').show();
                Uploader.select('uploadButtonSelector').attr('disabled', 'true');

                if (Uploader.attr.resolve_uuid) {
                    window.location.href = Uploader.attr.continue_url;
                }
            }

            this.trigger(this.select('fileListSelector'), 'uploadCompleted', completedFiles);
        }

        this.handleFileUploadedCompleted = function(ev, data) {
            files[data.file.name].server_id = data.file.server_id;
        }

        this.handleUploaderError = function(ev, data) {
            this.trigger(this.select('errorListSelector'), 'errorOccurred', data);
        }

        this.handleFileRemovedFromUploader = function(ev, data) {
            //
        }

        this.init_fileList = function(formfiles) {
            if (formfiles.length) {
                formfiles.forEach(function(file) {
                    files[file.name] = {
                        id: file.id,
                        name: file.name,
                        size: Uploader.bytesToSize(file.size),
                        status: 5,
                        percent: 100,
                        server_id: file.id
                    };
                });

                Uploader.trigger(this.select('fileListSelector'), 'filesAddedToFileList', files);
            }
        }

        this.handleFileListUpdated = function() {
            Uploader.trigger($(Uploader.attr.form_selector), 'dataSaveField', {
                name: "files",
                value: Uploader.getOrderedFileList()
            });
        };

        this.handleStopButton = function() {
            Uploader.select('stopButtonSelector').hide();
            Uploader.select('uploadButtonSelector').show();
            if (Uploader.getObjectSize(files) === 0) this.select('uploadButtonSelector').attr('disabled', true);

            $.each(this.select('uploadersSelector'), function(i, uploader) {
                Uploader.trigger(uploader, 'stopUploadFiles');
            });
        }

        this.getOrderedFileList = function() {
            return $.map(Uploader.$node.find('tbody').children(), function(file) {
                for (var elem in files) {
                    if (files[elem].id === file.id && files[elem].status === 5) return file.id;
                }
            })
        };

        this.handleFileListInitialized = function() {
            this.trigger(Uploader.select('fileListSelector'), 'updateGetFileUrl', {
                get_file_url: Uploader.attr.get_file_url
            });
            this.init_fileList(this.attr.form_files);
        };


        this.after('initialize', function() {
            Uploader = this;
            this.on('filesAdded', this.handleFilesAdded);
            this.on('fileRemovedByUser', this.handleFileRemovedByUser);
            this.on('fileProgressUpdated', this.handleFileProgressUpdated);
            this.on('fileUploadedCompleted', this.handleFileUploadedCompleted);
            this.on('filesUploadCompleted', this.handleUploadCompleted);
            this.on('fileRemovedFromUploader', this.handleFileRemovedFromUploader);
            this.on('uploaderError', this.handleUploaderError);
            this.on(this.select('stopButtonSelector'), 'click', this.handleStopButton);
            this.on('fileListUpdated', this.handleFileListUpdated);
            this.on('fileListInitialized', this.handleFileListInitialized);

            if (Uploader.attr.autoupload === false) {
                this.select('uploadButtonSelector').show();
                this.on(this.select('uploadButtonSelector'), 'click', this.handleUploadButtonClick);
            }

            this.$node.data('getOrderedFileList', this.getOrderedFileList);
        });
    }
});
