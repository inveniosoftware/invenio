 /*
 * This file is part of Invenio.
 * Copyright (C) 2013, 2014 CERN.
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

define(['jquery', 'prism', "js/workflows/hp_utilities"], function($, Prism, utilities) {
    var context = {},
        format = "hd",
        bwoid;

    function data_preview(url_preview, bwoid, format) {
        $.ajax({
            url: url_preview,
            data: {'objectid': bwoid,
                   'of': format},
            success: function (json) {
                if (format === "xm" || format === "xo") {
                    if (json.data === "") {
                        json.data = "Preview not available";
                    }
                    $('div[id="object_preview_container' + bwoid + '"]').empty();
                    $('div[id="object_preview_container' + bwoid + '"]').append("<pre><code id='object_preview' class='language-markup'></code></pre>");
                    $('code[id="object_preview"]').append(json.data);
                    Prism.highlightElement($('code[id="object_preview"]')[0]);
                } else {
                    if (json.data === "") {
                        json.data = "Preview not available";
                    }
                    $('div[id="object_preview_container' + bwoid + '"]').empty();
                    $('div[id="object_preview_container' + bwoid + '"]').append(json.data);
                }
            }
        });
    }

    return {
        bwoid: bwoid,
        data_preview: data_preview,
        init: function (context, bwoid) {
            if (window.addEventListener) {
                $("div.btn-group[name='data_version']").bind('click', function(event){
                    version = event.target.name;
                });
            }

            this.bwoid = bwoid;
            this.data_preview(context.holdingpen.url_preview,
                              bwoid,
                              format);

            $('button.preview').click(function () {
                var format = $(this).attr('name');
                data_preview(context.holdingpen.url_preview, bwoid, format);
                $('button.preview').each(function () {
                    $(this).removeClass('active');
                });
                $(this).addClass('active');
            });

            $('#restart_button').on('click', function () {
                $.ajax({
                    url: context.holdingpen.url_restart_record,
                    data: {'objectid': this.bwoid},
                    success: function (json) {
                        utilities.bootstrap_alert('Object restarted', 'info');
                    }
                });
            });

            $('#restart_button_prev').on('click', function () {
                $.ajax({
                    url: context.holdingpen.url_restart_record_prev,
                    data: {'objectid': this.bwoid},
                    success: function (json) {
                        utilities.bootstrap_alert('Object restarted from previous task', 'info');
                    }
                });
            });

            $('#continue_button').on('click', function () {
                $.ajax({
                    url: context.holdingpen.url_continue,
                    data: {'objectid': this.bwoid},
                    success: function (json) {
                        utilities.bootstrap_alert('Object continued from next task', 'info');
                    }
                });
            });

            $('#edit_form').on('submit', function (event) {
                event.preventDefault();
                var form_data = {};
                $("#edit_form input").each(function () {
                    if ($(this)[0].name !== 'submitButton') {
                        if ($(this)[0].name === 'core') {
                            form_data[$(this)[0].name] = $(this)[0].checked;
                        } else {
                            form_data[$(this)[0].name] = $(this)[0].value;
                        }
                    }
                });

                $.ajax({
                    type: 'POST',
                    url: context.holdingpen.url_resolve_edit,
                    data: {'objectid': this.bwoid,
                           'data': form_data},
                    success: function (json) {
                        utilities.bootstrap_alert('Record successfully edited', 'info');
                    }
                });
            });
        }
    };
});
