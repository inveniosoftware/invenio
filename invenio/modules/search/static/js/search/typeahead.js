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


/* A file contatining fuctions treating the search field. */

!function( $ ){

  "use strict"

  // It is necessary to import Bootstrap Typeahead before.
  var Typeahead = $.fn.typeahead.Constructor;

  var orig = {
    lookup: $.fn.typeahead.Constructor.prototype.lookup,
    render: $.fn.typeahead.Constructor.prototype.render,
    matcher:$.fn.typeahead.Constructor.prototype.matcher,
    select:$.fn.typeahead.Constructor.prototype.select
  };

  // Let's inherit Typeahead.
  function SearchTypeahead(e, o) { Typeahead.call(this, e, o) }

  SearchTypeahead.prototype = new Typeahead();

  $.extend(SearchTypeahead.prototype, {
    lookup: function(event) {
      var query = this.$element.val(),
          sources = this.options.sources,
          m = query.lastIndexOf(':'),
          type = query.substr(0,m),
          n = type.lastIndexOf(' ');
      if (0<n && n<m) {
        type = type.substr(n+1);
      }
      if (m>query.lastIndexOf(' ') && type in sources) {
        this.options.type = 'data';
        this.source = sources[type];
      } else {
        this.options.type = 'search';
        this.source = this.options.source;
      }
      //this.source = $.isFunction(this.source) ? this.source() : this.source
      orig.lookup.call(this);
    },
    select: function() {
      var val = this.$menu.find('.active').attr('data-value')
        , cwrap = (val.lastIndexOf(' ') > 0)?'"':''

      if (this.options.type == 'data') {
        var m = this.query.lastIndexOf(':')
          , newVal = this.$element.val().substr(0, m);
        if (~m) {
          newVal += ':'+cwrap;
        }
        this.$element.val(newVal+val+cwrap+' ');
        this.$element.change();
        this.options.type = 'search';
        return this.hide();
      }

      if (this.options.type == 'search') {
      var m = this.query.lastIndexOf(' '),
          im = (m<0)?0:m+1,
          p = this.$element.val(),
          op = ("+-|".indexOf(p[im])>-1)?p[im]:'',
          newVal = p.substr(0, m);
      if (~m) {
        newVal += ' ';
      }
      this.$element.val(newVal+op+val);
      this.$element.change();
      return this.hide();
      }

      orig.select.call(this);
      return this;
    },

    matcher: function(item) {

      if (this.options.type == 'data') {
        var m = this.query.lastIndexOf(':'),
            search = this.query.substr(m + 1).toLowerCase();
        return search.length && ~item.toLowerCase().indexOf(search);
      }

      if (this.options.type == 'search') {
        var m = this.query.lastIndexOf(' '),
            offset = 0,
            search = this.query.substr(m + 1).toLowerCase();
        if (search.length && "+-|".indexOf(search[0]) > -1) {
          offset = 1;
        }
        return search.length &&
          ~item.toLowerCase().indexOf(search.substr(offset));
      }

      return orig.matcher.call(this, item);
    }
  });

  $.fn.searchTypeahead = function (option) {
    return this.each(function () {
      var $this = $(this)
        , data = $this.data('typeahead')
        , options = typeof option == 'object' && option
      if (!data) $this.data('typeahead', (data = new SearchTypeahead(this, options)))
      if (typeof option == 'string') data[option]()
    })
  }

  $.fn.searchTypeahead.defaults = $.fn.typeahead.defaults
  $.fn.searchTypeahead.Constructor = SearchTypeahead

}( window.jQuery )
