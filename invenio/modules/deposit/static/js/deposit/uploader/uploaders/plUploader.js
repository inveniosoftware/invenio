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
 * This component provides PlUpload functionality.  
 * It supposed to be attached to the PlUpload button.
 *
 * @author Adrian Baran adrian.pawel.baran@cern.ch
 * @version 0.0.1 
 *
 * @requires plupload/js/plupload.full.min
 * @requires component/util
 *
 * @fires PlUploader#filesAdded
 * @fires PlUploader#filesRemoved
 * @fires PlUploader#fileProgressUpdated
 * @fires PlUploader#fileUploadCompleted
 * @fires PlUploader#uploaderError
 *
 * @returns {Component} PlUploader
 */
define(function (require) {

  var util = require('js/deposit/uploader/util');

  return require('flight/lib/component')(PlUploader);

  function PlUploader() {


    this.attributes({
      url: "http://httpbin.org/post",
      delete_url: "http://httpbin.org/post",
      drop_element: null,
      max_file_size: null
    });


    this.after('initialize', function () {

      var that = this;

      var PlUploader = new plupload.Uploader({
          browse_button: this.$node[0],
          url: this.attr.url,
          max_file_size: this.attr.max_file_size,
          drop_element: this.attr.drop_element,
          dragdrop: true,

          filters: {
            prevent_duplicates: true
        }
      });

      /**
        * Evevt Handlers
        */

      that.on('uploadFiles', function (ev, data) {
        PlUploader.start();
      });

      that.on('fileRemoved', function (ev, data) {
        var file = PlUploader.getFile(data.fileId);
        if (file !== undefined) {
          PlUploader.removeFile(file);
        }

        if (data.server_id) {
          $.ajax({
            type: "POST",
            url: this.attr.delete_url,
            data: $.param({
                file_id: data.server_id
            })
          });
        }
      });

      /**
       * Triggers
       */

      PlUploader.bind('FilesAdded', function (up, files) {
        files = $.map(files, function (file) {
          return {
            id: file.id,
            name: file.name,
            size: util.bytesToSize(file.size),
            percent: file.percent,
            status: file.status
          }
        });

        that.trigger('filesAdded', {
          files: files
        });
        });

      PlUploader.bind('FilesRemoved', function (up, file) {
        //
      });

        PlUploader.bind('UploadProgress', function (up, file) {
          var upload_speed = util.bytesToSize(up.total.bytesPerSec)+ "/s";
          that.trigger('fileProgressUpdated', {
            file: {
              id: file.id,
              percent: file.percent,
              name: file.name
            },
            upload_speed: upload_speed
          });
      });

      PlUploader.bind('FileUploaded', function (up, file, responseObj) {
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

      PlUploader.bind('UploadComplete', function (up, files) {
        files = $.map(files, function (file) {
          return {
            id: file.id,
            name: file.name,
            size: util.bytesToSize(file.size),
            status: file.status,
            percent: file.percent
          }
        });

        that.trigger('filesUploadCompleted', {
          files: files
        });
      });
      
      PlUploader.bind('Error', function (up, error) {
        that.trigger('uploaderError', {
          message: error.message
        });
      });

      PlUploader.init();
    });


  }

});

//## TODO: gdzie dac konfiguracje domysle chyba ze wyspecyfikowane jakies

//## TODO: gdy zly url - blad zglosic
//## TODO: file filter plupload.com/docs/File-filters
//## TODO: add JSDOC
//## TODO: duplicate file error