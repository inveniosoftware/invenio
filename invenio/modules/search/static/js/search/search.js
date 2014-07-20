/*
 * This file is part of Invenio.
 * Copyright (C) 2014 CERN.
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


define(function(require, exports, module) {
    "use strict";
    var $ = require('jquery')

    module.exports = function(facets) {
        // side facet list
        var facet_list = $(facets.elem)

        $('#overlay').modal({
            keyboard: false,
            backdrop: 'static'
        }).modal('hide');

        if (facet_list.length && typeof facets !== undefined) {
            var parent = facet_list.closest('.container, .row'),
                popupTimer

            facet_list.affix({
                offset: {
                    top: function () {
                        return parent.offset().top
                    },
                    bottom: 170
                }
            })

            facet_list.facet({
                button_builder: function(title) {
                    return require('hgn!./templates/button')({
                        title: title
                    })
                },
                row_builder: function(data, name) {
                    var title = data[(data.length==3) ? 2 : 0],
                    counter = data[1]
                    return require('hgn!./templates/row')({
                        target: facets.elem,
                        key: name,
                        value: data[0],
                        title: title,
                        counter: counter
                    })
                },
                box_builder: function(name, title) {
                    return require('hgn!./templates/box')({
                        target: facets.elem,
                        key: name,
                        title: title
                    })
                },
                facets: facets.data
            }).on('updated', function(event) {
                var p = $('#facet_filter input[name=p]').val(),
                    facet = facet_list.data('facet')

                $('#search-box-main input[name=p]').val(p+' '+facet.queryString());

                var filter = JSON.stringify(facet.filter),
                    hash = decodeURIComponent(document.location.hash)
                if (filter != hash.substr(1)) {
                    if (filter != '[]') {
                        document.location.hash = encodeURIComponent(filter);
                    } else {
                        document.location.hash = '';
                    }
                }

                var showModal = true;
                var modalShow= function() {
                    if (showModal) {
                        $("#overlay").modal('show');
                    }
                };
                setTimeout(modalShow, 100);
                $.ajax(facets.searchResultsUrl, {
                    type: 'POST',
                    data: $.extend({}, facets.args, {filter: filter})
                }).done(function(data) {
                    $('#search_results').html(data);
                    showModal = false;
                    $("#overlay").modal('hide');
                });

            }).on('loaded', function(event) {

                var typeahead = $('form[name=search] input[name=p]').data('typeahead'),
                    facet = facet_list.data('facet')

                // Move out from library
                    var expand = jQuery.grep(facet.filter, function (a) {
                        return a[0] == '!'
                    })
                    $.each(expand, function(i,v) {
                        facet.$element.trigger($.Event('added', {op: v[0], key: v[1], value: v[2]}));
                    });

                    $('[data-facet="toggle"]')
                        .filter('[data-facet-key="'+event.name+'"]')
                        .addClass('muted').each(function(i) {

                            var toggle = $(this),
                                filterContent = $.proxy(function() {
                                    return facets.labels.action +
                                        require('hgn!./templates/action')({
                                        targe: facets.elem,
                                        key: this.data('facet-key'),
                                        value: this.data('facet-value'),
                                        title: facets.labels.exclude
                                    })
                                }, toggle)

                            toggle.popover({
                                html: true,
                                placement: 'right',
                                trigger: 'manual',
                                content: filterContent,
                                title: facets.labels.didyouknow
                            }).on('mouseenter', function() {
                                if (popupTimer) {
                                    clearTimeout(popupTimer)
                                }
                                popupTimer = setTimeout(function() {
                                    toggle.popover('show')
                                }, 2000)
                            }).on('click', function() {
                                if (popupTimer) {
                                    clearTimeout(popupTimer)
                                }
                                toggle.popover('hide')
                            }).parent().on('mouseleave', function() {
                                if (popupTimer) {
                                    clearTimeout(popupTimer)
                                }
                                toggle.popover('hide')
                            })

                        }).on('click', function(event) {
                            var $el_clicked = $(this),
                            options = facet_list.data('facet').options

                            if (!$el_clicked.hasClass('expandable') && $el_clicked.attr('data-facet-key') === 'collection') {
                                if ($el_clicked.parent().has('ul')) {
                                    var $ul = $el_clicked.parent().find('ul')
                                    $ul.each(function(i, ul) {
                                        $(this).find('[data-facet="toggle"]').each(function() {
                                            facet_list.data('facet').delete('+', $(this).attr('data-facet-key'), $(this).attr('data-facet-value'))
                                            facet_list.data('facet').delete('-', $(this).attr('data-facet-key'), $(this).attr('data-facet-value'))
                                        })
                                    })

                                    if ($el_clicked.hasClass('text-info') || $el_clicked.hasClass('text-danger')) {
                                        $ul.remove()
                                        $el_clicked.addClass('expandable')
                                        facet_list.data('facet').filter = facet_list.data('facet').exclude('!', $(this).attr('data-facet-key'), $(this).attr('data-facet-value'))
                                    }
                                }
                            }
                        })

                    // on hover add button in popover
                    //$('[data-facet="reset-key"]').addClass('text-info')

                    $('[data-facet="reset-key"]').each(function(e) {
                        $(this).on('click', function() {
                            $('[data-facet-key="'+ $(this).attr('data-facet-key') +'"]')
                            .attr('data-facet-action', '+')
                            .removeClass('text-danger')
                            .removeClass('text-info')
                            .css('font-weight', 'normal')
                            $(this).removeClass('muted').addClass('text-info')
                        })
                    })


                    $('#search_results').css('min-height', facet_list.height())
                    facet_list.affix('checkPosition');

                    // When we load data we should select facets from filter.
                    if (facet.findByKey(event.name).length > 0) {
                        facet.rebuildFilter(facet.filter)
                    }

            }).on('deleted', function(event) {

                $('[data-facet-key="'+event.key+'"]')
                .filter('[data-facet-value="'+event.value+'"]')
                .each(function(e) {
                    $(this)
                    .removeClass('text-danger')
                    .removeClass('text-info')
                    .css('font-weight', 'normal')
                    .attr('data-facet-action', '+')
                })

                var resetKey = false
                try {
                    if ($(this).data('facet').findByKey(event.key).length === 0) {
                        resetKey = true
                    }
                } catch(err) {
                    resetKey = true
                }
                if (resetKey) {
                    $('[data-facet="reset-key"]')
                    .filter('[data-facet-key="'+event.key+'"]')
                    .addClass('text-info')
                }

            }).on('added', function(event) {

                var type = (event.op == '+')?'info':'error',
                    other_type = (event.op == '-')?'info':'error'

                $('[data-facet-key="'+event.key+'"]')
                .filter('[data-facet-value="'+event.value+'"]')
                .each(function(e) {
                    if (event.op != '!') {
                        $(this)
                        .removeClass('text-'+other_type)
                        .addClass('text-'+type)
                        .css('font-weight', 'bold')
                    }
                })
                .filter('.expandable')
                .each(function() {

                    var $el_clicked = $(this),
                        options = facet_list.data('facet').options

                    $el_clicked.removeClass('expandable')

                    if (event.key === 'collection') {
                        $(this).parent().find('ul').remove()
                        var facet = {url: options.url_map[event.key],
                            facet: event.key},
                            data = {parent: event.value},
                            $ul = $('<ul class="context list-unstyled"><ul>').clone().appendTo($el_clicked.parent())

                        var data_facet = facet_list.data('facet')
                        if (data_facet.find('!', event.key, event.value).length === 0) {
                            data_facet.filter.push(['!', event.key, event.value])
                        }
                        data_facet.createFacetBox(facet, $ul, data)
                    }
                })

                $('[data-facet="reset-key"]')
                .filter('[data-facet-key="'+event.key+'"]')
                .removeClass('text-info')
                .addClass('muted')


            }).on('exists', function(event) {
                alert(facets.labels.alreadyin);
            });

            // Rebuild facet filter on hash change.
            $(window).bind('hashchange', function() {
                var hash = decodeURIComponent(document.location.hash),
                    hash_filter = hash.substr(1),
                    filter;

                try {
                    filter = $.parseJSON(hash_filter)
                } catch (exc) {
                    console.exception(exc)
                }

                if (typeof JSON === undefined || JSON.stringify(facet_list.data('facet').filter) != hash_filter) {
                    facet_list.data('facet').rebuildFilter(filter || [])
                }
            })

            // Parse hash URI component.
            if (document.location.hash.length > 2) {
                var hash = decodeURIComponent(document.location.hash),
                    hash_filter = hash.substr(1),
                    filter

                try {
                    filter = $.parseJSON(hash_filter)
                } catch (exc) {
                    console.exception(exc)
                }

                facet_list.data('facet').filter = filter || []
            }
        }
    }
})
