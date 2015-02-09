/*
 * This file is part of Invenio.
 * Copyright (C) 2014, 2015 CERN.
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

var previewIframe = parent.document.getElementById('preview-iframe');
if (previewIframe) {
  var handleFullScreenClick = (function () {
    var isFullScreen = false;

    var pos = previewIframe.style.position,
        zIndex = previewIframe.style.zIndex,
        height = previewIframe.style.height,
        width = previewIframe.style.width,
        top = previewIframe.style.top,
        left = previewIframe.style.left,
        backgroundColor = previewIframe.style.backgroundColor;

    return function () {
      if (isFullScreen) {
        isFullScreen = false;
        previewIframe.style.position = pos;
        previewIframe.style.zIndex = zIndex;
        previewIframe.style.height = height;
        previewIframe.style.width = width;
        previewIframe.style.top = top;
        previewIframe.style.left = left;
        previewIframe.style.backgroundColor = backgroundColor;

        parent.document.body.style.overflow = ""
      } else {
        isFullScreen = true;
        previewIframe.style.position = "fixed";
        previewIframe.style.zIndex = 9999;
        previewIframe.style.height = "100%";
        previewIframe.style.width = "100%";
        previewIframe.style.top = 0;
        previewIframe.style.left = 0;
        previewIframe.style.backgroundColor="white";

        parent.document.body.style.overflow = "hidden"
      }
    }
  }());

  var fullScreenButton = previewIframe.contentDocument.getElementById('fullScreenMode');
  var secfullScreenButton = previewIframe.contentDocument.getElementById('secondaryFullScreenMode');
  if (fullScreenButton) fullScreenButton.addEventListener('click', handleFullScreenClick);
  if (secfullScreenButton) secfullScreenButton.addEventListener('click', handleFullScreenClick);
} else {
  var fullScreenButton = document.getElementById('fullScreenMode');
  var secfullScreenButton = document.getElementById('secondaryFullScreenMode');

  if (fullScreenButton) fullScreenButton.remove();
  if (secfullScreenButton) secfullScreenButton.remove();
}
