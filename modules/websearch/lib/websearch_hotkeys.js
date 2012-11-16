/*
 * This file is part of Invenio.
 * Copyright (C) 2012 CERN.
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


/* A file contatining fuctions treating the hotkey shortcuts. */

!function( $ ){

  "use strict"

  var Hotkeys = function(options) {

    /* make sure we call new operator first */
    if (!(this instanceof Hotkeys))
      return new Hotkeys(options)

    this.options = $.extend({}, this.defaults, options)
    this.init()
  }

  Hotkeys.fn = Hotkeys.prototype = {

    constructor: Hotkeys

  , defaults: {
      timeout: 500 // how long should we keep buffer before reseting it?
    }

  , init: function() {
    /*
     * Initialize hotkeys.
     */
      var that = this

      this.setTimer()
      this.clearBuffer()
      this.data = {}

      $('[data-hotkey-action="click"]').each(function(index, object) {
        var key = $(object).attr('data-hotkey-value')
        that.data[key] = $(object)
      })

      $(document).bind('keydown.esc', function(event) {
        that.clearTimer()
        that.clearBuffer()
      })

      $(document).bind('keydown', function(event) {
        // Don't fire in text-accepting inputs that we didn't directly bind to
        // important to note that $.fn.prop is only available on jquery 1.6+
        if ( this !== event.target && (/textarea|select/i.test( event.target.nodeName ) ||
            event.target.type === "text" || $(event.target).prop('contenteditable') == 'true' )) {
          return;
        }

        var character = String.fromCharCode( event.which ).toLowerCase()
        that.addCharacter(character)
        that.action()
        that.setTimer()
      })

    } // end init function

  , clearTimer: function() {
      if (this.timer)
        clearTimeout(this.timer)
    }

  , setTimer: function() {
      this.clearTimer()
      var that = this
        , c = function() {
          that.clearBuffer()
        }
      this.timer = setTimeout(c, this.options['timeout'])
    }

  , clearBuffer: function() {
      this.buffer = ''
    }

  , addCharacter: function(c) {
      this.buffer += c
    }

  , isDefined: function() {
      var key = String(this.buffer)
      return (key in this.data)
    }

  , getCurrentObject: function() {
      return this.data[this.buffer]
    }

  , action: function() {
      if (this.isDefined()) {
        window.location.href = this.getCurrentObject().attr('href')
        /* should not be called becase of redirection */
        this.clearBuffer()
        this.clearTimer()
      }
    }

  }

  window.Hotkeys = Hotkeys

}( window.jQuery )
