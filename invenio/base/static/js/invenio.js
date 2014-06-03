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

!function ($) {

  "use strict"; // jshint ;_;

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

  $(function() {

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
  });

}(window.jQuery);