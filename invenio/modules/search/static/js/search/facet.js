/*
 * This file is part of Invenio.
 * Copyright (C) 2012, 2014 CERN.
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


/* A file containing functions treating the faceting functionality. */
require(['jquery'], function($) {

  "use strict"

  var Facet = function(element, options) {
    this.$element = $(element)
    this.options = $.extend({}, $.fn.facet.defaults, options)

    this.wrap = function(a, p) {
      if (a.length > 1) {
        a[0] = p[0] + a[0];
        a[a.length-1] = a[a.length-1] + p[1];
      }
      return a;
    }
    this.groupByKey = function(a) {
      var group = {}
      a.map(function(value) {
        if (! (value[1] in group)) {
          group[value[1]] = []
        }
        group[value[1]].push(value[2])
      })
      return group
    }

    this.init()
  }

  Facet.prototype = {

    constructor: Facet

  , init: function() {
    /*
     * Initialize facet plugin for `element`.
     */

      var that = this,
          element = this.$element,
          facets = this.options.facets

      this.options.url_map = {}

      for (var i in facets) {
        var f = facets[i];
        this.options.url_map[f.facet] = f.url
        // Create facet sidebar.
        $(this.options.box_builder(f.facet, f.title)).appendTo(element);

        this.createFacetBox(f, $('.'+f.facet+' .context'), {})
      } // end for

      this.filter = []


    } // end init function

  , limitTo: function() {
      return jQuery.grep(this.filter, function (a) { return a[0] == '+' })
    }

  , excludeTo: function() {
      return jQuery.grep(this.filter, function (a) { return a[0] == '-' })
    }

  , expand: function() {
      return jQuery.grep(this.filter, function (a) { return a[0] == '!' })
    }

  , find: function(op, key, value) {
      return jQuery.grep(this.filter, function (a) {
        return a[0] == op && a[1] == key && a[2] == value
      })
    }

  , findByKey: function(key) {
      return jQuery.grep(this.filter, function (a) {
        return (a[0] == '+' || a[0] == '-') && a[1] == key
      })
    }

  , exclude: function(op, key, value) {
      return jQuery.grep(this.filter, function (a) {
        return a[0] != op || a[1] != key || a[2] != value
      })
    }

  , exists: function(op, key, value) {
      return this.find(op, key, value).length > 0
    }

  , createFacetBox: function(facet, element, data) {
      var that = this,
          split_by = this.options.split_by,
          button_more = this.options.button_builder(this.options.title_more),
          button_less = this.options.button_builder(this.options.title_less),
          row_builder = this.options.row_builder

      $(element).data('facet', facet)
      // Load sidebar options.
      $.ajax({
        url: facet.url,
        dataType : 'json',
        data: data,
        context: {element: element, facet: facet, that: this, data: data}
      }).done(function(json) {
        var el = this.element,
            options = this.facet,
            name = options.facet,
            data = this.data,
            context = this

        /* Generate facet rows with checkboxes. */
        $.each(json.facet, function(){
          var $row = $(row_builder(this, name))
          if (data.parent) {
            $row.on('click', function() {
              context.that._delete('+', name, data.parent)
              context.that._delete('-', name, data.parent)
              el.trigger($.Event('deleted', {op: '', key: name, value: data.parent}));
            })
          }
          $row.appendTo(el);
        });

        /* Append buttons */
        var l = $(button_less),
            m = $(button_more);

        m.on('click', function(e) {
          var controls = el.find('.controls:not(:visible)').slice(0,split_by)
          l.show();
          if (controls.length < split_by) {
            m.hide();
          }
          controls.show();
          return false
        }).appendTo(el);

        l.on('click', function(e) {
          var controls = el.find('.controls:visible');
          m.show();
          if (controls.length > split_by) {
            controls.slice(split_by).slice(-1-split_by).hide();
          }
          if (controls.length <= 2*split_by) {
            l.hide();
          }
          return false
        }).addClass('pull-right').appendTo(el);

        el.find('.controls:not(:visible)').slice(0,split_by).show();

        l.hide();
        if (json.facet.length <= split_by) {
          m.hide();
        }

        element.trigger($.Event('loaded', {
          name:name
        , facet:json.facet
        , options: options
        }));

        if (json.facet.length) {
          el.parent().parent().show();
          //$(this).parent().addClass("in");
          //$controls.show();
        }

      }); // end ajax done
    }

  , queryString: function() {
      var that = this,
          limit = that.wrap($.map(that.groupByKey(that.limitTo()), function(k, v) {
            var fields = $.map(k, function(i) {
              return v+':'+ that.wrap(i.split(' '),'""').join(' ');
            });
            return that.wrap(fields,"()").join(' OR ');
          }),"()").join(' AND '),
          exclude = $.map(that.groupByKey(that.excludeTo()), function(k, v) {
            var fields = $.map(k, function(i) { return ' AND NOT '+v+':'+i });
            return fields.join('');
          }).join('');
      return limit + exclude;
    }

  , updateFacets: function(prefix) {
      var that = this;
      this.$element.find('input:checked').each(function(i,el) {
        that._addFacet(prefix, $(el).attr('name'), $(el).val());
      });
      this.$element.trigger($.Event('updated'));
      return false;
    }

  , rebuildFilter: function(filter) {
      var that = this;
      this._clear();
      this.filter = filter
      $.each(this.limitTo(), function(i,v) {
        that._addFacet(v[0], v[1], v[2]);
        that.$element.trigger($.Event('added', {op: v[0], key: v[1], value: v[2]}));
      });
      $.each(this.excludeTo(), function(i,v) {
        that._addFacet(v[0], v[1], v[2]);
        that.$element.trigger($.Event('added', {op: v[0], key: v[1], value: v[2]}));
      });

      this.$element.trigger($.Event('updated'));
      return this;
    }

  , _addFacet: function(op, key, value) {
      var that = this,
          values = this.find(op, key, value)

      if (values.length > 0) {
        return false
      } else {
        this.filter.push([op, key, value])
      }

      var op2 = op == '+' ? '-' : '+'
      this._delete(op2, key, value)

      return true;
    }

  , addFacet: function(op, key, value) {
      if (this._addFacet(op, key, value)) {
        this.$element.trigger($.Event('added', {op: op, key: key, value: value}));
        this.$element.trigger($.Event('updated'));
      } else {
        this.$element.trigger($.Event('exists'));
      }
    }

  , _delete: function(op, key, value) {
      var excluded = this.exclude(op, key, value)

      if (excluded.length < this.filter.length) {
        this.filter = excluded
        return true
      }
      return false
    }

  , delete: function(op, key, value) {
      if (this._delete(op, key, value)) {
        this.$element.trigger($.Event('deleted', {op: op, key: key, value: value}));
      }
      this.$element.trigger($.Event('updated'));
    }

  , toggleFacet: function(op, key, value) {
      var keys = this.findByKey(key),
          exclude = this.exclude(op, key, value)
      if (keys.length > 0) {
        if (exclude.length < this.filter.length) {
          return this.delete(op, key, value)
        }
      }
      return this.addFacet(op, key, value)
    }

  , resetKey: function(key) {
      this.filter = jQuery.grep(this.filter, function (a) {
        return a[1] != key
      })

      this.$element.trigger($.Event('updated'));
    }

  , _clear: function() {
      this.filter = jQuery.grep(this.filter, function (a) {
        // keep additional information about filter
        return a[0] == '+' || a[0] == '-'
      })
      return this;
    }

  , clear: function() {
      this._clear()
      this.$element.trigger($.Event('updated'));
      return this;
    }
  }

  /* FACET PLUGIN DEFINITION
   * ======================= */

  $.fn.facet = function ( option ) {
    return this.each(function () {
      var $this = $(this)
        , data = $this.data('facet')
        , options = typeof option == 'object' && option
      if (!data) $this.data('facet', (data = new Facet(this, options)))
      if (typeof option == 'string') data[option]()
    })
  }

  $.fn.facet.defaults = {
    box_builder: function(name, title) {
      return '<div class="panel panel-default">' +
            '<div class="panel-heading">' +
              '<a data-toggle="collapse"' +
                ' data-target=".panel-collapse.' + name + '">' +
                    title +
                '</a>' +
              '</div>' +
              '<div class="' + name + ' panel-collapse collapse">' +
                '<div class="panel-body context">' +
                  '<!-- AJAX load -->' +
                '</div>' +
              '</div>' +
            '</div>';
    },
    row_builder: function(data, name) {
      return '<div class="controls" style="display:none;">'+
              '<label class="checkbox">' +
                '<input type="checkbox" name="'+ name +'" value="'+ data[0] +'">' +
                data[(data.length==3)?2:0] + ' (' + data[1] + ')'+
              '</label>' +
            '</div>';
    },
    button_builder: function(title) {
      return '<span class="btn btn-xs">'+title+'</span>';
    },
    clear_button_builder: function(title) {
      return '<span class="pull-right btn btn-danger">'+title+'</span>';
    },
    badge: $('<span/>', {style: 'float:left; line-height: 18px; margin-right: 5px', 'class': 'badge'}),
    close: $('<a/>', {'class': 'close', html:'&nbsp;×'}),
    op_classes: {'+': 'badge-info', '-': 'badge-important'},
    split_by: 5, // display by chunks of N elements
    title_exclude: 'Exclude', // translationable title
    title_limit_to: 'Limit to', // translationable title
    title_clear: 'Clear', // translationable title
    title_more: 'More', // translationable title
    title_less: 'Less' // translationable title
  };

  $.fn.facet.Constructor = Facet

  $(function () {
    $('body').on('click.facet.data-api', '[data-facet="toggle"]', function (e) {
      var $t = $(e.currentTarget),
          action = $t.attr('data-facet-action'),
          target = $t.attr('data-target')
      if (e.shiftKey) {
        action = (action=='+')?'-':'+'
        $t.attr('data-facet-action')
      }

      $(target).data('facet').toggleFacet(
        action,
        $t.attr('data-facet-key'),
        $t.attr('data-facet-value')
      )
    })

    $('body').on('click.facet.data-api', '[data-facet="reset-key"]', function (e) {
      var $t = $(e.currentTarget),
          target = $t.attr('data-target')
      $(target).data('facet').resetKey(
        $t.attr('data-facet-key')
      )
    })
  })

  /* AFFIX WIDTH FIX
   * ===============
   * Fixes issue with affix loosing it's width once removed from the DOM
   * See https://github.com/twbs/bootstrap/issues/6350
   *
   * Example:
   * --------
   * <div data-clampedwidth=".myParent">This long content will force clamped width</div>
   */
  $('[data-clampedwidth]').each(function () {
      var elem = $(this);
      var parentPanel = elem.data('clampedwidth');
      var resizeFn = function () {
          var sideBarNavWidth = $(parentPanel).width() -
            parseInt(elem.css('paddingLeft')) -
            parseInt(elem.css('paddingRight')) -
            parseInt(elem.css('marginLeft')) -
            parseInt(elem.css('marginRight')) -
            parseInt(elem.css('borderLeftWidth')) -
            parseInt(elem.css('borderRightWidth'));
          elem.css('width', sideBarNavWidth);
      };
      resizeFn();
      $(window).resize(resizeFn);
  });
});
