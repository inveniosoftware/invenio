
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


define(function(require, exports, module) {
  'use strict';

  var $ = require('jquery'),
      tpl_file_entry = require('hgn!./templates/file_entry'),
      tpl_file_link = require('hgn!./templates/file_link'),
      tpl_flash_message = require('hgn!./templates/flash_message'),
      tpl_field_message = require('hgn!./templates/field_message');

  var PluploadWidget = function(element, options) {
    this.$element = $(element);
    this.options = $.extend({}, $.fn.pluploadWidget.defaults, options);

    this.init();
  };

  PluploadWidget.prototype = {

    constructor: PluploadWidget,

    init: function() {
    /*
     * Initialize plupload plugin for `element`.
     */

      var that = this,
          url = this.options.url,
          save_url = this.options.save_url,
          delete_url = this.options.delete_url,
          get_file_url = this.options.get_file_url,
          dropbox_url = this.options.dropbox_url,
          newdep_url = this.options.newdep_url,
          continue_url = this.options.continue_url;

      var $upload_start = this.$element.find('.upload-start'),
          $upload_stop = this.$element.find('.upload-stop'),
          $upload_speed = this.$element.find('.upload-speed'),
          $upload_filetable = this.$element.find('.upload-filetable'),
          $upload_filelist = this.$element.find('.upload-filelist'),
          $upload_errors = this.$element.find('.upload-errors');

      var had_error = false;

      // Set prevent_duplicates to true if not specified
      if ( this.options.filters.prevent_duplicates === undefined ) {
        this.options.filters.prevent_duplicates = true;
      }

      this.uploader = new plupload.Uploader({
          // General settings
          runtimes : this.options.runtimes,
          url : url,
          max_file_size : this.options.max_file_size,
          chunk_size : this.options.chunk_size,
          unique_names : this.options.unique_names,
          browse_button : this.options.browse_button,
          drop_element : this.options.drop_element,
          filters : this.options.filters,
          autoupload : this.options.autoupload,
      });

      new plupload.QueueProgress();

      this.uploader.init();

      /**
       */

      function init_button_states(){
          $upload_start.addClass("disabled");
          $upload_stop.hide();
          $upload_start.show();
          $upload_speed.html('');
          had_error = false;
      }

      function redirect(){
          if(continue_url){
              if( window.location != continue_url ){
                  window.location = continue_url;
              }
          }
      }

      $upload_start.click(function(e) {
          e.preventDefault();

          $upload_start.addClass('disabled');
          $upload_start.hide();
          $upload_stop.show();

          if(that.uploader.files.length > 0){
              that.uploader.start();
          } else if (dropbox_files.length > 0) {
              start_dropbox_upload();
          }
      });

      $upload_stop.click(function(d){
          uploader.stop();
          $upload_stop.hide();
          $upload_start.show();
          $upload_start.removeClass('disabled');
          $.each(uploader.files, function(i, file) {
              if (file.loaded < file.size) {
                  $("#" + file.id + " .rmlink").show();
                  //$('#' + file.id + " .progress-bar").css('width', "0%");
              }
          });
          $upload_speed.html('');
          uploader.total.reset();
      });

      this.uploader.bind('FilesRemoved', function(up, files) {
          $.each(files, function(i, file) {
              $upload_filelist.find('#' + file.id).hide('fast', function(){
                  $upload_filelist.find('#' + file.id).remove();
                  if($upload_filelist.children().length === 0){
                      $upload_start.addClass("disabled");
                  }
              });
              if (file.status === plupload.DONE) { //If file has been successfully uploaded
                  $.ajax({
                      type: "POST",
                      url: delete_url,
                      data: $.param({
                          file_id: file.server_id
                      })
                  });
              }

          });
      });

      this.uploader.bind('UploadProgress', function(up, file) {
          $('#' + file.id + " .progress-bar").css('width', file.percent + "%");
          var upload_speed = that.getBytesWithUnit(up.total.bytesPerSec) + " per sec";
          console.log("Progress " + file.name + " - " + file.percent);
          $upload_speed.html(upload_speed);
          up.total.reset();
      });


      this.uploader.bind('UploadFile', function(up, file) {
          $('#' + file.id + " .rmlink").hide();
      });

      this.uploader.bind('FilesAdded', function(up, files) {
          that.$element.show();
          $upload_start.removeClass("disabled");
          $upload_filetable.show('slow');
          up.total.reset();
          $.each(files, function(index, file) {
            $upload_filelist.append(tpl_file_entry({
                  id: file.id,
                  filename: file.name,
                  filesize: that.getBytesWithUnit(file.size),
                  removeable: true,
                  progress: 0
            }));
            $('#' + file.id).show('fast');
            $('#' + file.id + ' .rmlink').on("click", function(event){
                up.removeFile(file);
            });
          });
          // auto start upload
          if ( that.options.autoupload ) {
            up.start();
          }
      });

      this.uploader.bind('FileUploaded', function(up, file, responseObj) {
          var res_data = {};

          try {
              res_data = JSON.parse(responseObj.response);
          } catch (err) {
              console.error(err);
          }

          file.server_id = res_data.id;

          $('#' + file.id + " .progress").removeClass("progress-striped");
          $('#' + file.id + " .progress-bar").css('width', "100%");
          $('#' + file.id + ' .rmlink').show();
          $('#' + file.id + " .progress").hide();
          $('#' + file.id + '_link').html(tpl_file_link({
              filename: file.name,
              download_url: get_file_url + "?file_id=" + res_data.id
          }));
          if (that.uploader.total.queued === 0)
              $upload_stop.hide();

          file.loaded = 0;
          $upload_speed.html('');
          up.total.reset();
      });

      function error_message(err) {
          var error_messages = {}, message, http_errors;

          error_messages[plupload.FILE_EXTENSION_ERROR] = "the file extensions is not allowed.";
          error_messages[plupload.FILE_SIZE_ERROR] = "the file is too big.";
          error_messages[plupload.GENERIC_ERROR] = "an unknown error.";
          error_messages[plupload.IO_ERROR] = "problems reading the file on disk.";
          error_messages[plupload.SECURITY_ERROR] = "problems reading the file on disk.";
          error_messages[plupload.FILE_DUPLICATE_ERROR] = "duplicated file.";

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

      this.uploader.bind('Error', function(up, err) {
          had_error = true;
          var message = error_message(err);
          $upload_errors.hide();
          if (err.file){
              $('#' + err.file.id + " .progress").removeClass("progress-striped").addClass("progress-danger");
              $upload_errors.append(tpl_flash_message({state:"danger",
                message:'<strong>Error:</strong> Could not upload ' + err.file.name +" due to " + message})
              );
          } else {
              $upload_errors.append(tpl_flash_message({state:"danger",
                message:'<strong>Error:</strong> ' + message})
              );
          }
          $upload_errors.show('fast');
          $upload_start.addClass("disabled");
          $upload_stop.hide();
          $upload_start.show();
          up.refresh(); // Reposition Flash/Silverlight
      });

      this.uploader.bind('UploadComplete', function(up, files) {
        if(!had_error) {
          redirect();
        }
        init_button_states();
      });

      this.val(this.options.files);

      $upload_filelist.sortable({
          forcePlaceholderSize: true,
          forceHelperSizeType: true,
          handle: ".sortlink",
          start: function(event, ui) {
              $(ui.placeholder).show();
              $(ui.placeholder).html("<td></td><td></td><td></td><td></td>");
              $(ui.placeholder).css("visibility", "");
              var header_ths = $("#file-table thead th"),
                  item_tds = $(ui.helper).find("td"),
                  placeholder_tds = $(ui.placeholder).find("td");
              for(var i = 0; i < header_ths.length; i++){
                  $(item_tds[i]).width($(header_ths[i]).width());
                  $(placeholder_tds[i]).width($(header_ths[i]).width());
              }
          },
          update: function(event, ui){
              if (save_url) {
                  $(that.options.form_selector).trigger("dataSaveField", {
                    save_url: save_url,
                    name: "files",
                    value: that.val()
                  });
              }
          }
      });

      $upload_filelist.disableSelection();
    },

    getBytesWithUnit: function(bytes) {
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
    },

    fake_file: function (file) {
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
    },

    val: function (value) {
      /* Set/get list of files from Plupload. */
      var that = this, ids, files, result,
          $upload_filetable = this.$element.find('.upload-filetable'),
          $upload_filelist = this.$element.find('.upload-filelist');

      if ( arguments.length ) {
          if (!$.isEmptyObject(value)) {
              $upload_filetable.show('slow');

              $.each(value, function(i, file) {
                  // Simulate a plupload file object
                  var plfile = that.fake_file(file);

                  that.uploader.files.push(plfile);
                  $upload_filelist.append(tpl_file_entry({
                      id: plfile.id,
                      filename: plfile.name,
                      filesize: that.getBytesWithUnit(plfile.size),
                      download_url: that.options.get_file_url + "?file_id=" + plfile.id,
                      removeable: true,
                      completed: true,
                  }));
                  $('#' + plfile.id).show('fast');
                  $("#" + plfile.id + " .rmlink").on("click", function(event) {
                      that.uploader.removeFile(plfile);
                  });
              });
          }

        return;
      }
      // Extract ids
      ids = this.$element.find('tr[id]').map(function(){ return $(this).attr('id');});
      // Build search dict
      files = {};
      $.each(this.uploader.files, function(idx, elem){
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
    },

    connectEvents: function() {},

    onStart: function() {},

    onStop: function() {},

  };

  $.fn.pluploadWidget = function ( option ) {
    return this.each(function () {
      var $this = $(this),
          data = $this.data('pluploadWidget'),
          options = typeof option == 'object' && option;
      if (!data) {
        $this.data('pluploadWidget', (data = new PluploadWidget(this, options)));
      }
      if (typeof option == 'string') {
        data[option]();
      }
    });
  };

  $.fn.pluploadWidget.defaults = {
    files: null,
    runtimes: 'html5,html4',
    chunksize: '10mb',
    unique_names : true,
    browse_button : 'pickfiles',
    drop_element : 'field-plupload_file',
    form_selector: "#submitForm",
    filters : {},
    autoupload: false,
  };

  $.fn.pluploadWidget.Constructor = PluploadWidget;

});
