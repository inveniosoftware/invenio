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
'use strict';

/**
 * This component provides Dropbox functionality.  
 * It supposed to be attached to the Dropbox button.
 *
 * @author Adrian Baran adrian.pawel.baran@cern.ch
 * @version 0.0.1 
 *
 * @requires dropins.js
 * @requires component/util
 *
 * @fires DropboxUploader#filesAdded
 * @fires DropboxUploader#filesRemoved
 *
 * @returns {Component} DropboxUploader
 */
define(function (require) {

  var util = require('js/deposit/uploader/util');

  return require('flight/lib/component')(DropboxUploader);

  function DropboxUploader() {


    this.attributes({
      dropbox_url: "http://httpbin.org/post"
    });

    var self;

    var dropboxFiles = {};

        var options = {

        success: function(files) {
          var newFiles = {};
        files.forEach(function (file) {
          if (dropboxFiles[file.name] === undefined) {
            dropboxFiles[file.name] = file;
            dropboxFiles[file.name].id = util.guid();
            dropboxFiles[file.name].status = 1;
            dropboxFiles[file.name].percent = 0;

            newFiles[file.name] = dropboxFiles[file.name]
          } else {
            self.trigger('uploaderError', {
              message: "Duplicated File"
            });
          }
        });
        files = $.map(newFiles, function (file) {
          return {
            id: file.id,
            name: file.name,
            size: util.bytesToSize(file.bytes),
            percent: file.percent,
            status: file.status
          }
        });
        if (files.length>0) {
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



    this.after('initialize', function () {
      self = this;

      this.on('click', function () {
        Dropbox.choose(options);
      });

      this.on('uploadFiles', function () {


        $.each(dropboxFiles, function (key, val) {
          if (val.status !== 5) {
            self.trigger('fileProgressUpdated', {
                file: {
                  id: val.id,
                  percent: 50, 
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
                }).done(function(data){
                    dropboxFiles[data.filename].server_id = data.id;
                    dropboxFiles[data.filename].status = 5;
                    dropboxFiles[data.filename].percent = 100;
                    self.trigger('filesUploadCompleted', {
                      files: [dropboxFiles[data.filename]]
                    });
                    self.trigger('fileUploadedCompleted', {
                      file: dropboxFiles[data.filename]
                    });
                });
          }
        });

      });

      this.on('fileRemoved', function (ev, data) {
        var fileName;
        $.each(dropboxFiles, function (key, val) {
          if (val.id === data.fileId) {
            fileName = key;
          }
        });
        delete dropboxFiles[fileName];
      });
    });


  }

});