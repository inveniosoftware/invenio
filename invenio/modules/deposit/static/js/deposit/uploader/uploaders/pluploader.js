/*
 * This file is part of Invenio.
 * Copyright (C) 2014, 2015 CERN.
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
define(function(require) {
    'use strict';

    var withUtil = require('js/deposit/uploader/mixins/util'),
        $ = require('jquery');

    return require('flight/lib/component')(PlUploader, withUtil);

    function PlUploader() {


        this.attributes({
            url: "http://httpbin.org/post",
            drop_element: null,
            max_file_size: null,
            max_files_count: null,
            preupload_hooks: {},
            filters: {prevent_duplicates: true}
        });


        this.after('initialize', function() {

            var that = this;

            var PlUploader = new plupload.Uploader({
                browse_button: this.$node[0],
                url: this.attr.url,
                chunk_size: '10mb',
                max_file_size: this.attr.max_file_size,
                drop_element: this.attr.drop_element,
                dragdrop: true,

                filters: this.attr.filters
            });

            /**
             * Evevt Handlers
             */

            that.on('uploadFiles', function(ev, data) {
                for (var key in that.attr.preupload_hooks) {
                    if (that.attr.preupload_hooks.hasOwnProperty(key)) that.attr.preupload_hooks[key](that);
                }
                PlUploader.settings.url = that.attr.url;
                PlUploader.start();
            });

            that.on('fileRemoved', function(ev, data) {
                var file = PlUploader.getFile(data.fileId);
                if (file !== undefined) {
                    PlUploader.removeFile(file);
                }
            });

            that.on('stopUploadFiles', function(ev, data) {
                PlUploader.stop();
            });

            /**
             * Triggers
             */

            PlUploader.bind('FilesAdded', function(up, files) {
                if (that.attr.max_files_count && (up.files.length > that.attr.max_files_count)) {
                    up.removeFile(files[files.length-1]);
                    files.pop();
                    that.trigger('uploaderError', {
                        message: "Max files count exceeded."
                    });
                }
                files = $.map(files, function(file) {
                    return {
                        id: file.id,
                        name: file.name,
                        size: that.bytesToSize(file.size),
                        percent: file.percent,
                        status: file.status
                    }
                });

                that.trigger('filesAdded', {
                    files: files
                });
            });

            PlUploader.bind('FilesRemoved', function(up, file) {
                //
            });

            PlUploader.bind('UploadProgress', function(up, file) {
                var upload_speed = that.bytesToSize(up.total.bytesPerSec) + "/s";
                that.trigger('fileProgressUpdated', {
                    file: {
                        id: file.id,
                        percent: file.percent,
                        name: file.name
                    },
                    upload_speed: upload_speed
                });
            });

            PlUploader.bind('FileUploaded', function(up, file, responseObj) {
                var res_data = {};

                try {
                    res_data = JSON.parse(responseObj.response);
                } catch (err) {
                    console.error(err);
                }

                that.trigger('fileUploadedCompleted', {
                    file: {
                        id: file.id,
                        name: file.name,
                        server_id: res_data.id
                    }
                });
            });

            PlUploader.bind('UploadComplete', function(up, files) {
                files = $.map(files, function(file) {
                    return {
                        id: file.id,
                        name: file.name,
                        size: that.bytesToSize(file.size),
                        status: file.status,
                        percent: file.percent
                    }
                });

                that.trigger('filesUploadCompleted', {
                    files: files
                });
            });

            PlUploader.bind('Error', function(up, error) {
                that.trigger('uploaderError', {
                    message: error.message
                });
            });

            PlUploader.init();
        });
    }
});
