/*
 * This file is part of Invenio.
 * Copyright (C) 2013 CERN.
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

/*
 * Plupload
 */

function webdeposit_init_plupload(selector, url) {
  // Convert divs to queue widgets.
  $(selector).pluploadQueue({
    // General settings
    runtimes : 'html5',
    url : url,
    max_file_size : '460mb',
    chunk_size : '1mb',
    unique_names : true,

    // Resize images on clientside if we can
    resize : {width : 320, height : 240, quality : 90},

    // Specify what files to browse for
    filters : [
       {title : "Image files", extensions : "jpg,gif,png,tif"},
       {title : "Compressed files", extensions : "zip,tar,gz"},
       {title : "PDF files", extensions : "pdf"}
    ]
  });
}


/* Error checking */
var errors = 0;
var oldJournal;


function webdeposit_handle_field_data(name, value, data, url, required_fields) {
    // handles a response from the server for the field
    if (data.error == 1) {
        errorMsg = data.error_message;
        $('#error-'+name).html(errorMsg);
        $('.error-list-'+name).hide('slow');
        $('#error-'+name).show('slow');
        $("#error-group-" + name).addClass('error');
        errors++;
    } else {
        $('#error-'+name).hide('slow');
        $('.error-list-'+name).hide('slow');
        $("#error-group-" + name).removeClass('error');
        if (errors > 0)
            errors--;
        emptyForm = checkEmptyFields(false, name, required_fields);
        if (emptyForm[0] == 0) {
            $('#empty-fields-error').hide('slow');
        }
        else {
            $('#empty-fields-error').html("These fields are required!</br>" + emptyForm[1]);
            $('#empty-fields-error').show();
        }
    }

    dismiss = '<button type="button" class="close" data-dismiss="alert">&times;</button>';

    if (data.success == 1) {
        success = '<div class="alert alert-success help-inline" id="success-' + name + '" style="display:none;">'
                  + dismiss + data.success_message +
                  '</div>';
        $('#success-' + name).remove();
        $('#field-' + name).append(success);
        $('#success-' + name).show('slow');
    }
    else {
      $('#success-' + name).remove();
    }

    if (data.info == 1) {
        info = '<div class="alert alert-info help-inline" id="info-' + name + '" style="display:none;">'
               + dismiss + data.info_message +
               '</div>';
        $('#info-' + name).remove();
        $('#field-' + name).append(info);
        $('#info-' + name).css('margin-top', '10px');
        $('#info-' + name).css('clear', 'both');
        $('#info-' + name).css('float', 'left');
        $('#info-' + name).show('slow');
    }
    else {
      $('#info-' + name).remove();
    }

    if (data.fields) {
        $.each(data.fields, function(name, value) {
            $('#error-' + name).hide('slow');
            errors--;
            old_value = $('[name=' + name + ']').val();
            if (old_value != value) {
                $('[name=' + name + ']').val(value);
                webdeposit_handle_new_value(name, value, url, required_fields);
            }
        });
    }

  }

function webdeposit_handle_new_value(name, value, url, required_fields) {
  // sends an ajax request with the data
  $.getJSON(url, {
      name: name,
      attribute: value
  }, function(data){
        webdeposit_handle_field_data(name, value, data, url, required_fields);
  });
}

function webdeposit_input_error_check(selector, url, required_fields) {
  $(selector).change( function() {
      name = this.name;
      value = this.value;
      $.getJSON(url, {
          name: name,
          attribute: value
      }, function(data){
            webdeposit_handle_field_data(name, value, data, url, required_fields)
      });
    return false;
  });
}


function checkEmptyFields(all_fields, field, required_fields) {
    var emptyFields = "";
    var empty = 0;
    $(":text, :file, :checkbox, select, textarea").each(function() {
      // Run the checks only for fields that are required
      if ($.inArray(this.name, required_fields) > -1) {
        if(($(this).val() === "") || ($(this).val() === null)) {
            emptyFields += "- " + $("label[for='"+this.name+"']").html() + "</br>";
            if ( (all_fields === true) || (field == this.name)) {
                $('#error-'+this.name).html($("label[for='"+this.name+"']").html() + " field is required!");
                $('#error-'+this.name).show('slow');
            }
            empty = 1;
        } else {
          $('#error-'+this.name).hide('slow');
        }
      }
    });
    // Return the text only if all fields where requested
    if ( (empty == 1) && all_fields)
        return [1, emptyFields];
    else
        return [0, emptyFields];
}

/* Sherpa Romeo auto completion "_autocomplete?type=journal" */

function type(o){
    return !!o && Object.prototype.toString.call(o).match(/(\w+)\]/)[1];
}

var autocomplete_request = $.ajax();

function webdeposit_field_autocomplete(selector, url) {

    var source = function(query) {
      $(selector).addClass('ui-autocomplete-loading');
      var typeahead = this;
      autocomplete_request.abort();
      autocomplete_request = $.ajax({
        type: 'GET',
        url: url,
        data: $.param({
          term: query
        })
      }).done(function(data) {
        typeahead.process(data.results);
        $(selector).removeClass('ui-autocomplete-loading');
      }).fail(function(data) {
        typeahead.process([query]);
        $(selector).removeClass('ui-autocomplete-loading');
      });
    };
    $(selector).typeahead({
      source: source,
      minLength: 5,
      items: 50
    });
}

/*
  $(function() {
    $('#keywords').keyup( function() {
        keywords = $('#keywords').val();
        if (keywords.indexOf(" ") == -1)
            return;
        keywordsArr = keywords.split(" ");
        txt = "";
        $.each(keywordsArr, function(index, value) {
            if (value != "")
                txt += "<div class='label label-info' id='"+value+"' style='margin-right:5px;margin-bottom:5px; display:inline-block;padding-right:2px;'><i class='icon-tag icon-white'></i><span style='margin-left:1px;margin-right:1px;'>"+ value +"</span><span id='delete_tag'><i class='icon-remove-sign icon-white' style='margin-left:5px;cursor:pointer;'></i></span></div>"
        });
        newtags = $('#editable').html() + txt;
        $('#editable').html(newtags);
        $('#keywords').val('');
        $('#editable').show();

        tempkeywords = $('#keywords2').val();
        $('#keywords2').val(tempkeywords+" "+keywords);

    });
  });

  $('#editable').on("click", "#delete_tag", function(event) {
        alert(this);
        alert("click!!!!");
  });
*/