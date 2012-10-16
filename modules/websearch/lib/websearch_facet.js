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


/* A file contatining fuctions treating the faceting functionality. */

!function( $ ){

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
    };

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
          filter = this.options.filter,
          facets = this.options.facets,
          split_by = this.options.split_by,
          button_more = this.options.button_builder(this.options.title_more),
          button_less = this.options.button_builder(this.options.title_less),
          //button_clear = this.options.clear_button_builder(this.options.title_clear),
          row_builder = this.options.row_builder;

      /*
      var $controls = $(this.options.controls_builder());
      $controls.hide().appendTo(element);
      $(this.options.control_button_builder(this.options.title_limit_to))
        .addClass('btn-info').on('click', function() {
          return that.updateFacets('+');
        }).appendTo($controls);
      $(this.options.control_button_builder(this.options.title_exclude))
        .addClass('btn-danger').on('click', function() {
          return that.updateFacets('-');
        }).appendTo($controls);
      */

      for (var i in facets) {
        var f = facets[i];

        // Create selected facet filter.
        $(this.options.filter_builder(f.facet, f.title)).appendTo(filter);
        // Create facet sidebar.
        $(this.options.box_builder(f.facet, f.title)).appendTo(element);
        // Load sidebar options.
        $.ajax({
          url: f.url,
          dataType : 'json',
          context: $('.'+f.facet+' .context').data('facet', f.facet)
        }).done(function(json) {
          var el = $(this),
              name = el.data('facet');

          /* Generate facet rows with checkboxes. */
          $.each(json.facet, function(){
            $(row_builder(this, name)).appendTo(el);
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
          }).addClass('pull-right').appendTo(el);

          el.find('.controls:not(:visible)').slice(0,split_by).show();

          l.hide();
          if (json.facet.length <= split_by) {
            m.hide();
          }

          element.trigger($.Event('loaded', {name:name, facet:json.facet}));

          if (json.facet.length) {
            $(this).parent().parent().show();
            //$(this).parent().addClass("in");
            //$controls.show();
          }

        }); // end ajax done
      } // end for

      // Filter clear button.
      //$(button_clear).on('click', $.proxy(this.clear, this)).appendTo(filter);

      this.filter = {'+': {}, '-': {} };


    } // end init function

  , queryString: function() {
      var that = this,
          limit = that.wrap($.map(this.filter['+'], function(k, v) {
            var fields = $.map(k, function(i) {
              return v+':'+ that.wrap(i.split(' '),'""').join(' ');
            });
            return that.wrap(fields,"()").join(' OR ');
          }),"()").join(' AND '),
          exclude = $.map(this.filter['-'], function(k, v) {
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
      if ('+' in filter) {
      $.each(filter['+'], function(k, vs) {
        $.each(vs, function(i, v) {
          that._addFacet('+', k, v);
        });
      });
      }
      if ('-' in filter) {
      $.each(filter['-'], function(k, vs) {
        $.each(vs, function(i, v) {
          that._addFacet('-', k, v);
        });
      });
      }
      this.$element.trigger($.Event('updated'));
      return this;
    }

  , _addFacet: function(op, key, value) {
      var that = this

      if (key in this.filter[op]) {
        if ($.inArray(value, this.filter[op][key])>-1) {
          return false;
        } else {
          this.filter[op][key].push(value);
        }
      } else {
        this.filter[op][key] = [value];
      }

      var op2 = op == '+' ? '-' : '+'
      this._delete(op2, key, value)

      /*
      filter.find('.'+key).show().parent().show();
      filter.find('.'+key+' span.data').append(
        that.options.badge.clone().addClass(that.options.op_classes[op]).append(
          that.options.close.clone().on('click', function(event) {
            $(this).parent().remove();
            that.delete(op, key, value);
          })
        ).append(value)
      );
      */
      this.$element.trigger($.Event('added', {op: op, key: key, value: value}));
      return true;
    }

  , addFacet: function(op, key, value) {
      if (this._addFacet(op, key, value)) {
        this.$element.trigger($.Event('updated'));
      } else {
        this.$element.trigger($.Event('exists'));
      }
    }

  , _delete: function(op, key, value) {
      var filter = $(this.options.filter),
          r = this.filter[op][key],
          i = $.inArray(value, r)

      if (i>-1) {
        this.filter[op][key].splice(i,1);
        if (!this.filter[op][key].length) {
          delete this.filter[op][key];
          this.$element.trigger($.Event('deleted', {op: op, key: key, value: value}));
        }
      }
    }

  , delete: function(op, key, value) {
      this._delete(op, key, value);
      this.$element.trigger($.Event('updated'));
    }

  , toggleFacet: function(op, key, value) {
      if (key in this.filter[op]) {
        if ($.inArray(value, this.filter[op][key])>-1) {
          return this.delete(op, key, value)
        }
      }
      return this.addFacet(op, key, value)
    }

  , resetKey: function(key) {
      var that = this,
          filter = this.filter
      if ('+' in filter && key in filter['+'] && filter['+'][key].length) {
        var values = $.extend([], filter['+'][key])
        $.each(values, function(i, v) {
          that._delete('+', key, v)
        })
      }
      if ('-' in filter && key in filter['-'] && filter['-'][key].length) {
        var values = $.extend([], filter['-'][key])
        $.each(values, function(i, v) {
          that._delete('-', key, v)
        })
      }
      this.$element.trigger($.Event('updated'));
    }

  , _clear: function() {
      var that = this,
          filter = $(this.options.filter);
      $.each(this.filter['+'], function(k, vs) {
        filter.find('.'+k+' span.data').children().remove();
        $.each(vs.slice(), function(i,v) {
          that._delete('+', k, v);
        });
      });
      $.each(this.filter['-'], function(k, vs) {
        filter.find('.'+k+' span.data').children().remove();
        $.each(vs.slice(), function(i,v) { that._delete('-', k, v); });
      });
      this.filter['+'] = {};
      this.filter['-'] = {};
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
      return '<div class="accordion-group">' +
            '<div class="accordion-heading">' +
              '<a class="accordion-toggle" data-toggle="collapse"' +
                ' data-target=".accordion-body.' + name + '">' +
                    title +
                '</a>' +
              '</div>' +
              '<div class="' + name + ' accordion-body collapse">' +
                '<div class="accordion-inner context">' +
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
      return '<span class="btn btn-mini">'+title+'</span>';
    },
    clear_button_builder: function(title) {
      return '<span class="pull-right btn btn-danger">'+title+'</span>';
    },
    filter_builder: function(name, title) {
      return '<div style="margin-bottom: 2px;" class="\
        ' + name + ' row facets_fill">\
        <strong class="span1">' + title + ':</strong>\
        <span class="data span6">\
        </span>\
        </div>';
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

}( window.jQuery )
