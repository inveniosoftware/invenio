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

    return require('flight/lib/component')(DropboxUploader, withUtil);

    function DropboxUploader() {


        this.attributes({
            dropbox_url: "http://httpbin.org/post",
            max_files_count: null,
            preupload_hooks: {}
        });

        var self;
        var pause = false;

        var dropboxFiles = {};

        var options = {

            success: function(files) {
                if (self.attr.max_files_count && (Object.keys(dropboxFiles).length + files.length > self.attr.max_files_count)) {
                    var maxFilesToAdd = self.attr.max_files_count - Object.keys(dropboxFiles).length;
                    while (files.length > maxFilesToAdd) {
                        files.pop();
                    }
                    self.trigger('uploaderError', {
                        message: "Max files count exceeded."
                    });
                }
                var newFiles = {};
                files.forEach(function(file) {
                    if (dropboxFiles[file.name] === undefined) {
                        dropboxFiles[file.name] = file;
                        dropboxFiles[file.name].id = self.guid();
                        dropboxFiles[file.name].status = 1;
                        dropboxFiles[file.name].percent = 0;

                        newFiles[file.name] = dropboxFiles[file.name]
                    } else {
                        self.trigger('uploaderError', {
                            message: "Duplicated File"
                        });
                    }
                });
                files = $.map(newFiles, function(file) {
                    return {
                        id: file.id,
                        name: file.name,
                        size: self.bytesToSize(file.bytes),
                        percent: file.percent,
                        status: file.status
                    }
                });
                if (files.length > 0) {
                    self.trigger('filesAdded', {
                        files: files
                    });
                }
            },

            cancel: function() {
                console.log('canceled');
            },

            linkType: "direct", // "preview" or "direct"

            multiselect: true,

            // extensions: ['.pdf', '.doc', '.docx'],
        };

        /**
         * Evevt Handlers
         */

        this.after('initialize', function() {
            self = this;

            this.on('click', function() {
                Dropbox.choose(options);
            });

            this.on('uploadFiles', function(ev, data) {
                for (var key in self.attr.preupload_hooks) {
                    if (self.attr.preupload_hooks.hasOwnProperty(key)) self.attr.preupload_hooks[key](self);
                }
                pause = false;

                $.each(dropboxFiles, function(key, val) {
                    var filename = val.name;
                    var all_done = true;
                    if (val.status !== 5) {
                        if (pause === 5) return false;
                        self.trigger('fileProgressUpdated', {
                            file: {
                                id: val.id,
                                percent: 80,
                                name: val.name
                            }
                        });
                        $.ajax({
                            type: 'POST',
                            url: self.attr.dropbox_url,
                            data: $.param({
                                name: val.name,
                                size: val.bytes,
                                url: val.link
                            }),
                            dataType: "json"
                        }).done(function(data) {
                            dropboxFiles[filename].server_id = data.id;
                            dropboxFiles[filename].status = 5;
                            dropboxFiles[filename].percent = 100;
                            self.trigger('fileUploadedCompleted', {
                                file: dropboxFiles[filename]
                            });

                            all_done = true;
                            $.each(dropboxFiles, function(key, val) {
                                if (val.status !== 5) all_done = false;
                            });
                            if (all_done) {
                                self.trigger('filesUploadCompleted', {
                                    files: dropboxFiles
                                });
                            }
                        });
                    }
                });

            });

            this.on('stopUploadFiles', function(ev, data) {});

            this.on('fileRemoved', function(ev, data) {
                var fileName;
                $.each(dropboxFiles, function(key, val) {
                    if (val.id === data.fileId) {
                        fileName = key;
                    }
                });
                delete dropboxFiles[fileName];
            });
        });
    }
});
