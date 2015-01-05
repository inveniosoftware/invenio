/*
 * This file is part of Invenio.
 * Copyright (C) 2014, 2015 CERN.
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

  var DecoratedArea = function DecoratedArea() {
    var cmpt;

    this.attributes({
      newEmailSelector: '.new-email',
      emailSelector: '.email',

      placeholder: null,
      delimiter: ';',
      newWasEmpty: false
    });

    this.testEmail = function (email) {
      var re = /^(([^<>()[\]\\.,;:\s@\"]+(\.[^<>()[\]\\.,;:\s@\"]+)*)|(\".+\"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
      return re.test(email);
    };

    this.saveSingleEmail = function (email) {
      if (cmpt.emails.indexOf(email) < 0) {
        cmpt.emails.push(email);
        cmpt.$node.data('emails', cmpt.emails);
      }
      console.debug(cmpt.emails);
      var e = document.createElement('div'),
        dismiss = document.createElement('i');
      e.className = 'email';
      e.innerText = email;
      //e.addEventListener('click', emailClickHandler);
      dismiss.className = 'dismiss fa fa-times';
      dismiss.addEventListener('click', function (ev) {
        $(ev.target.parentElement).remove();
        ev.stopPropagation();
      });
      e.appendChild(dismiss);
      cmpt.select('newEmailSelector').before(e);
    };

    this.isValid = function () {
      var isValid = false,
        content = "",
        emails = [],
        invalid_emails = [],
        re = /^(([^<>()[\]\\.,;:\s@\"]+(\.[^<>()[\]\\.,;:\s@\"]+)*)|(\".+\"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
      cmpt.select('newEmailSelector').removeClass('invalid');
      if (cmpt.select('newEmailSelector').html().indexOf('<div>') >= 0) {
        content = cmpt.select('newEmailSelector').html().replace(/<div>/g, "").replace(/<\/div>/g, " ").replace("<br>", ""); //new lines detection
      } else {
        content = cmpt.select('newEmailSelector').text();
      }
      if (content) {
        if (content.indexOf(cmpt.attr.delimiter) > 0) {
          emails = content.split(this.attr.delimiter);
          emails = emails.map(function (elem) { return elem.trim(); });
          emails.map(function (e) {
            if (cmpt.testEmail(e)) {
              cmpt.saveSingleEmail(e);
            } else {
              invalid_emails.push(e);
            }
          });
          if (invalid_emails.length > 0) {
            content = invalid_emails.join(' ');
            cmpt.select('newEmailSelector').addClass('invalid');
            cmpt.select('newEmailSelector').text(content);
          } else {
            cmpt.select('newEmailSelector').text('');
          }
        } else if (/\s/g.test(content.trim())) {
          emails = content.trim().split(/\s/g);
          emails = emails.map(function (elem) { return elem.trim(); });
          emails.map(function (e) {
            if (cmpt.testEmail(e)) {
              cmpt.saveSingleEmail(e);
            } else {
              invalid_emails.push(e);
            }
          });
          if (invalid_emails.length > 0) {
            content = invalid_emails.join(' ');
            cmpt.select('newEmailSelector').addClass('invalid');
            cmpt.select('newEmailSelector').text(content);
          } else {
            cmpt.select('newEmailSelector').text('');
          }
        } else {
          isValid = re.test(cmpt.select('newEmailSelector').text().trim());
          if (!isValid) {
            cmpt.select('newEmailSelector').addClass('invalid');
          }
        }
      }
      return isValid;
    };

    this.isEmpty = function () {
      var isEmpty = false;
      if (!cmpt.select('newEmailSelector').length) {
        isEmpty = true;
      } else if (!cmpt.select('newEmailSelector').text() && !cmpt.select('emailSelector').length) {
        isEmpty = true;
      }
      return isEmpty;
    };

    this.saveEmail = function () {
      cmpt.select('newEmailSelector').text(function (i, content) {
        var email = $.trim(content);
        if (cmpt.emails.indexOf(email) < 0) {
          cmpt.emails.push(email);
          cmpt.$node.data('emails', cmpt.emails);
        }
        console.debug(cmpt.emails);
        return email;
      });
      cmpt.select('newEmaiSelector').attr('contentEditable', false);
      cmpt.select('newEmailSelector').addClass('email');
      //cmpt.select('emailSelector').click(emailClickHandler);
      var dismiss = document.createElement('i');
      dismiss.className = 'dismiss fa fa-times';
      dismiss.addEventListener('click', function (ev) {
        var pos = cmpt.emails.indexOf($(ev.target.parentElement).text());
        if (pos >= 0) {
          cmpt.emails.splice(pos, 1);
        }
        $(ev.target.parentElement).remove();
        ev.stopPropagation();
      });
      cmpt.select('newEmailSelector').append(dismiss);
      cmpt.select('newEmailSelector').removeClass('new-email');
      cmpt.appendNewEmailInput();
      cmpt.select('newEmailSelector').focus();
    };

    this.appendPlaceholder = function () {
      cmpt.$node.html('<small class=text-muted>' + cmpt.attr.placeholder + '</small>');
    };

    this.appendNewEmailInput = function () {
      var newEmailInput = document.createElement('div');
      newEmailInput.setAttribute('contentEditable', true);
      newEmailInput.setAttribute('tabindex', -1);
      newEmailInput.className = 'new-email';
      newEmailInput.addEventListener('keydown', function (ev) {
        var code = ev.keyCode || ev.which;
        if (code === 13) {
          ev.preventDefault();
        } else if (code === 8) {
          if (!$('.new-email').text()) {
            cmpt.attr.newWasEmpty = true;
          } else {
            cmpt.attr.newWasEmpty = false;
          }
        }
      });
      cmpt.$node.append(newEmailInput);
    };

    this.clickHandler = function (ev) {
      if (cmpt.isEmpty()) {
        cmpt.$node.empty();
        cmpt.appendNewEmailInput();
        cmpt.select('newEmailSelector').focus();
        cmpt.$node.addClass('focused');
      }
      if (cmpt.select('newEmailSelector').length) {
        if ($(ev.target).get(0) === cmpt.$node.get(0)) {
          cmpt.select('newEmailSelector').focus();
        }
        cmpt.$node.addClass('focused');
      }
    };

    this.focusInHandler = function (ev) {
      cmpt.select('newEmailSelector').removeClass('invalid');
      cmpt.$node.removeClass('invalid');
      cmpt.$node.addClass('focused');
      cmpt.$node.parent().removeClass('has-error');
    };

    this.focusOutHandler = function (ev) {
      cmpt.$node.removeClass('focused');
      if (cmpt.isEmpty()) {
        cmpt.appendPlaceholder();
      } else if (cmpt.isValid()) {
        cmpt.saveEmail();
      }
      console.debug(cmpt.emails);
    };

    this.keyUpHandler = function (ev) {
      var code = ev.keyCode || ev.which,
        pos = -1,
        elem;
      if (code === 13 || code === 32 || code === 86) {
        // Enter || Space || V
        if (cmpt.isValid()) {
          cmpt.saveEmail();
        }
      } else if (code === 8 && cmpt.attr.newWasEmpty) {
        // Backspace
        elem = $(':focus');
        if (!elem.hasClass('email')) {
          pos = cmpt.emails.indexOf(cmpt.select('emailSelector').last().text());
          if (pos >= 0) {
            cmpt.emails.splice(pos, 1);
          }
          cmpt.select('emailSelector').last().remove();
        } else {
          /*...*/
        }
      }
    };


    this.after('initialize', function () {
      cmpt = this;
      cmpt.emails = [];
      cmpt.appendPlaceholder();

      cmpt.$node.sortable({
        items: ".email",
        stop: function (event, ui) {
          // prevention
          if (!cmpt.$node.children().last().hasClass('new-email')) {
            cmpt.select('newEmailSelector').before(ui.item);
          }
          /*ui.item.focus();*/
        }
      });

      cmpt.on('click', this.clickHandler);
      cmpt.on('focusin', this.focusInHandler);
      cmpt.on('focusout', this.focusOutHandler);
      cmpt.on('keyup', this.keyUpHandler);
    });
  };

  return require('flight/lib/component')(DecoratedArea);

});
