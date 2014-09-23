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
'use strict';

/**
 * Presents current file list.
 *
 * @requires mustache/mustache
 * @requires templates/fileListRow.html
 *
 * @returns {Component} FileList
 */
define( function (require) {

    return require('flight/lib/component')(FileList);

    function FileList() {


      this.attributes({
        tableBodySelector: 'tbody',
        get_file_url: null
      });

      var fileListRow = require('hgn!../../templates/fileListRow');


      /**
       * Event handlers.
       */

      function handleFilesAddedToFileList(ev, files) {
        var that = this;
        var html = "";

        $.each(files, function (i, file) {
          var downloadable = (file.status === 5) ? true : false;
          html += fileListRow({
            file: file,
            downloadable: downloadable,
            get_file_url: that.attr.get_file_url
          });
        });

        this.select('tableBodySelector').append(html);
      }

      function handleFileProgressUpdatedOnFileList(ev, data) {
        var selector = "#"+data.file.id;
        $(this.$node.find('thead tr').children()[2]).html('Progress ' + data.upload_speed);
        $(this.$node.find(selector).children()[2]).children().children().css('width', data.file.percent.toString() + "%");
        $(this.$node.find(selector).children()[2]).children().children().html(data.file.percent.toString() + "%");
      }

      function handleItemClick(ev) {
        if (ev.target.id==="removeFile") {
          var fileId = ev.target.parentNode.parentNode.id;

          this.trigger('fileRemovedByUser', {
            fileId: fileId
          });
          ev.target.parentNode.parentNode.remove();
        }
      }

      function handleUploadCompleted(ev, files) {
        var that = this;
        $(this.$node.find('thead tr').children()[2]).html('Progress');
        $.each(files, function (key, file) {
          if (file.status === 5) {
            var selector = '#'+file.id;
            var $elem = $(that.$node.find(selector).children()[2]).children().children();
            $elem.css('width', file.percent.toString() + "%");
            $elem.html(file.percent.toString() + "%");
            $elem.removeClass('active progress-bar-info progress-bar-striped');
            $elem.addClass('progress-bar-default');
            $elem.children().css('display','inline');
          }
        });
      };

      function handleMouseOver(ev) {
        if (ev.target.id==="sortFile") {
          $( "#sortable" ).sortable( "enable" );
        }
      }

      function handleItemMouseUp(ev) {
        if (ev.target.id==="sortFile") {
          $( "#sortable" ).sortable( "disable" );
        }
      }

      this.after('initialize', function () {
        var that = this;
        $( "#sortable" ).sortable({ 
          forceHelperSize: true,
          forcePlaceholderSize: true,
          disabled: true,

          start: function (event, ui) {
            var header_ths = $("#uploader-filelist thead th"),
                item_tds = $(ui.helper).find("td");
            for(var i = 0; i < header_ths.length; i++){
              $(item_tds[i]).width($(header_ths[i]).width());
            }
            $(ui.placeholder).height(ui.item.height());
            $(ui.helper).width(ui.item.width());
          },

          update: function (event, ui) {
            that.trigger('fileListUpdated');
          }
        });
        $("#sortable").disableSelection();

        this.on('filesAddedToFileList', handleFilesAddedToFileList);
        this.on('fileProgressUpdatedOnFileList', handleFileProgressUpdatedOnFileList);
        this.on('uploadCompleted', handleUploadCompleted);
        this.on('click', handleItemClick);
        this.on('mouseover', handleMouseOver);
        this.on('mouseup', handleItemMouseUp);

      });


  }

});