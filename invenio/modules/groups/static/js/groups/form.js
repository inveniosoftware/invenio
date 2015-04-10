/*
 * This file is part of Invenio.
 * Copyright (C) 2015 CERN.
 *
 * Invenio is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 2 of the
 * License, or (at your option) any later version.
 *
 * Invenio is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Invenio; if not, write to the Free Software Foundation, Inc.,
 * 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
 */

define(function (require) {
  'use strict';

  var NewMemberForm = function NewMemberForm() {
    var form;

    this.attributes({
    });

    this.getData = function () {
      var emails = $('#emails').data('emails') || [];

      return {
        'emails': emails,
        'user_status': "PENDING"
      };
    };

    this.validateRequired = function () {
      var isValid = false;

      if (form.getData().emails.length) {
        isValid = true;
      } else {
        $("#emails").addClass("invalid");
        $("#emails").parent().addClass('has-error');
      }

      return isValid;
    };

    this.submitHandler = function (ev) {
      var ajaxSettings = {
        'type': 'POST',
        'url': '',
        'contentType': 'application/json',
        'data': '',
        'dataType': 'json'
      },
        data;

      ev.preventDefault();

      if (form.validateRequired()) {
        ajaxSettings.data = JSON.stringify(form.getData());
        $.ajax(
          ajaxSettings
        ).done(function (data) {
          window.location = data.url;
        });
      }
    };

    this.after('initialize', function () {
      form = this;

      this.on('submit', this.submitHandler);
    });
  };

  return require('flight/lib/component')(NewMemberForm);

});
