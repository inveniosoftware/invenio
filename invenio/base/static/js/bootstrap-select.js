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


!function ($) {

  "use strict"; // jshint ;_;


 /* BUTTON SELECT PUBLIC CLASS DEFINITION
  * ===================================== */

  var ButtonSelect = function (element, options) {
    var that = this
    this.$element = $(element)
    this.options = $.extend({}, $.fn.buttonSelect.defaults, options)
    this.$wrap = this.$element.wrap(this.options.wrap)
                .parent();
    this.$prev = $(this.options.button).clone()
                .html(this.options.prev)
                .appendTo(this.$wrap)
    this.$span = $(this.options.span).clone()
                .text(this.$element.children(':selected').text())
                .appendTo(this.$wrap)
    this.$next = $(this.options.button).clone()
                .html(this.options.next)
                .appendTo(this.$wrap)
    this.$element.appendTo(this.$wrap.parent()).hide()
    this.$element.change(function() {
      that.$span.text(that.$element.children(':selected').text())
    })
    this.$next.on('click', function(e) {
      ButtonSelect.prototype.next.call(that)
    })
    this.$prev.on('click', function(e) {
      ButtonSelect.prototype.prev.call(that)
    })
  }

  ButtonSelect.prototype.next = function () {
    var i = this.$element.prop('selectedIndex'),
        l = this.$element.children('option').length
    if (i+1<l) {
      this.$element.prop('selectedIndex', i+1)
      this.$element.change()
    }
  }

  ButtonSelect.prototype.prev = function () {
    var i = this.$element.prop('selectedIndex')
    if (i>0) {
      this.$element.prop('selectedIndex', i-1)
      this.$element.change()
    }
  }

 /* BUTTON SELECT PLUGIN DEFINITION
  * =============================== */

  $.fn.buttonSelect = function (option) {
    return this.each(function () {
      var $this = $(this)
        , data = $this.data('buttonSelect')
        , options = typeof option == 'object' && option
      if (!data) $this.data('buttonSelect', (data = new ButtonSelect(this, options)))
      if (typeof option == 'string') data[option]()
    })
  }

  $.fn.buttonSelect.defaults = {
    wrap: '<div class="btn-group" />'
  , button: '<a class="btn" />'
  , span: '<span class="btn" />'
  , next: '&gt;'
  , prev: '&lt;'
  }

  $.fn.buttonSelect.Constructor = ButtonSelect


 /* BUTTON SELECT DATA-API
  * ====================== */

  $(function () {
    $('select[data-change=select]').buttonSelect({})
  })

}(window.jQuery);
