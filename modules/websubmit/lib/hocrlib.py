## This file is part of Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""hOCR parser and tools"""

from htmlentitydefs import entitydefs
import HTMLParser
import re
import os.path
from logging import info
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import green, red

_RE_PARSE_HOCR_BBOX = re.compile(r'\bbbox\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)')
_RE_CLEAN_SPACES = re.compile(r'\s+')
def extract_hocr(hocr_text):
    """
    Parse hocr_text and return a structure suitable to be used by create_pdf.
    """
    class HOCRReader(HTMLParser.HTMLParser):
        def __init__(self):
            HTMLParser.HTMLParser.__init__(self)
            self.lines = []
            self.bbox = None
            self.text = ""
            self.image = ''
            self.page_bbox = None
            self.pages = []
            self.started = False

        def store_current_page(self):
            if self.image:
                self.store_current_line()
                self.sort_current_lines()
                self.pages.append((self.page_bbox, self.image, self.lines))
                self.page_bbox = None
                self.image = ''
                self.lines = []

        def sort_current_lines(self):
            def line_cmp(a, b):
                y0_a = a[0][1]
                y0_b = b[0][1]
                return cmp(y0_b, y0_a)

            self.lines.sort(line_cmp)

        def store_current_line(self):
            if self.bbox:
                self.lines.append((self.bbox, _RE_CLEAN_SPACES.sub(' ', self.text).strip()))
                self.bbox = None
                self.text = ""

        def extract_hocr_properties(self, title):
            properties = title.split(';')
            ret = {}
            for prop in properties:
                prop = prop.strip()
                key, value = prop.split(' ', 1)
                key = key.strip().lower()
                value = value.strip()
                ret[key] = value
            return ret

        def handle_starttag(self, tag, attrs):
            attrs = dict(attrs)
            if attrs.get('class') == 'ocr_line':
                self.started = True
                self.store_current_line()
                properties = self.extract_hocr_properties(attrs.get('title', ''))
                try:
                    self.bbox = tuple(map(lambda x: int(x), properties['bbox'].split(' ', 4)))
                except:
                    ## If no bbox is retrievable, let's skip this line
                    pass
            elif attrs.get('class') == 'ocr_page':
                self.store_current_page()
                properties = self.extract_hocr_properties(attrs.get('title', ''))
                try:
                    self.page_bbox = tuple(map(lambda x: int(x), properties['bbox'].split(' ', 4)))
                except:
                    ## If no bbox is retrievable, let's skip this line
                    pass
                try:
                    self.image = os.path.abspath(properties['image'])
                except:
                    pass

        def handle_entityref(self, name):
            if self.started and name in entitydefs:
                self.text += entitydefs[name].decode('latin1').encode('utf8')

        def handle_data(self, data):
            if self.started and data.strip():
                self.text += data

        def handle_charref(self, data):
            if self.started:
                try:
                    self.text += unichr(int(data)).encode('utf8')
                except:
                    pass

        def close(self):
            HTMLParser.HTMLParser.close(self)
            self.store_current_page()

    hocr_reader = HOCRReader()
    hocr_reader.feed(hocr_text)
    hocr_reader.close()
    return hocr_reader.pages

def create_pdf(hocr, filename, font="Courier", author=None, keywords=None, subject=None, title=None, image_path=None, draft=False):
    """ transform hOCR information into a searchable PDF.
    @param hocr the hocr structure as coming from extract_hocr.
    @param filename the name of the PDF generated in output.
    @param font the default font (e.g. Courier, Times-Roman).
    @param author the author name.
    @param subject the subject of the document.
    @param title the title of the document.
    @param image_path the default path where images are stored. If not specified
           relative image paths will be resolved to the current directory.
    @param draft whether to enable debug information in the output.

    """
    def adjust_image_size(width, height):
        return max(width / A4[0], height / A4[1])

    canvas = Canvas(filename)

    if author:
        canvas.setAuthor(author)

    if keywords:
        canvas.setKeywords(keywords)

    if title:
        canvas.setTitle(title)

    if subject:
        canvas.setSubject(subject)

    for bbox, image, lines in hocr:
        if not image.startswith('/') and image_path:
            image = os.path.abspath(os.path.join(image_path, image))
        img_width, img_height = bbox[2:]
        ratio = adjust_image_size(img_width, img_height)
        if draft:
            canvas.drawImage(image, 0, A4[1] - img_height / ratio , img_width / ratio, img_height / ratio)
        canvas.setFont(font, 12)
        for bbox, line in lines:
            if draft:
                canvas.setFillColor(red)
            x0, y0, x1, y1 = bbox
            width = (x1 - x0) / ratio
            height = ((y1 - y0) / ratio)
            x0 = x0 / ratio
            #for ch in 'gjpqy,(){}[];$@':
                #if ch in line:
                    #y0 = A4[1] - (y0 / ratio) - height
                    #break
            #else:
            y0 = A4[1] - (y0 / ratio) - height / 1.3
            #canvas.setFontSize(height * 1.5)
            canvas.setFontSize(height)
            text_width = canvas.stringWidth(line)
            if text_width:
                ## If text_width != 0
                text_object = canvas.beginText(x0, y0)
                text_object.setHorizScale(1.0 * width / text_width * 100)
                text_object.textOut(line)
                canvas.drawText(text_object)
            else:
                info('%s, %s has width 0' % (bbox, line))
            if draft:
                canvas.setStrokeColor(green)
                canvas.rect(x0, y0, width, height)
        if draft:
            canvas.circle(0, 0, 10, fill=1)
            canvas.circle(0, A4[1], 10, fill=1)
            canvas.circle(A4[0], 0, 10, fill=1)
            canvas.circle(A4[0], A4[1], 10, fill=1)
            canvas.setFillColor(green)
            canvas.setStrokeColor(green)
            canvas.circle(0, A4[1] - img_height / ratio, 5, fill=1)
            canvas.circle(img_width / ratio, img_height /ratio, 5, fill=1)
        else:
            canvas.drawImage(image, 0, A4[1] - img_height / ratio , img_width / ratio, img_height / ratio)

        canvas.save()

