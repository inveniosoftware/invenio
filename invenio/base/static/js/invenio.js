/*
 * This file is part of Invenio.
 * Copyright (C) 2013, 2014, 2015 CERN.
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

require(['jquery', 'bootstrap'], function ($) {

  "use strict"; // jshint ;_;

  $(function() {
    /* ENABLE AUTOMATIC MENU LOADING
     * =============================
     *
     * Finds all elements with `data-menu="click"` attributes and loads menu with
     * AJAX call to url specified in attribute `data-menu-source`.
     *
     * Example:
     * --------
     *
     * <li>
     *   <a href="#">
     *     <span data-menu="click" data-menu-source="/menu">
     *       AJAX menu
     *     </span>
     *   </a>
     * </li>
     */

    $('[data-menu="click"]').each(function (index) {
      var that = this,
        $menu = $(this).parent(),
        $li = $menu.parent(),
        message_update = function(obj) {
          $(that).unbind('click');
          $.ajax({
            url: $(that).attr('data-menu-source')
          }).done(function (data) {
            $menu.parent().append(data);
          });
        };
      $(that).on('click', message_update);
      $li.addClass('dropdown');
      $menu.attr('data-toggle', "dropdown");
      $menu.dropdown();
    });

    /* ENABLE AUTOMATIC POPOVER REGISTRATION
     * =============================
     *
     * Finds all elements with `data-toggle="popover"` attributes and
     * registers the bootstrap popover element.
     * Attributes:
     *  data-content = text placed inside the popover
     *  data-original-title = title of popover
     *  data-html = whether the text should be rendered as HTML
     *  data-placement = left / right / top / bottom
     *
     * Clicking link/button with data-dismiss="popover" inside the popover
     * will close the popover.
     *
     * Example:
     * --------
     *
     * <a href="#"
     *  data-toggle="popover"
     *  data-html="true"
     *  data-original-title="Qua"
     *  data-content="<b>Qua</b> qua qua">
     *     open popover
     * </a>
     */
    $('[data-toggle="popover"]').each(function(){
      var $this = $(this);
      var bHtml = Boolean($this.attr('data-html'));
      var placement = $this.attr('data-placement');

      if(! placement)
      {
        placement = 'bottom';
      }

      var $popover = $(this).popover({
        html: bHtml,
        placement: placement,
      });

      $popover.popover('show');
      $popover.popover('hide');

      // Register the closing button
      $popover.parent().delegate('[data-dismiss="popover"]', 'click', function() {
        $popover.popover('hide');
      });
    });

    /* ENABLE AUTOMATIC JEDITABLE REGISTRATION
     * =============================
     *
     * Finds all elements with 'data-editable' attribute and
     * registers the element to use jeditable plugin.
     * Some elements can be created after document initialization,
     * therefore this function is triggered by click
     * (which usually opens the edit box)
     *
     * Attributes:
     *  data-editable = type of edit: text / textarea / select
     *  jeditable-action = URL to which data should be sent
     *
     * Some attributes are mirroring jeditable attributes,
     * which can be found here:
     * http://www.appelsiini.net/projects/jeditable
     *
     *  jeditable-XXX sets the option XXX in jeditable constructor
     *
     * (Not all options are mapped though, add them if you need them)
     *
     * Example:
     * --------
     *
     * <p data-editable="textarea"
     *  jeditable-action="{{ url_for('webtag.update_annotation', id_tag = tag.id, id_bibrec = id_bibrec) }}"
     *  jeditable-onblur='submit'
     *  id="webtag_annotation_{{id_bibrec}}_{{tag.id}}">{{tag.annotation}}</p>
     */
    $(document).delegate('[data-editable]', 'click', function(){
    //$('[data-editable]').each(function(){
      var $this = $(this);

      $this.editable($this.attr('jeditable-action'), {
         type      : $this.attr('data-editable') || 'textarea',
         cancel    : $this.attr('jeditable-cancel') || '',
         submit    : $this.attr('jeditable-submit') || '',
         indicator : $this.attr('jeditable-indicator') || 'Saving...',
         tooltip   : $this.attr('jeditable-tooltip') || 'Click to edit...',
         id        : $this.attr('jeditable-post-property-id') || 'id',
         name      : $this.attr('jeditable-post-property-value') || 'value',
         cssclass  : $this.attr('jeditable-cssclass') || '',
         onblur    : $this.attr('jeditable-onblur') || 'cancel',
         placeholder: $this.attr('jeditable-placeholder') || '',
      });

      //Remove attribute to prevent executing again
      $this.removeAttr('data-editable');

      //Trigger click event on the underlying jeditable object
      $this.trigger('click');

    });
  });

  function bindModals(filter, focusOn) {
    // Support for AJAX loaded modal window.
    // Focuses on first input textbox after it loads the window.
    if (filter) {
      filter = '[data-toggle="modal"]' + filter;
    } else {
      filter = '[data-toggle="modal"][href]';
    }
    $(filter).click(function (e) {
        e.preventDefault();
        var href = $(this).attr('href');
        if (href.indexOf('#') === 0) {
            $(href).modal({show: true});
        } else {
            $.get(href, function(data) {
                $('<div class="modal" >' + data + '</div>').modal();
            }).success(function() {
                if(focusOn) {
                    $(focusOn).focus()
                }
            });
        }
    });
  }

  $(document).ready(function() {
    bindModals();
  });
  window.bindModals = bindModals;

  $(document).on('hidden.bs.modal', function() {
        // delete any existing modal elements instead of just hiding them
        var href = $(this).attr('href');
        if (href !== undefined){
            $('.modal').remove();
            $('.modal-backdrop').remove();
        }
  });

  $('[rel=tooltip]').tooltip();

  $(document).ready(function(){
    var delta = 10;

    // name your elements here
    var stickyElement  = '.sticky',   // the element you want to make sticky
    bottomElement  = 'footer'; // the bottom element where you want the sticky element to stop (usually the footer)

    $(stickyElement).each(function() {
      var element = this;

      // figure out if we are not in one-column mode
      $(window).on('resize orientationChanged', null, element, function(evt) {
        var element = evt.data;
        $(element).css('width', '');

        window.setTimeout(function() {
          $(element).css('width', $(element).outerWidth());

          if (window.matchMedia('(min-width: 992px)').matches) {
            // let's save some messy code in clean variables
            // when should we start affixing? (the amount of pixels to the top from the element)
            var fromTop = $(element).offset().top - delta,
            stopOn = $(document).height() - ($(bottomElement).offset().top)       // top pixel of the footer
              + ($(element).outerHeight() - $(element).height())                  // height calculation error
              - ($(window).outerHeight() - $(element).outerHeight() - 2 * delta); // amount of screenspace which is not used by the sticky element

            var offset = {
              top: fromTop
            };

            // minimum is zero (aka not used)
            if (stopOn > 0) {
              offset.bottom = stopOn;
            }

            // let's put a sticky width on the element and assign it to the top
            $(element).css('top', delta);
            // assign the affix to the element
            $(element).affix({
              offset: offset
                // when the affix get's called then make sure the position is the default (fixed) and it's at the top
            });

            // trigger the scroll event so it always activates
            $(window).trigger('scroll');
          } else {
            // WARNING: these lines destroys affix for all elements!
            // we are waiting for bootstrap to get their plugin
            // system into a usable state so that we can destroy
            // plugins cleanly
            $(window).off('scroll.bs.affix.data-api');
            $(window).off('click.bs.affix.data-api');

            $(element).removeData('bs.affix');
            window.setTimeout(function(){
              $(element).css('top', '');
              $(element).removeClass('affix affix-top affix-bottom');
            }, 10);
          }
        }, 100);
      });
      $(window).trigger('resize');
    });

  });
});
