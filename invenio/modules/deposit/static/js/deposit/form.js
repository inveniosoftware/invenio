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
        tpl_field_message = require('hgn!./templates/field_message')

    // provides $.fn.dynamicFieldList
    require('./dynamic_field_list')
    // provides $.fn.sortable
    require('ui/sortable')
    // provides $.fn.datepicker
    require('ui/datepicker')

    var messages = {
        errors: 'The form was saved, but there were errors. Please see below.',
        status_saving: 'Saving <img src="/img/loading.gif" />',
        status_error: '<span class="text-danger">Not saved due to server error. Please try to reload your browser <i class="glyphicon glyphicon-warning-sign"></i></span>',
        status_saved: 'Saved <i class="fa fa-check"></i>',
        status_saved_with_errors: '<span class="text-warning">Saved, but with errors <i class="glyphicon glyphicon-warning-sign"></i></span>',
        success: 'Successfully saved.',
        loader: '<img src="/img/loading.gif"/>',
        loader_success: '<span class="text-success"> <i class="fa fa-check"></i></span>',
        loader_failed: '<span class="text-muted"> <i class="glyphicon glyphicon-warning-sign"></i></span>'
    }

  var empty_cssclass = "empty-element";

  // Globals
  var uploader;

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
      if (typeof CKEDITOR !== 'undefined') {
        $.each(CKEDITOR.instances, function(instance, editor) {
          $("#" + instance).val(editor.getData())
        });
      }
      var fields = $(selector).serializeArray();
      if(uploader !== null){
          fields.push({name: 'files', value: serialize_files('#filelist')});
      }
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
      var bytes_to_fixed = bytes.toFixed(2);
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
  function handle_field_msg(name, data) {
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
          var $state_name = $("#state-" + name);
          var $state_group_name = $("#state-group-" + name);

          $state_name.html(
              tpl_field_message({
                  name: name,
                  state: state,
                  messages: data.messages
              })
          );

          var error_state = 'danger';

          ['info', 'warning', 'error', 'success'].forEach(function(s){
              $state_group_name.removeClass(s);
              $state_name.removeClass('alert-'+s);
              if(s == state) {
                  $state_group_name.addClass(state);
                  if(s == 'error') {
                      has_error = true;
                      $state_name.addClass('alert-'+error_state);
                  }
                  else
                      $state_name.addClass('alert-'+state);
              }
          });

          $state_name.show('fast');
          return has_error;
      } else {
          clear_error(name);
          return has_error;
      }
  }

  /**
   */
  function clear_error(name){
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
  function handle_field_values(name, value) {
      if (name == 'files'){
          $.each(value, function(i, file){
              id = unique_id();

              new_file = {
                  id: id,
                  name: file.name,
                  size: file.size
              };

              $('#filelist').append(tpl_file_entry({
                  id: id,
                  filename: file.name,
                  filesize: getBytesWithUnit(file.size)
              }));
              $('#filelist #' + id).show('fast');
          });
          $('#file-table').show('fast');
      } else {
          clear_error(name);
          var has_ckeditor = $('[name=' + name + ']').data('ckeditor');
          if( has_ckeditor === 1) {
              if(CKEDITOR.instances[name].getData(value) != value) {
                  CKEDITOR.instances[name].setData(value);
              }
          } else if (field_lists !== undefined && name in field_lists &&
                     value instanceof Array) {
              for(var i = 0; i < value.length; i++){
                  field_lists[name].update_element(value[i], i);
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
  function handle_response(data) {
      var errors = 0;

      if('messages' in data) {
          $.each(data.messages, function(name, data) {
              if(handle_field_msg(name, data)){
                  errors++;
              }
          });
      }
      if('values' in data) {
          $.each(data.values, handle_field_values);
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
  function set_status(html) {
      $('.status-indicator').show();
      $('.status-indicator').html(html);
  }

  function set_loader(selector, html) {
      $(selector).show();
      $(selector).html(html);
  }

  /**
   * Flash a message in the top.
   */
  function _flash_message(ctx) {
      $('#flash-message').html(tpl_flash_message(ctx));
      $('#flash-message').show('fast');
  }

  /**
   * Save field value value
   */
  function save_field(url, name, value) {
      var request_data = {};
      request_data[name] = value;
      save_data(url, request_data);
  }
  /**
   * Save field value value
   */
  function save_data(url, request_data, flash_message, success_callback, failure_callback) {
      var loader_selector = '#' + name + '-loader';

      if(flash_message === undefined){
          flash_message = false;
      }

      set_status(messages.status_saving);
      set_loader(loader_selector, messages.loader);

      $.ajax(
          json_options({url: url, data: request_data})
      ).done(function(data) {
          var errors = handle_response(data);
          set_loader(loader_selector, messages.loader_success);
          if(errors) {
              set_status(messages.status_saved_with_errors);
              if(flash_message) {
                  _flash_message({state:'warning', message: messages.errors});
              }
              if(failure_callback !== undefined){
                  failure_callback();
              }
          } else {
              set_status(messages.status_saved);
              if(flash_message) {
                  _flash_message({state:'success', message: messages.success});
              }
              if(success_callback !== undefined){
                  success_callback();
              }
          }

      }).fail(function() {
          set_status(messages.status_error);
          set_loader(loader_selector, messages.loader_failed);
      });
  }

  /**
   */
  function check_status(url){
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
  function init_plupload(config) {
      var uuid = config.uuid,
          selector = config.selector,
          max_size = config.max_size,
          db_files = config.db_files,
          url = config.url,
          save_url = config.save_url,
          delete_url = config.delete_url,
          get_file_url = config.get_file_url,
          dropbox_url = config.dropbox_url,
          newdep_url = config.newdep_url,
          continue_url = config.continue_url;

      if($(selector).length === 0){
          uploader = null;
          return;
      }

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
              url = url.replace("-1", uuid);
              uploader.settings.url = url.replace("-1", uuid);
              delete_url = delete_url.replace("-1", uuid);
              get_file_url = get_file_url.replace("-1", uuid);
              dropbox_url = dropbox_url.replace("-1", uuid);
              continue_url = continue_url.replace("-1", uuid);
          }
      }

      new plupload.QueueProgress();

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
                  $('#filelist').append(tpl_file_entry({
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
          $('#' + file.id + " .progress-bar").css('width', "100%");
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
              file.server_id = data.id;

              $('#' + file.id + " .progress").removeClass("progress-striped");
              $('#' + file.id + " .progress").hide();
              $('#' + file.id + " .progress-bar").css('width', "100%");
              $('#' + file.id + '_link').html(tpl_file_link({
                  filename: file.name,
                  download_url: get_file_url + "?file_id=" + data.id
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
                  //$('#' + file.id + " .progress-bar").css('width', "0%");
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
          $('#' + file.id + " .progress-bar").css('width', file.percent + "%");
          var upload_speed = getBytesWithUnit(up.total.bytesPerSec) + " per sec";
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
          var remove_files = [];
          $.each(up.files, function(i, file) {

          });

          $(selector).show();
          $('#uploadfiles').removeClass("disabled");
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
                  $('#filelist').append(tpl_file_entry({
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
              }
          });
          if(filename_already_exists.length > 0) {
              $('#upload-errors').hide();
              $('#upload-errors').append('<div class="alert alert-warning"><a class="close" data-dismiss="alert" href="#">&times;</a><strong>Warning:</strong>' + filename_already_exists.join(", ") + " already exist.</div>");
              $('#upload-errors').show('fast');
          }
      });

      uploader.bind('FileUploaded', function(up, file, responseObj) {
          var res_data = {}
          try{
              res_data = JSON.parse(responseObj.response);
          } catch (err) {
              console.error(err)
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
                  save_field(save_url, 'files', serialize_files("#filelist"));
              }
          }
      });
      $("#filelist").disableSelection();
  }

  /**
   * Initialize save-button
   */
  function init_save(url, selector, form_selector) {
      $(selector).click(function(e){
          e.preventDefault();
          save_data(url, serialize_form(form_selector), true);
          return false;
      });
  }


  /**
   * Initialize submit-button
   */
  function init_submit(url, selector, form_selector, dialog) {
      $(selector).click(function(e){
          e.preventDefault();
          submit(url, form_selector, dialog);
      });
  }

  function submit(url, form_selector, dialog){
      if(dialog !== undefined){
          $(dialog).modal({
              backdrop: 'static',
              keyboard: false,
              show: true,
          });
      }
      save_data(
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
  function init_field_lists(selector, url, autocomplete_selector, url_autocomplete) {
    function serialize_and_save(options) {
      // Save list on remove element, sorting and paste of list
      var data = $('#'+options.prefix).serialize_object();
      if($.isEmptyObject(data)){
          data[options.prefix] = [];
      }
      save_data(url, data);

    }

    function install_handler(options, element) {
      // Install save handler when adding new elements
      $(element).find(":input").change( function() {
          save_field(url, this.name, this.value);
      });
      $(element).find(autocomplete_selector).each(function (){
          init_autocomplete(this, url, url_autocomplete);
      });
    }

    var opts = {
      updated: serialize_and_save,
      removed: serialize_and_save,
      added: install_handler,
      pasted: serialize_and_save,
    };

    $(selector).dynamicFieldList(opts).each(function(index, fieldList){
      field_lists[fieldList.element.id] = fieldList;
    });
  }


  /**
   * Save and check field values for errors.
   */
  function init_inputs(selector, url) {
      $(selector).change( function() {
          if(this.name.indexOf('__input__') == -1){
              save_field(url, this.name, this.value);
          }
      });
  }

  /**
   * Click form-button
   */
  function init_buttons(selector, url) {
      $(selector).click( function() {
          save_field(url, this.name, true);
          return false;
      });
  }


  /**
   * CKEditor initialization
   */
  function init_ckeditor(selector, url) {
      $(selector).each(function(){
          var options = $(this).data('ckeditorConfig');
          if(options ===  undefined){
              CKEDITOR.replace(this);
          } else {
              CKEDITOR.replace(this, options);
          }
          var ckeditor = CKEDITOR.instances[$(this).attr('name')];
          ckeditor.on('blur',function(e){
              save_field(url, e.editor.name, e.editor.getData());
          });
      });
  }


  /**
   * Autocomplete initialization
   */
  function init_autocomplete(selector, save_url, url_template, handle_selection) {
      $(selector).each(function(){
          var item = this;
          var url = url_template.replace("__FIELDNAME__", item.name);

          if(handle_selection === undefined){
              handle_selection = typeahead_selection;
          }

          if($(item).parents('.' + empty_cssclass).length === 0) {
              init_typeaheadjs(item, url, save_url, handle_selection);
          }
      });
  }

  /**
   * Twitter typeahead.js support for autocompletion
   */
  function init_typeaheadjs(item, url, save_url, handle_selection) {
      var autocomplete_request = null;

      function source(query, process) {
          if(autocomplete_request !== null){
              autocomplete_request.abort();
          }
          $(item).addClass('ui-autocomplete-loading');
          autocomplete_request = $.ajax({
              type: 'GET',
              url: url,
              data: $.param({term: query})
          }).done(function(data) {
              process(data);
              $(item).removeClass('ui-autocomplete-loading');
          }).fail(function(data) {
              $(item).removeClass('ui-autocomplete-loading');
          });
      }

      $(item).typeahead({
            minLength: 1
        },
        {
            source: source,
            displayKey: 'value'
      });

      $(item).on('typeahead:selected', function(e, datum, name){
          handle_selection(save_url, item, datum, name);
      });
  }

  /**
   * Handle selection of an autocomplete option
   */
  function typeahead_selection(save_url, item, datum, name) {
      if(typeof datum == 'string') {
          var value = datum;
          datum = {value: value, fields: {}};
          datum.fields = value;
      }
      if(datum.fields === undefined) {
          datum.fields = datum.value;
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
                     $(item).typeahead('val', "");
                  } catch (error) {
                     //Suppress error
                     console.error(error)
                  }
                  // Save list
                  var data = $('#'+field_list_name).serialize_object();
                  if($.isEmptyObject(data)){
                      data[options.prefix] = [];
                  }
                  save_data(save_url, data);
                  return;
              }
          }

          for(var field_name in datum.fields) {
              handle_field_values(field_name, datum.fields[field_name]);
              if(field_name == name) {
                  try {
                     $(item).typeahead('setQuery', datum.fields[field_name]);
                  } catch (error) {
                     //Suppress error
                     console.error(error)
                  }
              }
          }
          //FIXME: sends wrong field names
          save_data(save_url, datum.fields);
      }
  }


  var dropbox_files = [];

  if (document.getElementById("db-chooser") !== null) {
      document.getElementById("db-chooser").addEventListener("DbxChooserSuccess",
          function(e) {
              $('.pluploader').show();
              $('#file-table').show('fast');
              $.each(e.files, function(i, file){
                  var dbfile = {
                      id: unique_id(),
                      name: file.name,
                      size: file.bytes,
                      url: file.link
                  };

                  $('#filelist').append(tpl_file_entry({
                      id: dbfile.id,
                      filename: file.name,
                      filesize: getBytesWithUnit(file.bytes),
                      removeable: true
                  }));
                  $('#filelist #' + dbfile.id).show('fast');
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
   * Exports
   */
  module.exports.submit = submit;

  module.exports.init = function(config){
    init_plupload(config.plupload);
    init_save(config.urls.save_all_url, '.form-save', '#submitForm');
    init_submit(config.urls.complete_url, '.form-submit', '#submitForm', '#form-submit-dialog');
    init_inputs('#submitForm input, #submitForm textarea, #submitForm select', config.urls.save_url);
    init_buttons('#submitForm .form-button', config.urls.save_url);
    init_autocomplete('[data-autocomplete="1"]', config.urls.save_url, config.urls.autocomplete_url);
    init_field_lists('#submitForm .dynamic-field-list', config.urls.save_url, '[data-autocomplete="1"]', config.urls.autocomplete_url);
    init_ckeditor('#submitForm textarea[data-ckeditor="1"]', config.urls.save_url);
    // Initialize rest of jquery plugins
    // Fix issue with typeahead.js drop-down partly cut-off due to overflow ???
    $('#webdeposit_form_accordion').on('hide', function (e) {
      $(e.target).css("overflow","hidden");
    })
    $('#webdeposit_form_accordion').on('shown', function (e) {
      $(e.target).css("overflow", "visible");
    })
    $('#webdeposit_form_accordion .panel-collapse.in.collapse').css("overflow", "visible");
    // Initialize jquery_plugins
    $(config.datepicker.element).datepicker(config.datepicker.options);
  }
})
