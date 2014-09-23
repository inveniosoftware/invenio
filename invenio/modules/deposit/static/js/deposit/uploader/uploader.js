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

define(function (require) {

  var util = require('js/deposit/uploader/util');

  return require('flight/lib/component')(Uploader);

  function Uploader() {

    var Uploader,
        files = {};

    this.attributes({
      formfiles: [],

      uploadersSelector: '#uploader-uploaders',
      fileListSelector: '#uploader-filelist',
      errorListSelector: '#uploader-errorlist',
      uploadButtonSelector: '#uploader-upload',
      form_selector: null, 
      save_url: null,
      get_file_url: null
    });

    /**
     * Events Handlers
     */

    this.handleFilesAdded = function (ev, data) {
      var newFiles = {};

      data.files.forEach(function (file) {
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
    }

    this.handleFileRemovedByUser = function (ev, data) {
      $.each(files, function (i, file) {
        if (file.id === data.fileId) {
          data.server_id = file.server_id;
          delete files[i];
        }
      });

      $.each(this.select('uploadersSelector').children(), function (i, uploader) {
        Uploader.trigger(uploader, 'fileRemoved', data);
      });
    }

    this.handleUpload = function (ev, data) {
      $.each(this.select('uploadersSelector').children(), function (i, uploader) {
        Uploader.trigger(uploader, 'uploadFiles');
      });
    }

    this.handleFileProgressUpdated = function (ev, data) {
      files[data.file.name].percent = data.file.percent;
      this.trigger(this.select('fileListSelector'), 'fileProgressUpdatedOnFileList', data)
    }

    this.handleUploadCompleted = function (ev, data) {
      var completedFiles = {};

      $.each(data.files, function (i, file) {
        files[file.name].status = file.status;
        files[file.name].percent = file.percent;
        completedFiles[file.name] = files[file.name];
      });

      this.trigger(this.select('fileListSelector'), 'uploadCompleted', completedFiles);
    }

    this.handleFileUploadedCompleted = function (ev, data) {
      files[data.file.name].server_id = data.file.server_id;
    }

    this.handleUploaderError = function (ev, data) {
      this.trigger(this.select('errorListSelector'), 'errorOccurred', data);
    }

    this.handleFileRemovedFromUploader = function (ev, data) {
      //
    }

    this.init_fileList = function (formfiles) {
      formfiles.forEach(function (file) {
        files[file.name] = {
          id: file.id,
          name: file.name,
          size: util.bytesToSize(file.size),
          status: 5,
          percent: 100,
          server_id: file.id
        };
      });

      Uploader.trigger(this.select('fileListSelector'), 'filesAddedToFileList', files);
    }

    this.handleFileListUpdated = function () {
      Uploader.trigger($(Uploader.attr.form_selector), 'dataSaveField', {
        save_url: Uploader.attr.save_url,
        name: "files",
        value: Uploader.getOrderedFileList()
      });
    };

    this.getOrderedFileList = function () {
      return $.map(Uploader.$node.find('tbody').children(), function (file) { 
        for (var elem in files) {
          if (files[elem].id === file.id && files[elem].status === 5) return file.id;
        }
      })
    };

    this.after('initialize', function () {
      Uploader = this;
      var FileList = require('js/deposit/uploader/ui/filelist');
      var ErrorList = require('js/deposit/uploader/ui/errorList');

      FileList.attachTo(this.select('fileListSelector'), {
        get_file_url: Uploader.attr.get_file_url
      });
      ErrorList.attachTo(this.select('errorListSelector'));

      this.init_fileList(this.attr.formfiles);

      this.on('filesAdded', this.handleFilesAdded);
      this.on('fileRemovedByUser', this.handleFileRemovedByUser);
      this.on('fileProgressUpdated', this.handleFileProgressUpdated);
      this.on('fileUploadedCompleted', this.handleFileUploadedCompleted);
      this.on('filesUploadCompleted', this.handleUploadCompleted);
      this.on('fileRemovedFromUploader', this.handleFileRemovedFromUploader);
      this.on('uploaderError', this.handleUploaderError);

      this.on(this.select('uploadButtonSelector'), 'click', this.handleUpload);
      this.on('fileListUpdated', this.handleFileListUpdated);

      this.$node.data('getOrderedFileList', this.getOrderedFileList);
    });

  }

});
// ## TODO: tiredToAddExistingFile ERRORS in general
// ## not to all but discover by tag or name
// ## remove file from server
// ## autoupload funciton
// ## TODO: zielone tylko jak sa jakies nowe pliki