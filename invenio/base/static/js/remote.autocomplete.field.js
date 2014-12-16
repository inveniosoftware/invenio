/*
 * This file is part of Invenio.
 * Copyright (C) 2014 CERN.
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
 * Example:
 * require([
 *   'js/remote.autocomplete.field'
 * ], function(autocomplete) {
 *   autocomplete.attachTo($('input.remote-typeahead-widget'))
 * })
 */

define([ 'jquery', 'typeahead', 'flight/lib/component' ], function($, bloodhound, flight_component){

  "use strict";

  var RemoteAutocomplete = flight_component(function(){
    this.after('initialize', function() {
      var tag = this.$node
      var field_id = tag.attr('id')
      var interfacefield = tag
      var form = interfacefield.closest("form");

      // define automatically interface field and hidden field
      var interfacefield_id = field_id + '_interface'
      var field = $('<input>').attr({
          type: 'hidden',
          id: field_id,
          name: field_id
      })

      // swap
      interfacefield.attr('id', interfacefield_id).removeAttr('name')
      field.appendTo(form);

      // load configuration
      var remote = interfacefield.data('remoteautocompleteRemote')
      var minLength = parseInt(interfacefield.data('remoteautocompleteMinlength'))
      var highlight = interfacefield.data('remoteautocompleteHighlight')
      var data_key = interfacefield.data('remoteautocompleteDataKey')
      var data_value = interfacefield.data('remoteautocompleteDataValue')

      // enable form only after a selection
      form.submit(function(e){
        if(field.val() == '')
          return false;
        return true;
      });

      // init Bloodhound
      var bloodhound = new Bloodhound({
        name: field.attr('id'),
        datumTokenizer: Bloodhound.tokenizers.obj.whitespace('value'),
        queryTokenizer: Bloodhound.tokenizers.whitespace,
        remote: {
          url: remote,
          filter: function(list) {
            return list.results
          }
        }
      });

      bloodhound.initialize();

      // init typeahead
      interfacefield.typeahead({
        highlight: highlight,
        minLength: minLength,
      }, {
        name: field.attr('id'),
        displayKey: data_value,
        source: bloodhound.ttAdapter()
      }).on('typeahead:selected', function (e, data) {
        // set the id_user selected
        field.val(data[data_key])
      });
    });
  });

  return RemoteAutocomplete
})
