# -*- coding: utf-8 -*-
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

"""
This module implement fulltext conversion between many different file formats.
"""

import os
import re
import sys
import shutil
import tempfile
import HTMLParser
import time

from logging import debug, error, DEBUG, getLogger
from htmlentitydefs import entitydefs
from optparse import OptionParser

try:
    from invenio.hocrlib import create_pdf, extract_hocr
    CFG_HAS_REPORTLAB = True
except ImportError:
    CFG_HAS_REPORTLAB = False

from invenio.shellutils import run_process_with_timeout
from invenio.config import CFG_TMPDIR, CFG_ETCDIR, CFG_PYLIBDIR, \
    CFG_PATH_ANY2DJVU, \
    CFG_PATH_PDFINFO, \
    CFG_PATH_GS, \
    CFG_PATH_PDFOPT, \
    CFG_PATH_PDFTOPS, \
    CFG_PATH_GZIP, \
    CFG_PATH_GUNZIP, \
    CFG_PATH_PDFTOTEXT, \
    CFG_PATH_PDFTOPPM, \
    CFG_PATH_OCROSCRIPT, \
    CFG_PATH_DJVUPS, \
    CFG_PATH_DJVUTXT, \
    CFG_PATH_OPENOFFICE_PYTHON, \
    CFG_PATH_PSTOTEXT, \
    CFG_PATH_TIFF2PDF, \
    CFG_OPENOFFICE_SERVER_HOST, \
    CFG_OPENOFFICE_SERVER_PORT, \
    CFG_OPENOFFICE_USER, \
    CFG_PATH_CONVERT, \
    CFG_PATH_PAMFILE

from invenio.websubmit_config import \
    CFG_WEBSUBMIT_BEST_FORMATS_TO_EXTRACT_TEXT_FROM, \
    CFG_WEBSUBMIT_DESIRED_CONVERSIONS
from invenio.errorlib import register_exception

#logger = getLogger()
#logger.setLevel(DEBUG)

CFG_TWO2THREE_LANG_CODES = {
    'en': 'eng',
    'nl': 'nld',
    'es': 'spa',
    'de': 'deu',
    'it': 'ita',
    'fr': 'fra',
}

CFG_OPENOFFICE_TMPDIR = os.path.join(CFG_TMPDIR, 'ooffice-tmp-files')

_RE_CLEAN_SPACES = re.compile(r'\s+')


class InvenioWebSubmitFileConverterError(Exception):
    pass


def get_conversion_map():
    """Return a dictionary of the form:
    '.pdf' : {'.ps.gz' : ('pdf2ps', {param1 : value1...})
    """
    ret = {
        '.csv': {},
        '.djvu': {},
        '.doc': {},
        '.docx': {},
        '.htm': {},
        '.html': {},
        '.odp': {},
        '.ods': {},
        '.odt': {},
        '.pdf': {},
        '.ppt': {},
        '.pptx': {},
        '.ps': {},
        '.ps.gz': {},
        '.rtf': {},
        '.tif': {},
        '.tiff': {},
        '.txt': {},
        '.xls': {},
        '.xlsx': {},
        '.xml': {},
        '.hocr': {},
    }
    if CFG_PATH_GZIP:
        ret['.ps']['.ps.gz'] = (gzip, {})
    if CFG_PATH_GUNZIP:
        ret['.ps.gz']['.ps'] = (gunzip, {})
    if CFG_PATH_ANY2DJVU:
        ret['.pdf']['.djvu'] = (any2djvu, {})
        ret['.ps']['.djvu'] = (any2djvu, {})
        ret['.ps.gz']['.djvu'] = (any2djvu, {})
    if CFG_PATH_DJVUPS:
        ret['.djvu']['.ps'] = (djvu2ps, {'compress': False})
        if CFG_PATH_GZIP:
            ret['.djvu']['.ps.gz'] = (djvu2ps, {'compress': True})
    if CFG_PATH_DJVUTXT:
        ret['.djvu']['.txt'] = (djvu2text, {})
    if CFG_PATH_PSTOTEXT:
        ret['.ps']['.txt'] = (pstotext, {})
        if CFG_PATH_GUNZIP:
            ret['.ps.gz']['.txt'] = (pstotext, {})
    if CFG_PATH_GS:
        ret['.ps']['.pdf'] = (ps2pdfa, {})
        if CFG_PATH_GUNZIP:
            ret['.ps.gz']['.pdf'] = (ps2pdfa, {})
    if CFG_PATH_PDFTOPS:
        ret['.pdf']['.ps'] = (pdf2ps, {'compress': False})
        if CFG_PATH_GZIP:
            ret['.pdf']['.ps.gz'] = (pdf2ps, {'compress': True})
    if CFG_PATH_PDFTOTEXT:
        ret['.pdf']['.txt'] = (pdf2text, {})
    if CFG_PATH_PDFTOPPM and CFG_PATH_OCROSCRIPT and CFG_PATH_PAMFILE:
        ret['.pdf']['.hocr'] = (pdf2hocr, {})
    if CFG_PATH_PDFTOPS and CFG_PATH_GS and CFG_PATH_PDFOPT and CFG_PATH_PDFINFO:
        ret['.pdf']['.pdf'] = (pdf2pdfa, {})
    ret['.txt']['.txt'] = (txt2text, {})
    ret['.csv']['.txt'] = (txt2text, {})
    ret['.html']['.txt'] = (html2text, {})
    ret['.htm']['.txt'] = (html2text, {})
    ret['.xml']['.txt'] = (html2text, {})
    if CFG_HAS_REPORTLAB:
        ret['.hocr']['.pdf'] = (hocr2pdf, {})
    if CFG_PATH_TIFF2PDF:
        ret['.tiff']['.pdf'] = (tiff2pdf, {})
        ret['.tif']['.pdf'] = (tiff2pdf, {})
    if CFG_PATH_OPENOFFICE_PYTHON and CFG_OPENOFFICE_SERVER_HOST:
        ret['.rtf']['.odt'] = (unoconv, {'output_format': 'odt'})
        ret['.rtf']['.doc'] = (unoconv, {'output_format': 'doc'})
        ret['.rtf']['.pdf'] = (unoconv, {'output_format': 'pdf'})
        ret['.rtf']['.txt'] = (unoconv, {'output_format': 'text'})
        ret['.doc']['.odt'] = (unoconv, {'output_format': 'odt'})
        ret['.doc']['.pdf'] = (unoconv, {'output_format': 'pdf'})
        ret['.doc']['.txt'] = (unoconv, {'output_format': 'text'})
        ret['.docx']['.odt'] = (unoconv, {'output_format': 'odt'})
        ret['.docx']['.doc'] = (unoconv, {'output_format': 'doc'})
        ret['.docx']['.pdf'] = (unoconv, {'output_format': 'pdf'})
        ret['.docx']['.txt'] = (unoconv, {'output_format': 'text'})
        ret['.odt']['.doc'] = (unoconv, {'output_format': 'doc'})
        ret['.odt']['.pdf'] = (unoconv, {'output_format': 'pdf'})
        ret['.odt']['.txt'] = (unoconv, {'output_format': 'text'})
        ret['.ppt']['.odp'] = (unoconv, {'output_format': 'odp'})
        ret['.ppt']['.pdf'] = (unoconv, {'output_format': 'pdf'})
        ret['.ppt']['.txt'] = (unoconv, {'output_format': 'text'})
        ret['.pptx']['.odp'] = (unoconv, {'output_format': 'odp'})
        ret['.pptx']['.ppt'] = (unoconv, {'output_format': 'ppt'})
        ret['.pptx']['.pdf'] = (unoconv, {'output_format': 'pdf'})
        ret['.pptx']['.txt'] = (unoconv, {'output_format': 'text'})
        ret['.odp']['.ppt'] = (unoconv, {'output_format': 'ppt'})
        ret['.odp']['.pdf'] = (unoconv, {'output_format': 'pdf'})
        ret['.odp']['.txt'] = (unoconv, {'output_format': 'text'})
        ret['.xls']['.ods'] = (unoconv, {'output_format': 'ods'})
        ret['.xls']['.pdf'] = (unoconv, {'output_format': 'pdf'})
        ret['.xls']['.txt'] = (unoconv, {'output_format': 'text'})
        ret['.xls']['.csv'] = (unoconv, {'output_format': 'csv'})
        ret['.xlsx']['.xls'] = (unoconv, {'output_format': 'xls'})
        ret['.xlsx']['.ods'] = (unoconv, {'output_format': 'ods'})
        ret['.xlsx']['.pdf'] = (unoconv, {'output_format': 'pdf'})
        ret['.xlsx']['.txt'] = (unoconv, {'output_format': 'text'})
        ret['.xlsx']['.csv'] = (unoconv, {'output_format': 'csv'})
        ret['.ods']['.xls'] = (unoconv, {'output_format': 'xls'})
        ret['.ods']['.pdf'] = (unoconv, {'output_format': 'pdf'})
        ret['.ods']['.txt'] = (unoconv, {'output_format': 'text'})
        ret['.ods']['.csv'] = (unoconv, {'output_format': 'csv'})
    return ret


def get_best_format_to_extract_text_from(filelist, best_formats=CFG_WEBSUBMIT_BEST_FORMATS_TO_EXTRACT_TEXT_FROM):
    """
    Return among the filelist the best file whose format is best suited for
    extracting text.
    """
    from invenio.bibdocfile import decompose_file, normalize_format
    best_formats = [normalize_format(aformat) for aformat in best_formats if can_convert(aformat, '.txt')]
    for aformat in best_formats:
        for filename in filelist:
            if decompose_file(filename, skip_version=True)[2].endswith(aformat):
                return filename
    raise InvenioWebSubmitFileConverterError("It's not possible to extract valuable text from any of the proposed files.")


def get_missing_formats(filelist, desired_conversion=None):
    """Given a list of files it will return a dictionary of the form:
    file1 : missing formats to generate from it...
    """
    from invenio.bibdocfile import normalize_format, decompose_file

    def normalize_desired_conversion():
        ret = {}
        for key, value in desired_conversion.iteritems():
            ret[normalize_format(key)] = [normalize_format(aformat) for aformat in value]
        return ret

    if desired_conversion is None:
        desired_conversion = CFG_WEBSUBMIT_DESIRED_CONVERSIONS

    available_formats = [decompose_file(filename, skip_version=True)[2] for filename in filelist]
    missing_formats = []
    desired_conversion = normalize_desired_conversion()
    ret = {}
    for filename in filelist:
        aformat = decompose_file(filename, skip_version=True)[2]
        if aformat in desired_conversion:
            for desired_format in desired_conversion[aformat]:
                if desired_format not in available_formats and desired_format not in missing_formats:
                    missing_formats.append(desired_format)
                    if filename not in ret:
                        ret[filename] = []
                    ret[filename].append(desired_format)
    return ret


def can_convert(input_format, output_format, max_intermediate_conversions=2):
    """Return the chain of conversion to transform input_format into output_format, if any."""
    from invenio.bibdocfile import normalize_format
    if max_intermediate_conversions <= 0:
        return []
    input_format = normalize_format(input_format)
    output_format = normalize_format(output_format)
    if input_format in __CONVERSION_MAP:
        if output_format in __CONVERSION_MAP[input_format]:
            return [__CONVERSION_MAP[input_format][output_format]]
        best_res = []
        best_intermediate = ''
        for intermediate_format in __CONVERSION_MAP[input_format]:
            res = can_convert(intermediate_format, output_format, max_intermediate_conversions-1)
            if res and (len(res) < best_res or not best_res):
                best_res = res
                best_intermediate = intermediate_format
        if best_res:
            return [__CONVERSION_MAP[input_format][best_intermediate]] + best_res
    return []


def can_pdfopt():
    """Return True if it's possible to optimize PDFs."""
    return bool(CFG_PATH_PDFOPT)


def can_pdfa():
    """Return True if it's possible to generate PDF/As."""
    return bool(CFG_PATH_PDFTOPS and CFG_PATH_GS and CFG_PATH_PDFINFO)


def can_perform_ocr():
    """Return True if it's possible to perform OCR."""
    return bool(CFG_PATH_OCROSCRIPT) and bool(CFG_PATH_PDFTOPPM)


def guess_ocropus_produced_garbage(input_file, hocr_p):
    """Return True if the output produced by OCROpus in hocr format contains
    only garbage instead of text. This is implemented via an heuristic:
    if the most common length for sentences encoded in UTF-8 is 1 then
    this is Garbage (tm).
    """

    def _get_words_from_text():
        ret = []
        for row in open(input_file):
            for word in row.strip().split(' '):
                ret.append(word.strip())
        return ret

    def _get_words_from_hocr():
        ret = []
        hocr = extract_hocr(open(input_file).read())
        for dummy, dummy, lines in hocr:
            for dummy, line in lines:
                for word in line.split():
                    ret.append(word.strip())
        return ret

    if hocr_p:
        words = _get_words_from_hocr()
    else:
        words = _get_words_from_text()
    #stats = {}
    #most_common_len = 0
    #most_common_how_many = 0
    #for word in words:
        #if word:
            #word_length = len(word.decode('utf-8'))
            #stats[word_length] = stats.get(word_length, 0) + 1
            #if stats[word_length] > most_common_how_many:
                #most_common_len = word_length
                #most_common_how_many = stats[word_length]
    goods = 0
    bads = 0
    for word in words:
        for char in word.decode('utf-8'):
            if (u'a' <= char <= u'z') or (u'A' <= char <= u'Z'):
                goods += 1
            else:
                bads += 1
    if bads > goods:
        debug('OCROpus produced garbage')
        return True
    else:
        return False


def guess_is_OCR_needed(input_file, ln='en'):
    """
    Tries to see if enough text is retrievable from input_file.
    Return True if OCR is needed, False if it's already
    possible to retrieve information from the document.
    """
    ## FIXME: a way to understand if pdftotext has returned garbage
    ## shuould be found. E.g. 1.0*len(text)/len(zlib.compress(text)) < 2.1
    ## could be a good hint for garbage being found.
    return True


def convert_file(input_file, output_file=None, output_format=None, **params):
    """
    Convert files from one format to another.
    @param input_file [string] the path to an existing file
    @param output_file [string] the path to the desired ouput. (if None a
        temporary file is generated)
    @param output_format [string] the desired format (if None it is taken from
        output_file)
    @param params other paramaters to pass to the particular converter
    @return [string] the final output_file
    """
    from invenio.bibdocfile import decompose_file, normalize_format
    if output_format is None:
        if output_file is None:
            raise ValueError("At least output_file or format should be specified.")
        else:
            output_ext = decompose_file(output_file, skip_version=True)[2]
    else:
        output_ext = normalize_format(output_format)
    input_ext = decompose_file(input_file, skip_version=True)[2]
    conversion_chain = can_convert(input_ext, output_ext)
    if conversion_chain:
        current_input = input_file
        current_output = None
        for i in xrange(len(conversion_chain)):
            if i == (len(conversion_chain) - 1):
                current_output = output_file
            converter = conversion_chain[i][0]
            final_params = dict(conversion_chain[i][1])
            final_params.update(params)
            try:
                return converter(current_input, current_output, **final_params)
            except InvenioWebSubmitFileConverterError, err:
                raise InvenioWebSubmitFileConverterError("Error when converting from %s to %s: %s" % (input_file, output_ext, err))
            except Exception, err:
                register_exception()
                raise InvenioWebSubmitFileConverterError("Unexpected error when converting from %s to %s (%s): %s" % (input_file, output_ext, type(err), err))
            current_input = current_output
    else:
        raise InvenioWebSubmitFileConverterError("It's impossible to convert from %s to %s" % (input_ext, output_ext))


def check_openoffice_tmpdir():
    """Return True if OpenOffice tmpdir do exists and OpenOffice can
    successfully create file there."""
    if not os.path.exists(CFG_OPENOFFICE_TMPDIR):
        raise InvenioWebSubmitFileConverterError('%s does not exists' % CFG_OPENOFFICE_TMPDIR)
    if not os.path.isdir(CFG_OPENOFFICE_TMPDIR):
        raise InvenioWebSubmitFileConverterError('%s is not a directory' % CFG_OPENOFFICE_TMPDIR)
    now = str(time.time())
    execute_command('sudo', '-u', CFG_OPENOFFICE_USER, CFG_PATH_OPENOFFICE_PYTHON, '-c', 'import os; open(os.path.join(%s, "test"), "w").write(%s)' % (repr(CFG_OPENOFFICE_TMPDIR), repr(now)))
    try:
        test = open(os.path.join(CFG_OPENOFFICE_TMPDIR, 'test')).read()
        if test != now:
            raise IOError
    except:
        raise InvenioWebSubmitFileConverterError("%s can't be properly written by OpenOffice.org or read by Apache" % CFG_OPENOFFICE_TMPDIR)


def unoconv(input_file, output_file=None, output_format='txt', pdfopt=True, **dummy):
    """Use unconv to convert among OpenOffice understood documents."""
    from invenio.bibdocfile import normalize_format
    try:
        check_openoffice_tmpdir()
    except InvenioWebSubmitFileConverterError, err:
        register_exception(alert_admin=True, prefix='ERROR: it\'s impossible to properly execute OpenOffice.org conversions: %s' % err)
        raise

    input_file, output_file, dummy = prepare_io(input_file, output_file, output_format, need_working_dir=False)
    if output_format == 'txt':
        unoconv_format = 'text'
    else:
        unoconv_format = output_format
    try:
        tmpfile = tempfile.mktemp(dir=CFG_OPENOFFICE_TMPDIR, suffix=normalize_format(output_format))
        execute_command('sudo', '-u', CFG_OPENOFFICE_USER, CFG_PATH_OPENOFFICE_PYTHON, os.path.join(CFG_PYLIBDIR, 'invenio', 'unoconv.py'), '-v', '-s', CFG_OPENOFFICE_SERVER_HOST, '-p', CFG_OPENOFFICE_SERVER_PORT, '--outputfile', tmpfile, '-f', unoconv_format, input_file)
    except InvenioWebSubmitFileConverterError:
        time.sleep(5)
        execute_command('sudo', '-u', CFG_OPENOFFICE_USER, CFG_PATH_OPENOFFICE_PYTHON, os.path.join(CFG_PYLIBDIR, 'invenio', 'unoconv.py'), '-v', '-s', CFG_OPENOFFICE_SERVER_HOST, '-p', CFG_OPENOFFICE_SERVER_PORT, '--outputfile', tmpfile, '-f', unoconv_format, input_file)

    if not os.path.exists(tmpfile):
        raise InvenioWebSubmitFileConverterError('No output was generated by OpenOffice')

    output_format = normalize_format(output_format)

    if output_format == '.pdf' and pdfopt:
        pdf2pdfopt(tmpfile, output_file)
    else:
        shutil.copy(tmpfile, output_file)
    execute_command('sudo', '-u', CFG_OPENOFFICE_USER, CFG_PATH_OPENOFFICE_PYTHON, '-c', 'import os; os.remove(%s)' % repr(tmpfile))
    return output_file


def any2djvu(input_file, output_file=None, resolution=400, ocr=True, input_format=5, **dummy):
    """
    Transform input_file into a .djvu file.
    @param input_file [string] the input file name
    @param output_file [string] the output_file file name, None for temporary generated
    @param resolution [int] the resolution of the output_file
    @param input_format [int] [1-9]:
        1 - DjVu Document (for verification or OCR)
        2 - PS/PS.GZ/PDF Document (default)
        3 - Photo/Picture/Icon
        4 - Scanned Document - B&W - <200 dpi
        5 - Scanned Document - B&W - 200-400 dpi
        6 - Scanned Document - B&W - >400 dpi
        7 - Scanned Document - Color/Mixed - <200 dpi
        8 - Scanned Document - Color/Mixed - 200-400 dpi
        9 - Scanned Document - Color/Mixed - >400 dpi
    @return [string] output_file input_file.
    raise InvenioWebSubmitFileConverterError in case of errors.
    Note: due to the bottleneck of using a centralized server, it is very
    slow and is not suitable for interactive usage (e.g. WebSubmit functions)
    """
    from invenio.bibdocfile import decompose_file
    input_file, output_file, working_dir = prepare_io(input_file, output_file, '.djvu')

    ocr = ocr and "1" or "0"

    ## Any2djvu expect to find the file in the current directory.
    execute_command(CFG_PATH_ANY2DJVU, '-a', '-c', '-r', resolution, '-o', ocr, '-f', input_format, os.path.basename(input_file), cwd=working_dir)

    ## Any2djvu doesn't let you choose the output_file file name.
    djvu_output = os.path.join(working_dir, decompose_file(input_file)[1] + '.djvu')
    shutil.move(djvu_output, output_file)
    clean_working_dir(working_dir)
    return output_file


_RE_FIND_TITLE = re.compile(r'^Title:\s*(.*?)\s*$')


def pdf2pdfa(input_file, output_file=None, title=None, pdfopt=True, **dummy):
    """
    Transform any PDF into a PDF/A (see: <http://www.pdfa.org/>)
    @param input_file [string] the input file name
    @param output_file [string] the output_file file name, None for temporary generated
    @param title [string] the title of the document. None for autodiscovery.
    @param pdfopt [bool] whether to linearize the pdf, too.
    @return [string] output_file input_file
    raise InvenioWebSubmitFileConverterError in case of errors.
    """

    input_file, output_file, working_dir = prepare_io(input_file, output_file, '.pdf')

    if title is None:
        stdout = execute_command(CFG_PATH_PDFINFO, input_file)
        for line in stdout.split('\n'):
            g = _RE_FIND_TITLE.match(line)
            if g:
                title = g.group(1)
                break
    if not title:
        title = 'No title'

    debug("Extracted title is %s" % title)

    shutil.copy(os.path.join(CFG_ETCDIR, 'websubmit', 'file_converter_templates', 'ISOCoatedsb.icc'), working_dir)
    pdfa_header = open(os.path.join(CFG_ETCDIR, 'websubmit', 'file_converter_templates', 'PDFA_def.ps')).read()
    pdfa_header = pdfa_header.replace('<<<<TITLEMARKER>>>>', title)
    inputps = os.path.join(working_dir, 'input.ps')
    outputpdf = os.path.join(working_dir, 'output_file.pdf')
    open(os.path.join(working_dir, 'PDFA_def.ps'), 'w').write(pdfa_header)
    execute_command(CFG_PATH_PDFTOPS, '-level3', input_file, inputps)
    execute_command(CFG_PATH_GS, '-sProcessColorModel=DeviceCMYK', '-dPDFA', '-dBATCH', '-dNOPAUSE', '-dNOOUTERSAVE', '-dUseCIEColor', '-sDEVICE=pdfwrite', '-sOutputFile=output_file.pdf', 'PDFA_def.ps', 'input.ps', cwd=working_dir)
    if pdfopt:
        execute_command(CFG_PATH_PDFOPT, outputpdf, output_file)
    else:
        shutil.move(outputpdf, output_file)
    clean_working_dir(working_dir)
    return output_file


def pdf2pdfopt(input_file, output_file=None, **dummy):
    """
    Linearize the input PDF in order to improve the web-experience when
    visualizing the document through the web.
    @param input_file [string] the input input_file
    @param output_file [string] the output_file file name, None for temporary generated
    @return [string] output_file input_file
    raise InvenioWebSubmitFileConverterError in case of errors.
    """
    input_file, output_file, dummy = prepare_io(input_file, output_file, '.pdf', need_working_dir=False)
    execute_command(CFG_PATH_PDFOPT, input_file, output_file)
    return output_file


def pdf2ps(input_file, output_file=None, level=2, compress=True, **dummy):
    """
    Convert from Pdf to Postscript.
    """
    if compress:
        suffix = '.ps.gz'
    else:
        suffix = '.ps'
    input_file, output_file, working_dir = prepare_io(input_file, output_file, suffix)
    execute_command(CFG_PATH_PDFTOPS, '-level%i' % level, input_file, os.path.join(working_dir, 'output.ps'))
    if compress:
        execute_command(CFG_PATH_GZIP, '-c', os.path.join(working_dir, 'output.ps'), filename_out=output_file)
    else:
        shutil.move(os.path.join(working_dir, 'output.ps'), output_file)
    clean_working_dir(working_dir)
    return output_file


def ps2pdfa(input_file, output_file=None, title=None, pdfopt=True, **dummy):
    """
    Transform any PS into a PDF/A (see: <http://www.pdfa.org/>)
    @param input_file [string] the input file name
    @param output_file [string] the output_file file name, None for temporary generated
    @param title [string] the title of the document. None for autodiscovery.
    @param pdfopt [bool] whether to linearize the pdf, too.
    @return [string] output_file input_file
    raise InvenioWebSubmitFileConverterError in case of errors.
    """

    input_file, output_file, working_dir = prepare_io(input_file, output_file, '.pdf')
    if not title:
        title = 'No title'

    shutil.copy(os.path.join(CFG_ETCDIR, 'websubmit', 'file_converter_templates', 'ISOCoatedsb.icc'), working_dir)
    pdfa_header = open(os.path.join(CFG_ETCDIR, 'websubmit', 'file_converter_templates', 'PDFA_def.ps')).read()
    pdfa_header = pdfa_header.replace('<<<<TITLEMARKER>>>>', title)
    outputpdf = os.path.join(working_dir, 'output_file.pdf')
    open(os.path.join(working_dir, 'PDFA_def.ps'), 'w').write(pdfa_header)
    execute_command(CFG_PATH_GS, '-sProcessColorModel=DeviceCMYK', '-dPDFA', '-dBATCH', '-dNOPAUSE', '-dNOOUTERSAVE', '-dUseCIEColor', '-sDEVICE=pdfwrite', '-sOutputFile=output_file.pdf', 'PDFA_def.ps', input_file, cwd=working_dir)
    if pdfopt:
        execute_command(CFG_PATH_PDFOPT, outputpdf, output_file)
    else:
        shutil.move(outputpdf, output_file)
    clean_working_dir(working_dir)
    return output_file


def pdf2hocr(input_file, output_file=None, ln='en', return_working_dir=False, extract_only_text=False, **dummy):
    """
    Return the text content in input_file.
    @param ln is a two letter language code to give the OCR tool a hint.
    @param return_working_dir if set to True, will return output_file path and the working_dir path, instead of deleting the working_dir. This is useful in case you need the intermediate images to build again a PDF.
    """

    def _perform_rotate(working_dir, imagefile, angle):
        """Rotate imagefile of the corresponding angle. Creates a new file
        with rotated- as prefix."""
        debug('Performing rotate on %s by %s degrees' % (imagefile, angle))
        if not angle:
            #execute_command('%s %s %s', CFG_PATH_CONVERT, os.path.join(working_dir, imagefile), os.path.join(working_dir, 'rotated-%s' % imagefile))
            shutil.copy(os.path.join(working_dir, imagefile), os.path.join(working_dir, 'rotated-%s' % imagefile))
        else:
            execute_command(CFG_PATH_CONVERT, os.path.join(working_dir, imagefile), '-rotate', str(angle), os.path.join(working_dir, 'rotated-%s' % imagefile))
        return True

    def _perform_deskew(working_dir, imagefile):
        """Perform ocroscript deskew. Expect to work on rotated-imagefile.
        Creates deskewed-imagefile.
        Return True if deskewing was fine."""
        debug('Performing deskew on %s' % imagefile)
        try:
            dummy, stderr = execute_command_with_stderr(CFG_PATH_OCROSCRIPT, os.path.join(CFG_ETCDIR, 'websubmit', 'file_converter_templates', 'deskew.lua'), os.path.join(working_dir, 'rotated-%s' % imagefile), os.path.join(working_dir, 'deskewed-%s' % imagefile))
            if stderr.strip():
                debug('Errors found during deskewing')
                return False
            else:
                return True
        except InvenioWebSubmitFileConverterError, err:
            debug('Deskewing error: %s' % err)
            return False

    def _perform_recognize(working_dir, imagefile):
        """Perform ocroscript recognize. Expect to work on deskewed-imagefile.
        Creates recognized.out Return True if recognizing was fine."""
        debug('Performing recognize on %s' % imagefile)
        if extract_only_text:
            output_mode = 'text'
        else:
            output_mode = 'hocr'
        try:
            dummy, stderr = execute_command_with_stderr(CFG_PATH_OCROSCRIPT, 'recognize', '--tesslanguage=%s' % ln, '--output-mode=%s' % output_mode, os.path.join(working_dir, 'deskewed-%s' % imagefile), filename_out=os.path.join(working_dir, 'recognize.out'))
            if stderr.strip():
                ## There was some output on stderr
                debug('Errors found in recognize.err')
                return False
            return not guess_ocropus_produced_garbage(os.path.join(working_dir, 'recognize.out'), not extract_only_text)
        except InvenioWebSubmitFileConverterError, err:
            debug('Recognizer error: %s' % err)
            return False

    def _perform_dummy_recognize(working_dir, imagefile):
        """Return an empty text or an empty hocr referencing the image."""
        debug('Performing dummy recognize on %s' % imagefile)
        if extract_only_text:
            out = ''
        else:
            stdout = stderr = ''
            try:
                ## Since pdftoppm is returning a netpbm image, we use
                ## pamfile to retrieve the size of the image, in order to
                ## create an empty .hocr file containing just the
                ## desired file and a reference to its size.
                stdout, stderr = execute_command_with_stderr(CFG_PATH_PAMFILE, os.path.join(working_dir, imagefile))
                g = re.search(r'(?P<width>\d+) by (?P<height>\d+)', stdout)
                if g:
                    width = int(g.group('width'))
                    height = int(g.group('height'))

                    out = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
    <html xmlns="http://www.w3.org/1999/xhtml"><head><meta content="ocr_line ocr_page" name="ocr-capabilities"/><meta content="en" name="ocr-langs"/><meta content="Latn" name="ocr-scripts"/><meta content="" name="ocr-microformats"/><title>OCR Output</title></head>
    <body><div class="ocr_page" title="bbox 0 0 %s %s; image %s">
    </div></body></html>""" % (width, height, os.path.join(working_dir, imagefile))
                else:
                    raise InvenioWebSubmitFileConverterError()
            except Exception, err:
                raise InvenioWebSubmitFileConverterError('It\'s impossible to retrieve the size of %s needed to perform a dummy OCR. The stdout of pamfile was: %s, the stderr was: %s. (%s)' % (imagefile, stdout, stderr, err))
        open(os.path.join(working_dir, 'recognize.out'), 'w').write(out)

    if CFG_PATH_OCROSCRIPT:
        ln = CFG_TWO2THREE_LANG_CODES.get(ln, 'eng')
        if extract_only_text:
            output_format = '.txt'
        else:
            output_format = '.hocr'
        input_file, output_file, working_dir = prepare_io(input_file, output_file, output_format)
        #execute_command('pdfimages %s %s', input_file, os.path.join(working_dir, 'image'))
        execute_command(CFG_PATH_PDFTOPPM, '-r', '300', '-aa', 'yes', '-freetype', 'yes', input_file, os.path.join(working_dir, 'image'))

        images = os.listdir(working_dir)
        images.sort()
        for imagefile in images:
            if imagefile.startswith('image-'):
                for angle in (0, 90, 180, 270):
                    if _perform_rotate(working_dir, imagefile, angle) and _perform_deskew(working_dir, imagefile) and _perform_recognize(working_dir, imagefile):
                        ## Things went nicely! So we can remove the original
                        ## pbm picture which is soooooo huuuuugeee.
                        os.remove(os.path.join(working_dir, 'rotated-%s' % imagefile))
                        os.remove(os.path.join(working_dir, imagefile))
                        break
                else:
                    _perform_dummy_recognize(working_dir, imagefile)
                open(output_file, 'a').write(open(os.path.join(working_dir, 'recognize.out')).read())

        if return_working_dir:
            return output_file, working_dir
        else:
            clean_working_dir(working_dir)
            return output_file

    else:
        raise InvenioWebSubmitFileConverterError("It's impossible to generate HOCR output from PDF. OCROpus is not available.")


def hocr2pdf(input_file, output_file=None, working_dir=None, font="Courier", author=None, keywords=None, subject=None, title=None, draft=False, pdfopt=True, **dummy):
    """
    @param working_dir the directory containing images to build the PDF.
    @param font the default font (e.g. Courier, Times-Roman).
    @param author the author name.
    @param subject the subject of the document.
    @param title the title of the document.
    @param draft whether to enable debug information in the output.
    """
    if working_dir:
        working_dir = os.path.abspath(working_dir)
    else:
        working_dir = os.path.abspath(os.path.dirname(input_file))

    if pdfopt:
        input_file, tmp_output_file, dummy = prepare_io(input_file, output_ext='.pdf', need_working_dir=False)
    else:
        input_file, output_file, dummy = prepare_io(input_file, output_file=output_file, need_working_dir=False)
        tmp_output_file = output_file

    try:
        create_pdf(extract_hocr(open(input_file).read()), tmp_output_file, font=font, author=author, keywords=keywords, subject=subject, title=title, image_path=working_dir, draft=draft)
    except:
        register_exception()
        raise

    if pdfopt:
        output_file = pdf2pdfopt(tmp_output_file, output_file)
        os.remove(tmp_output_file)
        return output_file
    else:
        return tmp_output_file


def pdf2hocr2pdf(input_file, output_file=None, font="Courier", author=None, keywords=None, subject=None, title=None, draft=False, ln='en', pdfopt=True, **dummy):
    """
    Transform a scanned PDF into a PDF with OCRed text.
    @param font the default font (e.g. Courier, Times-Roman).
    @param author the author name.
    @param subject the subject of the document.
    @param title the title of the document.
    @param draft whether to enable debug information in the output.
    @param ln is a two letter language code to give the OCR tool a hint.
    """
    input_file, output_hocr_file, dummy = prepare_io(input_file, output_ext='.hocr', need_working_dir=False)
    output_hocr_file, working_dir = pdf2hocr(input_file, output_file=output_hocr_file, ln=ln, return_working_dir=True)
    output_file = hocr2pdf(output_hocr_file, output_file, working_dir, font=font, author=author, keywords=keywords, subject=subject, title=title, draft=draft, pdfopt=pdfopt)
    os.remove(output_hocr_file)
    clean_working_dir(working_dir)
    return output_file


def pdf2text(input_file, output_file=None, perform_ocr=True, ln='en', **dummy):
    """
    Return the text content in input_file.
    """
    input_file, output_file, dummy = prepare_io(input_file, output_file, '.txt', need_working_dir=False)
    execute_command(CFG_PATH_PDFTOTEXT, '-enc', 'UTF-8', '-eol', 'unix', '-nopgbrk', input_file, output_file)
    if perform_ocr and can_perform_ocr():
        ocred_output = pdf2hocr(input_file, ln=ln, extract_only_text=True)
        open(output_file, 'a').write(open(ocred_output).read())
        os.remove(ocred_output)
    return output_file


def txt2text(input_file, output_file=None, **dummy):
    """
    Return the text content in input_file
    """
    input_file, output_file, dummy = prepare_io(input_file, output_file, '.txt', need_working_dir=False)
    shutil.copy(input_file, output_file)
    return output_file


def html2text(input_file, output_file=None, **dummy):
    """
    Return the text content of an HTML/XML file.
    """

    class HTMLStripper(HTMLParser.HTMLParser):

        def __init__(self, output_file):
            HTMLParser.HTMLParser.__init__(self)
            self.output_file = output_file

        def handle_entityref(self, name):
            if name in entitydefs:
                self.output_file.write(entitydefs[name].decode('latin1').encode('utf8'))

        def handle_data(self, data):
            if data.strip():
                self.output_file.write(_RE_CLEAN_SPACES.sub(' ', data))

        def handle_charref(self, data):
            try:
                self.output_file.write(unichr(int(data)).encode('utf8'))
            except:
                pass

        def close(self):
            self.output_file.close()
            HTMLParser.HTMLParser.close(self)

    input_file, output_file, dummy = prepare_io(input_file, output_file, '.txt', need_working_dir=False)
    html_stripper = HTMLStripper(open(output_file, 'w'))
    for line in open(input_file):
        html_stripper.feed(line)
    html_stripper.close()
    return output_file


def djvu2text(input_file, output_file=None, **dummy):
    """
    Return the text content in input_file.
    """
    input_file, output_file, dummy = prepare_io(input_file, output_file, '.txt', need_working_dir=False)
    execute_command(CFG_PATH_DJVUTXT, input_file, output_file)
    return output_file


def djvu2ps(input_file, output_file=None, level=2, compress=True, **dummy):
    """
    Convert a djvu into a .ps[.gz]
    """
    if compress:
        input_file, output_file, working_dir = prepare_io(input_file, output_file, output_ext='.ps.gz')
        execute_command(CFG_PATH_DJVUPS, input_file, os.path.join(working_dir, 'output.ps'))
        execute_command(CFG_PATH_GZIP, '-c', os.path.join(working_dir, 'output.ps'), filename_out=output_file)
    else:
        input_file, output_file, working_dir = prepare_io(input_file, output_file, output_ext='.ps')
        execute_command(CFG_PATH_DJVUPS, '-level=%i' % level, input_file, output_file)
    clean_working_dir(working_dir)
    return output_file


def tiff2pdf(input_file, output_file=None, pdfopt=True, pdfa=True, perform_ocr=True, **args):
    """
    Convert a .tiff into a .pdf
    """
    if pdfa or pdfopt or perform_ocr:
        input_file, output_file, working_dir = prepare_io(input_file, output_file, '.pdf')
        partial_output = os.path.join(working_dir, 'output.pdf')
        execute_command(CFG_PATH_TIFF2PDF, '-o', partial_output, input_file)
        if perform_ocr:
            pdf2hocr2pdf(partial_output, output_file, pdfopt=pdfopt, **args)
        elif pdfa:
            pdf2pdfa(partial_output, output_file, pdfopt=pdfopt, **args)
        else:
            pdfopt(partial_output, output_file)
        clean_working_dir(working_dir)
    else:
        input_file, output_file, dummy = prepare_io(input_file, output_file, '.pdf', need_working_dir=False)
        execute_command(CFG_PATH_TIFF2PDF, '-o', output_file, input_file)
    return output_file


def pstotext(input_file, output_file=None, **dummy):
    """
    Convert a .ps[.gz] into text.
    """
    input_file, output_file, working_dir = prepare_io(input_file, output_file, '.txt')
    if input_file.endswith('.gz'):
        new_input_file = os.path.join(working_dir, 'input.ps')
        execute_command(CFG_PATH_GUNZIP, '-c', input_file, filename_out=new_input_file)
        input_file = new_input_file
    execute_command(CFG_PATH_PSTOTEXT, '-output', output_file, input_file)
    clean_working_dir(working_dir)
    return output_file


def gzip(input_file, output_file=None, **dummy):
    """
    Compress a file.
    """
    input_file, output_file, dummy = prepare_io(input_file, output_file, '.gz', need_working_dir=False)
    execute_command(CFG_PATH_GZIP, '-c', input_file, filename_out=output_file)
    return output_file


def gunzip(input_file, output_file=None, **dummy):
    """
    Uncompress a file.
    """
    from invenio.bibdocfile import decompose_file
    input_ext = decompose_file(input_file, skip_version=True)[2]
    if input_ext.endswith('.gz'):
        input_ext = input_ext[:-len('.gz')]
    else:
        input_ext = None
    input_file, output_file, dummy = prepare_io(input_file, output_file, input_ext, need_working_dir=False)
    execute_command(CFG_PATH_GUNZIP, '-c', input_file, filename_out=output_file)
    return output_file


def prepare_io(input_file, output_file=None, output_ext=None, need_working_dir=True):
    """Clean input_file and the output_file."""
    from invenio.bibdocfile import decompose_file, normalize_format
    output_ext = normalize_format(output_ext)
    debug('Preparing IO for input=%s, output=%s, output_ext=%s' % (input_file, output_file, output_ext))
    if output_ext is None:
        if output_file is None:
            output_ext = '.tmp'
        else:
            output_ext = decompose_file(output_file, skip_version=True)[2]
    if output_file is None:
        try:
            (fd, output_file) = tempfile.mkstemp(suffix=output_ext, dir=CFG_TMPDIR)
            os.close(fd)
        except IOError, err:
            raise InvenioWebSubmitFileConverterError("It's impossible to create a temporary file: %s" % err)
    else:
        output_file = os.path.abspath(output_file)
        if os.path.exists(output_file):
            os.remove(output_file)

    if need_working_dir:
        try:
            working_dir = tempfile.mkdtemp(dir=CFG_TMPDIR, prefix='conversion')
        except IOError, err:
            raise InvenioWebSubmitFileConverterError("It's impossible to create a temporary directory: %s" % err)

        input_ext = decompose_file(input_file, skip_version=True)[2]
        new_input_file = os.path.join(working_dir, 'input' + input_ext)
        shutil.copy(input_file, new_input_file)
        input_file = new_input_file
    else:
        working_dir = None
        input_file = os.path.abspath(input_file)

    debug('IO prepared: input_file=%s, output_file=%s, working_dir=%s' % (input_file, output_file, working_dir))
    return (input_file, output_file, working_dir)


def clean_working_dir(working_dir):
    """
    Remove the working_dir.
    """
    debug('Cleaning working_dir: %s' % working_dir)
    shutil.rmtree(working_dir)


def execute_command(*args, **argd):
    """Wrapper to run_process_with_timeout."""
    debug("Executing: %s" % (args, ))
    res, stdout, stderr = run_process_with_timeout(args, cwd=argd.get('cwd'), filename_out=argd.get('filename_out'), filename_err=argd.get('filename_err'))
    if res != 0:
        error("Error when executing %s" % (args, ))
        raise InvenioWebSubmitFileConverterError("Error in running %s\n stdout:\n%s\nstderr:\n%s\n" % (args, stdout, stderr))
    return stdout


def execute_command_with_stderr(*args, **argd):
    """Wrapper to run_process_with_timeout."""
    debug("Executing: %s" % (args, ))
    res, stdout, stderr = run_process_with_timeout(args, cwd=argd.get('cwd'), filename_out=argd.get('filename_out'))
    if res != 0:
        error("Error when executing %s" % (args, ))
        raise InvenioWebSubmitFileConverterError("Error in running %s\n stdout:\n%s\nstderr:\n%s\n" % (args, stdout, stderr))
    return stdout, stderr

__CONVERSION_MAP = get_conversion_map()


def main_cli():
    """
    main function when the library behaves as a normal CLI tool.
    """
    from invenio.bibdocfile import normalize_format
    parser = OptionParser()
    parser.add_option("-c", "--convert", dest="input_name",
                  help="convert the specified FILE", metavar="FILE")
    parser.add_option("-d", "--debug", dest="debug", action="store_true", help="Enable debug information")
    parser.add_option("--special-pdf2hocr2pdf", dest="ocrize", help="convert the given scanned PDF into a PDF with OCRed text", metavar="FILE")
    parser.add_option("-f", "--format", dest="output_format", help="the desired output format", metavar="FORMAT")
    parser.add_option("-o", "--output", dest="output_name", help="the desired output FILE (if not specified a new file will be generated with the desired output format)")
    parser.add_option("--without-pdfa", action="store_false", dest="pdf_a", default=True, help="don't force creation of PDF/A  PDFs")
    parser.add_option("--without-pdfopt", action="store_false", dest="pdfopt", default=True, help="don't force optimization of PDFs files")
    parser.add_option("--without-ocr", action="store_false", dest="ocr", default=True, help="don't force OCR")
    parser.add_option("--can-convert", dest="can_convert", help="display all the possible format that is possible to generate from the given format", metavar="FORMAT")
    parser.add_option("--is-ocr-needed", dest="check_ocr_is_needed", help="check if OCR is needed for the FILE specified", metavar="FILE")
    parser.add_option("-t", "--title", dest="title", help="specify the title (used when creating PDFs)", metavar="TITLE")
    parser.add_option("-l", "--language", dest="ln", help="specify the language (used when performing OCR, e.g. en, it, fr...)", metavar="LN", default='en')
    (options, dummy) = parser.parse_args()
    if options.debug:
        getLogger().setLevel(DEBUG)
    if options.can_convert:
        if options.can_convert:
            input_format = normalize_format(options.can_convert)
            if input_format == '.pdf':
                if can_pdfopt():
                    print "PDF linearization supported"
                else:
                    print "No PDF linearization support"
                if can_pdfa():
                    print "PDF/A generation supported"
                else:
                    print "No PDF/A generation support"
            if can_perform_ocr():
                print "OCR supported"
            else:
                print "OCR not supported"
            print 'Can convert from "%s" to:' % input_format[1:],
            for output_format in __CONVERSION_MAP:
                if can_convert(input_format, output_format):
                    print '"%s"' % output_format[1:],
            print
    elif options.check_ocr_is_needed:
        print "Checking if OCR is needed on %s..." % options.check_ocr_is_needed,
        sys.stdout.flush()
        if guess_is_OCR_needed(options.check_ocr_is_needed):
            print "needed."
        else:
            print "not needed."
    elif options.ocrize:
        try:
            output = pdf2hocr2pdf(options.ocrize, output_file=options.output_name, title=options.title, ln=options.ln)
            print "Output stored in %s" % output
        except InvenioWebSubmitFileConverterError, err:
            print "ERROR: %s" % err
            sys.exit(1)
    else:
        try:
            if not options.output_name and not options.output_format:
                parser.error("Either --format, --output should be specified")
            if not options.input_name:
                parser.error("An input should be specified!")
            output = convert_file(options.input_name, output_file=options.output_name, output_format=options.output_format, pdfopt=options.pdfopt, pdfa=options.pdf_a, title=options.title, ln=options.ln)
            print "Output stored in %s" % output
        except InvenioWebSubmitFileConverterError, err:
            print "ERROR: %s" % err
            sys.exit(1)


if __name__ == "__main__":
    main_cli()
