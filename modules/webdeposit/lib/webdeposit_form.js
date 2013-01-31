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

function webdeposit_input_error_check(selector, url, required_fields) {
  $(selector).change( function() {
      name = this.name;
      value = this.value;
      $.getJSON(url, {
          name: name,
          attribute: value
      }, function(data) {
        if (data.error == 1) {
            errorMsg = data.error_message;
            $('#error-'+name).html(errorMsg);
            $('#error-'+name).show('slow');
            errors++;
        } else {
            $('#error-'+name).hide('slow');
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
    if (empty == 1)
        return [1, emptyFields];
    else
        return [0, emptyFields];
}

/* Sherpa Romeo auto completion "_autocomplete?type=journal" */

function type(o){
    return !!o && Object.prototype.toString.call(o).match(/(\w+)\]/)[1];
}

function webdeposit_field_autocomplete(selector, url) {

    var source = function(query) {
      $(selector).addClass('ui-autocomplete-loading');
      var typeahead = this;
      $.ajax({
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