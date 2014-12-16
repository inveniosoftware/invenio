/**
This file is part of Invenio.
Copyright (C) 2014 CERN.

Invenio is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License as
published by the Free Software Foundation; either version 2 of the
License, or (at your option) any later version.

Invenio is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License
along with Invenio; if not, write to the Free Software Foundation, Inc.,
59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
**/

'use strict';

/* global console */
/* exported ANNOTATIONS */

var ANNOTATIONS = (function($) {
    function fillTab(event) {
        event.preventDefault();
        var url = $(event.target).attr('href');
        $.ajax({
            type: 'GET',
            url: url,
            data: {target: window.location.pathname},
            success: function(data) {
                $('#modal-body').html(data);
                $(document).trigger('anno_menu_tab_done', url);
            }
        });
    }

    $(document).on('anno_menu_tab_done', function() {
        if(typeof OPTION !== 'undefined' && OPTION === 'private') {
            $('#private_anno_btn').trigger('click');
        }
    });

    function submitForm(event) {
        event.preventDefault();
        $.ajax({
            type: 'POST',
            data: $('#write-annotation').serialize(),
            url: $('#write-annotation').attr('action'),
            success: function(data) {
                $('#modal-body').html(data);
            },
            error: function() {
                console.log('error');
            }
        });
    }

    function getAnnoCount() {
        $.ajax({
            type: 'GET',
            url: '/annotations/get_count',
            success: function(data) {
                $("#anno_count").html('(' + data.total + ')');
            },
            error: function() {
                console.log('error');
            }
        });
    }

    function switchView(target) {
        target = $(target)
        switch(target.attr('id')) {
        case 'private_anno_btn':
            $('#public_anno').hide();
            $('#private_anno').show();
            return;
        case 'public_anno_btn':
            $('#public_anno').show();
            $('#private_anno').hide();
            return;
        }
    }

    $(document).ready(function() {
        getAnnoCount();
    });

    return {
        fillTab: fillTab,
        submitForm: submitForm,
        switchView: switchView
    };
})(window.jQuery);
