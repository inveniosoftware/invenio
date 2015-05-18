/*
 * This file is part of Invenio.
 * Copyright (C) 2013, 2014, 2015 CERN.
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
        defineComponent = require('flight/lib/component'),
        tpl_file_entry = require('hgn!./templates/file_entry'),
        tpl_file_link = require('hgn!./templates/file_link'),
        tpl_flash_message = require('hgn!./templates/flash_message'),
        tpl_field_message = require('hgn!./templates/field_message'),
        tpl_save_error = require('hgn!./templates/save_error'),
        tpl_status_saving = require('hgn!./templates/status_saving'),
        tpl_status_error = require('hgn!./templates/status_error'),
        tpl_status_saved = require('hgn!./templates/status_saved'),
        tpl_status_saved_with_error = require('hgn!./templates/status_saved_with_error'),
        tpl_success = require('hgn!./templates/success'),
        tpl_loader = require('hgn!./templates/loader'),
        tpl_loader_success = require('hgn!./templates/loader_success'),
        tpl_loader_failed = require('hgn!./templates/loader_failed')

    // provides $.fn.dynamicFieldList
    require('./dynamic_field_list')
    // provides $.fn.sortable
    require('ui/sortable')
    // provides $.fn.datetimepicker
    require('bootstrap-datetimepicker')
    // provides $.fn.typeahead
    require('typeahead')
  var empty_cssclass = "empty-element";

  return defineComponent(depositForm);

  function depositForm() {
    this.defaultAttrs({
        save_url: "",
        save_all_url: "",
        complete_url: "",
        autocomplete_url: "",
        datepicker_options: {
          format: "YYYY-MM-DD",
          pickTime: false,
        },

        // Selectors
        datepickerSelector: '.datepicker',
        formSelector: '#submitForm',
        formDialogSelector: '#form-submit-dialog',

        // Classes
        formSaveClass: '.form-save',
        formSubmitClass: '.form-submit',
        dynamicFieldListClass : ".dynamic-field-list",
        uploaderSelector: "#uploader"
      });

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

  /**
   * Serialize a form
   */
  this.serialize_form = function(selector){

      // Sync CKEditor before serializing
      if (typeof CKEDITOR !== 'undefined') {
        $.each(CKEDITOR.instances, function(instance, editor) {
          $("#" + instance).val(editor.getData())
        });
      }
      var fields = $(selector).serializeArray(),
          uploader = this.select('uploaderSelector'),
          $checkboxes = $('input[type=checkbox]:not(:checked)'),
          $bootstrap_multiselect = $("[multiple=multiple]");

      if (uploader.length) {
        fields.push({
          name: 'files',
          value: uploader.data('getOrderedFileList')()
        });
      }

      if ($bootstrap_multiselect.length && !$bootstrap_multiselect.val()) {
        fields = fields.concat(
          $bootstrap_multiselect.map(
              function() {
                return {name: this.name, value: $(this).val()}
              }).get()
        );
      }

      if ($checkboxes.length) {
        fields = fields.concat(
          $checkboxes.map(
            function() {
              return {name: this.name, value: ''}
            }).get()
        );
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

          var msgs = $.map(data.messages, function(value, top_index) {
            if (typeof value !== "string") {
              return $.map(value, function(msg, index) {
                return msg;
              });
            } else {
              return [value];
            }
          });

          $state_name.html(tpl_field_message({
            name: name,
            state: state,
            messages: msgs
          }));

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
   * Fired when a form field has to be saved
   *
   * @event dataSaveField
   * @param ev {Event}
   * @param data {Object}
   */
  this.onSaveField = function(ev, data) {
    save_field(this.attr.save_url, data.name, data.value);
  }


  /**
   * Save field value value
   */
  function save_data(url, request_data, flash_message, success_callback, failure_callback) {
      var loader_selector = '#' + name + '-loader';

      if(flash_message === undefined){
          flash_message = false;
      }

      set_status(tpl_status_saving());
      set_loader(loader_selector, tpl_loader());

      $.ajax(
          json_options({url: url, data: request_data})
      ).done(function(data) {
          var errors = handle_response(data);
          set_loader(loader_selector, tpl_loader_success());
          if(errors) {
              set_status(tpl_status_saved_with_error());
              if(flash_message) {
                  _flash_message({state:'warning', message: tpl_save_error()});
              }
              if(failure_callback !== undefined){
                  failure_callback();
              }
          } else {
              set_status(tpl_status_saved());
              if(flash_message) {
                  _flash_message({state:'success', message: tpl_success()});
              }
              if(success_callback !== undefined){
                  success_callback();
              }
          }

      }).fail(function() {
          set_status(tpl_status_error());
          set_loader(loader_selector, tpl_loader_failed());
      });
  }

  /**
   * Fired on save button click
   *
   * @event click
   * @param event {Event}
   */
  this.onSaveClick = function (event) {
      event.preventDefault();
      this.trigger('dataFormSave', {
        url: this.attr.save_all_url,
        form_selector: this.attr.formSelector,
        show: true
      });
      return false;
  }


  /**
   * Fired on submit button click
   * @event click
   * @param event {Event}
   */
  this.onSubmitClick = function (event) {
      event.preventDefault();
      this.trigger('dataFormSubmit', {
        url: this.attr.complete_url,
        form_selector: this.attr.formSelector,
        dialog: this.attr.formDialogSelector
      });
  }

  /**
   * Fired when the form data has to be submitted
   *
   * @event dataFormSubmit
   * @param ev {Event}
   * @param data {Object}
   */
  this.submitForm = function (ev, data) {
      var dialog = data.dialog;
      if(dialog !== undefined){
          $(dialog).modal({
              backdrop: 'static',
              keyboard: false,
              show: true,
          });
      }
      save_data(
           data.url,
           this.serialize_form(data.form_selector),
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
  this.init_field_lists = function(selector, url, autocomplete_selector, url_autocomplete) {
    function serialize_and_save(options) {
      // Save list on remove element, sorting and paste of list
      var data = $('#'+options.prefix).serialize_object();
      if($.isEmptyObject(data)){
          data[options.prefix] = [];
      }
      save_data(url, data);

    }

    var that = this;

    function install_handler(options, element) {
      // Install save handler when adding new elements
      $(element).find(":input").change( function() {
          save_field(url, this.name, this.value);
      });
      $(element).find(autocomplete_selector).each(function (){
          that.init_autocomplete(this, url, url_autocomplete);
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

  this.onFieldChanged = function (event) {
    if(event.target.name.indexOf('__input__') == -1){
              save_field(this.attr.save_url, event.target.name, $(event.target).val());
          }
  }

  /**
   * Fired when text is pasted into an input
   *
   * @event paste
   * @param event {Event}
   */
  this.onFieldPasted = function(event) {
    var that=this;
    /* timeout allows the pasted content to be available */
    setTimeout(function () {
      that.onFieldChanged(event);
    }, 0);
  }

  this.onCheckboxChanged = function (event) {
    if (event.target.name.indexOf('__input__') == -1 && event.target.name) {
      if ($(event.target).prop("checked")) {
        save_field(this.attr.save_url, event.target.name, event.target.value);
      } else {
        save_field(this.attr.save_url, event.target.name, '');
      }
    }
  }

  /**
   * Click form-button
   */
  this.onButtonClick = function (event) {
    save_field(this.attr.save_url, event.target.name, true);
    return false;
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
  this.init_autocomplete = function(selector, save_url, url_template, handle_selection) {
      var that = this;

      $(selector).each(function(){
          var item = this;
          var url = url_template.replace("__FIELDNAME__", item.name);

          if(handle_selection === undefined){
              handle_selection = typeahead_selection;
          }

          if($(item).parents('.' + empty_cssclass).length === 0) {
              that.trigger("form:init-autocomplete", {
                item: item,
                url: url
              });
              connect_typeahead_events($(item), save_url, handle_selection);
          }
      });
  }

  /**
   * Twitter typeahead.js support for autocompletion
   */
  function init_typeahead_dataengine($item, url) {

    var engine = new Bloodhound({
      datumTokenizer: Bloodhound.tokenizers.obj.whitespace('value'),
      queryTokenizer: Bloodhound.tokenizers.whitespace,
      remote: url + "?term=%QUERY&" + $.param({
        limit: $item.data("autocomplete-limit")
      }),
    });

    engine.initialize();

    $item.typeahead({
      minLength: 3
    },
    {
      // after typeahead upgrade to 0.11 can be substituted with:
      // source: this.engine.ttAdapter(),
      // https://github.com/twitter/typeahead.js/issues/166
      source: function(query, callback) {
        // trigger can be deleted after typeahead upgrade to 0.11
        $item.trigger('typeahead:asyncrequest');
        engine.get(query, function(suggestions) {
          $item.trigger('typeahead:asyncreceive');
          callback(suggestions);
        });
      },
      displayKey: 'value'
    });
  }

  /**
   * Connect events of typeahead
   * @param $item
   * @param save_url
   * @param handle_selection
   */
  function connect_typeahead_events($item, save_url, handle_selection) {
      $item.on('typeahead:selected', function(e, datum, name){
          handle_selection(save_url, $item, datum, name);
      });

      $item.on('typeahead:asyncrequest', function() {
          $(this).addClass('ui-autocomplete-loading');
      });

      $item.on('typeahead:asynccancel typeahead:asyncreceive', function() {
          $(this).removeClass('ui-autocomplete-loading');
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

  /**
   * Inits typeahead autocomplete
   *
   * @event form:init-autocomplete
   * @param ev {Event}
   * @param data {Object}
   */
  this.initAutocomplete = function(ev, data) {
    var $item = $(data.item);
    if ($item.attr('data-autocomplete') == 'default') {
      init_typeahead_dataengine($item, data.url);
    }
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
   * Fired when the form data has to be saved
   *
   * @event dataFormSave
   * @param ev {Event}
   * @param data {Object}
   */
  this.saveForm = function(ev, data) {
    save_data(data.url, this.serialize_form(data.form_selector), data.show);
  }

  /**
   * Show validation message for a field.
   *
   * @param ev {Event}
   * @param data {Object}
   */
  this.handleFieldMessage = function(ev, data) {
    handle_field_msg(data.name, data.data);
  };

  this.after('initialize', function() {
    // Custom handlers
    this.on('dataFormSave', this.saveForm);
    this.on('dataFormSubmit', this.submitForm);
    this.on('dataSaveField', this.onSaveField);
    this.on('handleFieldMessage', this.handleFieldMessage);
    this.on("form:init-autocomplete", this.initAutocomplete);

    this.on(document, "click", {
      formSaveClass: this.onSaveClick,
      formSubmitClass: this.onSubmitClick
    });

    this.on(this.attr.formSelector + ' .form-button', "click", this.onButtonClick);
    this.on('#submitForm input[type!=checkbox], #submitForm textarea, #submitForm select', "change", this.onFieldChanged);
    this.on('#submitForm input[type!=checkbox], #submitForm textarea, #submitForm select', "paste", this.onFieldPasted);
    this.on('#submitForm input[type=checkbox]', 'change', this.onCheckboxChanged);

    this.init_autocomplete('[data-autocomplete]', this.attr.save_url, this.attr.autocomplete_url);
    this.init_field_lists(this.attr.formSelector + ' .dynamic-field-list', this.attr.save_url, '[data-autocomplete]', this.attr.autocomplete_url);
    init_ckeditor(this.attr.formSelector + ' textarea[data-ckeditor="1"]', this.attr.save_url);
    // Initialize rest of jquery plugins
    // Fix issue with typeahead.js drop-down partly cut-off due to overflow ???

    //FIXME remove these hacks
    $('#webdeposit_form_accordion').on('hide', function (e) {
      $(e.target).css("overflow","hidden");
    });
    $('#webdeposit_form_accordion').on('shown', function (e) {
      $(e.target).css("overflow", "visible");
    })
    // Initialize jquery_plugins
    $(this.attr.datepickerSelector).datetimepicker(this.attr.datepicker_options);

    $('.form-group input[type="radio"]').on('mousedown', function(){
        // http://stackoverflow.com/a/6246260
        var $self = $(this);
        if( $self.is(':checked') ){
            var uncheck = function(){
                setTimeout(function(){
                    $self.removeAttr('checked');
                    $self.trigger('change');
                },0);
            };
            var unbind = function(){
                $self.unbind('mouseup',up);
            };
            var up = function(){
                uncheck();
                unbind();
            };
            $self.bind('mouseup',up);
            $self.one('mouseout', unbind);
        }
    });
  });

  }
})
