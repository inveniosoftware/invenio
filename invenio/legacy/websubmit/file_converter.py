# -*- coding: utf-8 -*-
# This file is part of Invenio.
# Copyright (C) 2009, 2010, 2011, 2012 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

from __future__ import print_function

"""
This module implement fulltext conversion between many different file formats.
"""

import HTMLParser
import atexit
import os
import pkg_resources
import re
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import threading
import time

from logging import DEBUG, getLogger
from six.moves.html_entities import entitydefs
from optparse import OptionParser
from six import iteritems

try:
    from invenio.legacy.websubmit.hocrlib import create_pdf, extract_hocr, CFG_PPM_RESOLUTION
    try:
        from PyPDF2 import PdfFileReader, PdfFileWriter
    except ImportError:
        from pyPdf import PdfFileReader, PdfFileWriter
    CFG_CAN_DO_OCR = True
except ImportError:
    CFG_CAN_DO_OCR = False

from invenio.utils.text import wrap_text_in_a_box
from invenio.utils.shell import run_process_with_timeout, run_shell_command
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
    CFG_PATH_PS2PDF, \
    CFG_OPENOFFICE_SERVER_HOST, \
    CFG_OPENOFFICE_SERVER_PORT, \
    CFG_OPENOFFICE_USER, \
    CFG_PATH_CONVERT, \
    CFG_PATH_PAMFILE, \
    CFG_BINDIR, \
    CFG_LOGDIR, \
    CFG_BIBSCHED_PROCESS_USER, \
    CFG_BIBDOCFILE_BEST_FORMATS_TO_EXTRACT_TEXT_FROM, \
    CFG_BIBDOCFILE_DESIRED_CONVERSIONS

from invenio.ext.logging import register_exception

def get_file_converter_logger():
    return getLogger("InvenioWebSubmitFileConverterLogger")

CFG_TWO2THREE_LANG_CODES = {
    'en': 'eng',
    'nl': 'nld',
    'es': 'spa',
    'de': 'deu',
    'it': 'ita',
    'fr': 'fra',
}

CFG_OPENOFFICE_TMPDIR = os.path.join(CFG_TMPDIR, 'ooffice-tmp-files')
CFG_GS_MINIMAL_VERSION_FOR_PDFA = "8.65"
CFG_GS_MINIMAL_VERSION_FOR_PDFX = "8.52"
#FIXME: pu don't know where is this file
CFG_ICC_PATH = os.path.join(CFG_ETCDIR, 'websubmit', 'file_converter_templates', 'ISOCoatedsb.icc')

CFG_PDFA_DEF_PATH = pkg_resources.resource_filename('invenio.legacy.websubmit', os.path.join('file_converter_template', 'PDFA_def.ps'))
CFG_PDFX_DEF_PATH = pkg_resources.resource_filename('invenio.legacy.websubmit', os.path.join('file_converter_template', 'PDFX_def.ps'))

CFG_UNOCONV_LOG_PATH = os.path.join(CFG_LOGDIR, 'unoconv.log')
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
        '.sxw': {},
        '.htm': {},
        '.html': {},
        '.odp': {},
        '.ods': {},
        '.odt': {},
        '.pdf': {},
        '.ppt': {},
        '.pptx': {},
        '.sxi': {},
        '.ps': {},
        '.ps.gz': {},
        '.rtf': {},
        '.tif': {},
        '.tiff': {},
        '.txt': {},
        '.xls': {},
        '.xlsx': {},
        '.sxc': {},
        '.xml': {},
        '.hocr': {},
        '.pdf;pdfa': {},
        '.asc': {},
    }
    if CFG_PATH_GZIP:
        ret['.ps']['.ps.gz'] = (gzip, {})
    if CFG_PATH_GUNZIP:
        ret['.ps.gz']['.ps'] = (gunzip, {})
    if CFG_PATH_ANY2DJVU:
        ret['.pdf']['.djvu'] = (any2djvu, {})
        ret['.ps']['.djvu'] = (any2djvu, {})
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
    if can_pdfa():
        ret['.ps']['.pdf;pdfa'] = (ps2pdfa, {})
        ret['.pdf']['.pdf;pdfa'] = (pdf2pdfa, {})
        if CFG_PATH_GUNZIP:
            ret['.ps.gz']['.pdf;pdfa'] = (ps2pdfa, {})
    else:
        if CFG_PATH_PS2PDF:
            ret['.ps']['.pdf;pdfa'] = (ps2pdf, {})
            if CFG_PATH_GUNZIP:
                ret['.ps.gz']['.pdf'] = (ps2pdf, {})
    if can_pdfx():
        ret['.ps']['.pdf;pdfx'] = (ps2pdfx, {})
        ret['.pdf']['.pdf;pdfx'] = (pdf2pdfx, {})
        if CFG_PATH_GUNZIP:
            ret['.ps.gz']['.pdf;pdfx'] = (ps2pdfx, {})
    if CFG_PATH_PDFTOPS:
        ret['.pdf']['.ps'] = (pdf2ps, {'compress': False})
        ret['.pdf;pdfa']['.ps'] = (pdf2ps, {'compress': False})
        if CFG_PATH_GZIP:
            ret['.pdf']['.ps.gz'] = (pdf2ps, {'compress': True})
            ret['.pdf;pdfa']['.ps.gz'] = (pdf2ps, {'compress': True})
    if CFG_PATH_PDFTOTEXT:
        ret['.pdf']['.txt'] = (pdf2text, {})
        ret['.pdf;pdfa']['.txt'] = (pdf2text, {})
    ret['.asc']['.txt'] = (txt2text, {})
    ret['.txt']['.txt'] = (txt2text, {})
    ret['.csv']['.txt'] = (txt2text, {})
    ret['.html']['.txt'] = (html2text, {})
    ret['.htm']['.txt'] = (html2text, {})
    ret['.xml']['.txt'] = (html2text, {})
    if CFG_PATH_TIFF2PDF:
        ret['.tiff']['.pdf'] = (tiff2pdf, {})
        ret['.tif']['.pdf'] = (tiff2pdf, {})
    if CFG_PATH_OPENOFFICE_PYTHON and CFG_OPENOFFICE_SERVER_HOST:
        ret['.rtf']['.odt'] = (unoconv, {'output_format': 'odt'})
        ret['.rtf']['.pdf;pdfa'] = (unoconv, {'output_format': 'pdf'})
        ret['.rtf']['.txt'] = (unoconv, {'output_format': 'txt'})
        ret['.rtf']['.docx'] = (unoconv, {'output_format': 'docx'})
        ret['.doc']['.odt'] = (unoconv, {'output_format': 'odt'})
        ret['.doc']['.pdf;pdfa'] = (unoconv, {'output_format': 'pdf'})
        ret['.doc']['.txt'] = (unoconv, {'output_format': 'txt'})
        ret['.doc']['.docx'] = (unoconv, {'output_format': 'docx'})
        ret['.docx']['.odt'] = (unoconv, {'output_format': 'odt'})
        ret['.docx']['.pdf;pdfa'] = (unoconv, {'output_format': 'pdf'})
        ret['.docx']['.txt'] = (unoconv, {'output_format': 'txt'})
        ret['.sxw']['.odt'] = (unoconv, {'output_format': 'odt'})
        ret['.sxw']['.pdf;pdfa'] = (unoconv, {'output_format': 'pdf'})
        ret['.sxw']['.txt'] = (unoconv, {'output_format': 'txt'})
        ret['.docx']['.docx'] = (unoconv, {'output_format': 'docx'})
        ret['.odt']['.doc'] = (unoconv, {'output_format': 'doc'})
        ret['.odt']['.pdf;pdfa'] = (unoconv, {'output_format': 'pdf'})
        ret['.odt']['.txt'] = (unoconv, {'output_format': 'txt'})
        ret['.odt']['.docx'] = (unoconv, {'output_format': 'docx'})
        ret['.ppt']['.odp'] = (unoconv, {'output_format': 'odp'})
        ret['.ppt']['.pdf;pdfa'] = (unoconv, {'output_format': 'pdf'})
        ret['.ppt']['.txt'] = (unoconv, {'output_format': 'txt'})
        ret['.ppt']['.pptx'] = (unoconv, {'output_format': 'pptx'})
        ret['.pptx']['.odp'] = (unoconv, {'output_format': 'odp'})
        ret['.pptx']['.pdf;pdfa'] = (unoconv, {'output_format': 'pdf'})
        ret['.pptx']['.txt'] = (unoconv, {'output_format': 'txt'})
        ret['.sxi']['.odp'] = (unoconv, {'output_format': 'odp'})
        ret['.sxi']['.pdf;pdfa'] = (unoconv, {'output_format': 'pdf'})
        ret['.sxi']['.txt'] = (unoconv, {'output_format': 'txt'})
        ret['.sxi']['.pptx'] = (unoconv, {'output_format': 'pptx'})
        ret['.odp']['.ppt'] = (unoconv, {'output_format': 'ppt'})
        ret['.odp']['.pptx'] = (unoconv, {'output_format': 'pptx'})
        ret['.odp']['.pdf;pdfa'] = (unoconv, {'output_format': 'pdf'})
        ret['.odp']['.txt'] = (unoconv, {'output_format': 'txt'})
        ret['.odp']['.pptx'] = (unoconv, {'output_format': 'pptx'})
        ret['.xls']['.ods'] = (unoconv, {'output_format': 'ods'})
        ret['.xls']['.xlsx'] = (unoconv, {'output_format': 'xslx'})
        ret['.xlsx']['.ods'] = (unoconv, {'output_format': 'ods'})
        ret['.sxc']['.ods'] = (unoconv, {'output_format': 'ods'})
        ret['.sxc']['.xlsx'] = (unoconv, {'output_format': 'xslx'})
        ret['.ods']['.xls'] = (unoconv, {'output_format': 'xls'})
        ret['.ods']['.pdf;pdfa'] = (unoconv, {'output_format': 'pdf'})
        ret['.ods']['.csv'] = (unoconv, {'output_format': 'csv'})
        ret['.ods']['.xlsx'] = (unoconv, {'output_format': 'xslx'})
    ret['.csv']['.txt'] = (txt2text, {})

    ## Let's add all the existing output formats as potential input formats.
    for value in ret.values():
        for key in value.keys():
            if key not in ret:
                ret[key] = {}
    return ret


def get_best_format_to_extract_text_from(filelist, best_formats=CFG_BIBDOCFILE_BEST_FORMATS_TO_EXTRACT_TEXT_FROM):
    """
    Return among the filelist the best file whose format is best suited for
    extracting text.
    """
    from invenio.legacy.bibdocfile.api import decompose_file, normalize_format
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
    from invenio.legacy.bibdocfile.api import normalize_format, decompose_file

    def normalize_desired_conversion():
        ret = {}
        for key, value in iteritems(desired_conversion):
            ret[normalize_format(key)] = [normalize_format(aformat) for aformat in value]
        return ret

    if desired_conversion is None:
        desired_conversion = CFG_BIBDOCFILE_DESIRED_CONVERSIONS

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


def can_convert(input_format, output_format, max_intermediate_conversions=4):
    """Return the chain of conversion to transform input_format into output_format, if any."""
    from invenio.legacy.bibdocfile.api import normalize_format
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


def can_pdfopt(verbose=False):
    """Return True if it's possible to optimize PDFs."""
    if CFG_PATH_PDFOPT:
        return True
    elif verbose:
        print("PDF linearization is not supported because the pdfopt executable is not available", file=sys.stderr)
    return False


def can_pdfx(verbose=False):
    """Return True if it's possible to generate PDF/Xs."""
    if not CFG_PATH_PDFTOPS:
        if verbose:
            print("Conversion of PS or PDF to PDF/X is not possible because the pdftops executable is not available", file=sys.stderr)
        return False
    if not CFG_PATH_GS:
        if verbose:
            print("Conversion of PS or PDF to PDF/X is not possible because the gs executable is not available", file=sys.stderr)
        return False
    else:
        try:
            output = run_shell_command("%s --version" % CFG_PATH_GS)[1].strip()
            if not output:
                raise ValueError("No version information returned")
            if [int(number) for number in output.split('.')] < [int(number) for number in CFG_GS_MINIMAL_VERSION_FOR_PDFX.split('.')]:
                print("Conversion of PS or PDF to PDF/X is not possible because the minimal gs version for the executable %s is not met: it should be %s but %s has been found" % (CFG_PATH_GS, CFG_GS_MINIMAL_VERSION_FOR_PDFX, output), file=sys.stderr)
                return False
        except Exception as err:
            print("Conversion of PS or PDF to PDF/X is not possible because it's not possible to retrieve the gs version using the executable %s: %s" % (CFG_PATH_GS, err), file=sys.stderr)
            return False
    if not CFG_PATH_PDFINFO:
        if verbose:
            print("Conversion of PS or PDF to PDF/X is not possible because the pdfinfo executable is not available", file=sys.stderr)
        return False
    if not os.path.exists(CFG_ICC_PATH):
        if verbose:
            print("Conversion of PS or PDF to PDF/X is not possible because %s does not exists. Have you run make install-pdfa-helper-files?" % CFG_ICC_PATH, file=sys.stderr)
        return False
    return True


def can_pdfa(verbose=False):
    """Return True if it's possible to generate PDF/As."""
    if not CFG_PATH_PDFTOPS:
        if verbose:
            print("Conversion of PS or PDF to PDF/A is not possible because the pdftops executable is not available", file=sys.stderr)
        return False
    if not CFG_PATH_GS:
        if verbose:
            print("Conversion of PS or PDF to PDF/A is not possible because the gs executable is not available", file=sys.stderr)
        return False
    else:
        try:
            output = run_shell_command("%s --version" % CFG_PATH_GS)[1].strip()
            if not output:
                raise ValueError("No version information returned")
            if [int(number) for number in output.split('.')] < [int(number) for number in CFG_GS_MINIMAL_VERSION_FOR_PDFA.split('.')]:
                print("Conversion of PS or PDF to PDF/A is not possible because the minimal gs version for the executable %s is not met: it should be %s but %s has been found" % (CFG_PATH_GS, CFG_GS_MINIMAL_VERSION_FOR_PDFA, output), file=sys.stderr)
                return False
        except Exception as err:
            print("Conversion of PS or PDF to PDF/A is not possible because it's not possible to retrieve the gs version using the executable %s: %s" % (CFG_PATH_GS, err), file=sys.stderr)
            return False
    if not CFG_PATH_PDFINFO:
        if verbose:
            print("Conversion of PS or PDF to PDF/A is not possible because the pdfinfo executable is not available", file=sys.stderr)
        return False
    if not os.path.exists(CFG_ICC_PATH):
        if verbose:
            print("Conversion of PS or PDF to PDF/A is not possible because %s does not exists. Have you run make install-pdfa-helper-files?" % CFG_ICC_PATH, file=sys.stderr)
        return False
    return True


def can_perform_ocr(verbose=False):
    """Return True if it's possible to perform OCR."""
    if not CFG_CAN_DO_OCR:
        if verbose:
            print("OCR is not supported because either the pyPdf of ReportLab Python libraries are missing", file=sys.stderr)
        return False
    if not CFG_PATH_OCROSCRIPT:
        if verbose:
            print("OCR is not supported because the ocroscript executable is not available", file=sys.stderr)
        return False
    if not CFG_PATH_PDFTOPPM:
        if verbose:
            print("OCR is not supported because the pdftoppm executable is not available", file=sys.stderr)
        return False
    return True


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
        get_file_converter_logger().debug('OCROpus produced garbage')
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
    from invenio.legacy.bibdocfile.api import decompose_file, normalize_format
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
        get_file_converter_logger().debug("Conversion chain from %s to %s: %s" % (input_ext, output_ext, conversion_chain))
        current_input = input_file
        for i, (converter, final_params) in enumerate(conversion_chain):
            current_output = None
            if i == (len(conversion_chain) - 1):
                current_output = output_file
            final_params = dict(final_params)
            final_params.update(params)
            try:
                get_file_converter_logger().debug("Converting from %s to %s using %s with params %s" % (current_input, current_output, converter, final_params))
                current_output = converter(current_input, current_output, **final_params)
                get_file_converter_logger().debug("... current_output %s" % (current_output, ))
            except InvenioWebSubmitFileConverterError as err:
                raise InvenioWebSubmitFileConverterError("Error when converting from %s to %s: %s" % (input_file, output_ext, err))
            except Exception as err:
                register_exception(alert_admin=True)
                raise InvenioWebSubmitFileConverterError("Unexpected error when converting from %s to %s (%s): %s" % (input_file, output_ext, type(err), err))
            if current_input != input_file:
                os.remove(current_input)
            current_input = current_output
        return current_output
    else:
        raise InvenioWebSubmitFileConverterError("It's impossible to convert from %s to %s" % (input_ext, output_ext))


try:
    _UNOCONV_DAEMON
except NameError:
    _UNOCONV_DAEMON = None

_UNOCONV_DAEMON_LOCK = threading.Lock()

def _register_unoconv():
    global _UNOCONV_DAEMON
    if CFG_OPENOFFICE_SERVER_HOST != 'localhost':
        return
    _UNOCONV_DAEMON_LOCK.acquire()
    try:
        if not _UNOCONV_DAEMON:
            output_log = open(CFG_UNOCONV_LOG_PATH, 'a')
            _UNOCONV_DAEMON = subprocess.Popen(['sudo', '-S', '-u', CFG_OPENOFFICE_USER, os.path.join(CFG_BINDIR, 'inveniounoconv'), '-vvv', '-s', CFG_OPENOFFICE_SERVER_HOST, '-p', str(CFG_OPENOFFICE_SERVER_PORT), '-l'], stdin=open('/dev/null', 'r'), stdout=output_log, stderr=output_log)
            time.sleep(3)
    finally:
        _UNOCONV_DAEMON_LOCK.release()

def _unregister_unoconv():
    global _UNOCONV_DAEMON
    if CFG_OPENOFFICE_SERVER_HOST != 'localhost':
        return
    _UNOCONV_DAEMON_LOCK.acquire()
    try:
        if _UNOCONV_DAEMON:
            output_log = open(CFG_UNOCONV_LOG_PATH, 'a')
            subprocess.call(['sudo', '-S', '-u', CFG_OPENOFFICE_USER, os.path.join(CFG_BINDIR, 'inveniounoconv'), '-k', '-vvv'], stdin=open('/dev/null', 'r'), stdout=output_log, stderr=output_log)
            time.sleep(1)
            if _UNOCONV_DAEMON.poll():
                try:
                    os.kill(_UNOCONV_DAEMON.pid, signal.SIGTERM)
                except OSError:
                    pass
                if _UNOCONV_DAEMON.poll():
                    try:
                        os.kill(_UNOCONV_DAEMON.pid, signal.SIGKILL)
                    except OSError:
                        pass
    finally:
        _UNOCONV_DAEMON_LOCK.release()

# NOTE: in case we switch back keeping LibreOffice running, uncomment
# the following line.
#atexit.register(_unregister_unoconv)

def unoconv(input_file, output_file=None, output_format='txt', pdfopt=True, **dummy):
    """Use unconv to convert among OpenOffice understood documents."""
    from invenio.legacy.bibdocfile.api import normalize_format

    ## NOTE: in case we switch back keeping LibreOffice running, uncomment
    ## the following line.
    #_register_unoconv()
    input_file, output_file, dummy = prepare_io(input_file, output_file, output_format, need_working_dir=False)
    if output_format == 'txt':
        unoconv_format = 'text'
    else:
        unoconv_format = output_format
    try:
        try:
            ## We copy the input file and we make it available to OpenOffice
            ## with the user nobody
            from invenio.legacy.bibdocfile.api import decompose_file
            input_format = decompose_file(input_file, skip_version=True)[2]
            fd, tmpinputfile = tempfile.mkstemp(dir=CFG_TMPDIR, suffix=normalize_format(input_format))
            os.close(fd)
            shutil.copy(input_file, tmpinputfile)
            get_file_converter_logger().debug("Prepared input file %s" % tmpinputfile)
            os.chmod(tmpinputfile, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
            tmpoutputfile = tempfile.mktemp(dir=CFG_OPENOFFICE_TMPDIR, suffix=normalize_format(output_format))
            get_file_converter_logger().debug("Prepared output file %s" % tmpoutputfile)
            try:
                execute_command(os.path.join(CFG_BINDIR, 'inveniounoconv'), '-vvv', '-s', CFG_OPENOFFICE_SERVER_HOST, '-p', str(CFG_OPENOFFICE_SERVER_PORT), '--output', tmpoutputfile, '-f', unoconv_format, tmpinputfile, sudo=CFG_OPENOFFICE_USER)
            except:
                register_exception(alert_admin=True)
                raise
        except InvenioWebSubmitFileConverterError:
            ## Ok maybe OpenOffice hanged. Let's better kill it and restarted!
            if CFG_OPENOFFICE_SERVER_HOST != 'localhost':
                ## There's not that much that we can do. Let's bail out
                if not os.path.exists(tmpoutputfile) or not os.path.getsize(tmpoutputfile):
                    raise
                else:
                    ## Sometimes OpenOffice crashes but we don't care :-)
                    ## it still have created a nice file.
                    pass
            else:
                execute_command(os.path.join(CFG_BINDIR, 'inveniounoconv'), '-vvv', '-k', sudo=CFG_OPENOFFICE_USER)
                ## NOTE: in case we switch back keeping LibreOffice running, uncomment
                ## the following lines.
                #_unregister_unoconv()
                #_register_unoconv()
                time.sleep(5)
                try:
                    execute_command(os.path.join(CFG_BINDIR, 'inveniounoconv'), '-vvv', '-s', CFG_OPENOFFICE_SERVER_HOST, '-p', str(CFG_OPENOFFICE_SERVER_PORT), '--output', tmpoutputfile, '-f', unoconv_format, tmpinputfile, sudo=CFG_OPENOFFICE_USER)
                except InvenioWebSubmitFileConverterError:
                    execute_command(os.path.join(CFG_BINDIR, 'inveniounoconv'), '-vvv', '-k', sudo=CFG_OPENOFFICE_USER)
                    if not os.path.exists(tmpoutputfile) or not os.path.getsize(tmpoutputfile):
                        raise InvenioWebSubmitFileConverterError('No output was generated by OpenOffice')
                    else:
                        ## Sometimes OpenOffice crashes but we don't care :-)
                        ## it still have created a nice file.
                        pass
    except Exception as err:
        raise InvenioWebSubmitFileConverterError(get_unoconv_installation_guideline(err))

    output_format = normalize_format(output_format)

    if output_format == '.pdf' and pdfopt:
        pdf2pdfopt(tmpoutputfile, output_file)
    else:
        shutil.copy(tmpoutputfile, output_file)
    execute_command(os.path.join(CFG_BINDIR, 'inveniounoconv'), '-r', tmpoutputfile, sudo=CFG_OPENOFFICE_USER)
    os.remove(tmpinputfile)
    return output_file

def get_unoconv_installation_guideline(err):
    """Return the Libre/OpenOffice installation guideline (embedding the
    current error message).
    """
    from invenio.legacy.bibsched.bibtask import guess_apache_process_user
    return wrap_text_in_a_box("""\
OpenOffice.org can't properly create files in the OpenOffice.org temporary
directory %(tmpdir)s, as the user %(nobody)s (as configured in
CFG_OPENOFFICE_USER invenio(-local).conf variable): %(err)s.

In your /etc/sudoers file, you should authorize the %(apache)s user to run
 %(unoconv)s as %(nobody)s user as in:


%(apache)s ALL=(%(nobody)s) NOPASSWD: %(unoconv)s


You should then run the following commands:

$ sudo mkdir -p %(tmpdir)s

$ sudo chown -R %(nobody)s %(tmpdir)s

$ sudo chmod -R 755 %(tmpdir)s""" % {
            'tmpdir' : CFG_OPENOFFICE_TMPDIR,
            'nobody' : CFG_OPENOFFICE_USER,
            'err' : err,
            'apache' : CFG_BIBSCHED_PROCESS_USER or guess_apache_process_user(),
            'python' : CFG_PATH_OPENOFFICE_PYTHON,
            'unoconv' : os.path.join(CFG_BINDIR, 'inveniounoconv')
            })

def can_unoconv(verbose=False):
    """
    If OpenOffice.org integration is enabled, checks whether the system is
    properly configured.
    """
    if CFG_PATH_OPENOFFICE_PYTHON and CFG_OPENOFFICE_SERVER_HOST:
        try:
            test = os.path.join(CFG_TMPDIR, 'test.txt')
            open(test, 'w').write('test')
            output = unoconv(test, output_format='pdf')
            output2 = convert_file(output, output_format='.txt')
            if 'test' not in open(output2).read():
                raise Exception("Coulnd't produce a valid PDF with Libre/OpenOffice.org")
            os.remove(output2)
            os.remove(output)
            os.remove(test)
            return True
        except Exception as err:
            if verbose:
                print(get_unoconv_installation_guideline(err), file=sys.stderr)
            return False
    else:
        if verbose:
            print("Libre/OpenOffice.org integration not enabled", file=sys.stderr)
        return False


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
    from invenio.legacy.bibdocfile.api import decompose_file
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

def pdf2pdfx(input_file, output_file=None, title=None, pdfopt=False, profile="pdf/x-3:2002", **dummy):
    """
    Transform any PDF into a PDF/X (see: <http://en.wikipedia.org/wiki/PDF/X>)
    @param input_file [string] the input file name
    @param output_file [string] the output_file file name, None for temporary generated
    @param title [string] the title of the document. None for autodiscovery.
    @param pdfopt [bool] whether to linearize the pdf, too.
    @param profile: [string] the PDFX profile to use. Supports: 'pdf/x-1a:2001', 'pdf/x-1a:2003', 'pdf/x-3:2002'
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

    get_file_converter_logger().debug("Extracted title is %s" % title)

    if os.path.exists(CFG_ICC_PATH):
        shutil.copy(CFG_ICC_PATH, working_dir)
    else:
        raise InvenioWebSubmitFileConverterError('ERROR: ISOCoatedsb.icc file missing. Have you run "make install-pdfa-helper-files" as part of your Invenio deployment?')
    pdfx_header = open(CFG_PDFX_DEF_PATH).read()
    pdfx_header = pdfx_header.replace('<<<<TITLEMARKER>>>>', title)
    icc_iso_profile_def = ''
    if profile == 'pdf/x-1a:2001':
        pdfx_version = 'PDF/X-1a:2001'
        pdfx_conformance = 'PDF/X-1a:2001'
    elif profile == 'pdf/x-1a:2003':
        pdfx_version = 'PDF/X-1a:2003'
        pdfx_conformance = 'PDF/X-1a:2003'
    elif profile == 'pdf/x-3:2002':
        icc_iso_profile_def = '/ICCProfile (ISOCoatedsb.icc)'
        pdfx_version = 'PDF/X-3:2002'
        pdfx_conformance = 'PDF/X-3:2002'
    pdfx_header = pdfx_header.replace('<<<<ICCPROFILEDEF>>>>', icc_iso_profile_def)
    pdfx_header = pdfx_header.replace('<<<<GTS_PDFXVersion>>>>', pdfx_version)
    pdfx_header = pdfx_header.replace('<<<<GTS_PDFXConformance>>>>', pdfx_conformance)
    outputpdf = os.path.join(working_dir, 'output_file.pdf')
    open(os.path.join(working_dir, 'PDFX_def.ps'), 'w').write(pdfx_header)
    if profile in ['pdf/x-3:2002']:
        execute_command(CFG_PATH_GS, '-sProcessColorModel=DeviceCMYK', '-dPDFX', '-dBATCH', '-dNOPAUSE', '-dNOOUTERSAVE', '-dUseCIEColor', '-sDEVICE=pdfwrite', '-dAutoRotatePages=/None', '-sOutputFile=output_file.pdf', os.path.join(working_dir, 'PDFX_def.ps'), input_file, cwd=working_dir)
    elif profile in ['pdf/x-1a:2001', 'pdf/x-1a:2003']:
        execute_command(CFG_PATH_GS, '-sProcessColorModel=DeviceCMYK', '-dPDFX', '-dBATCH', '-dNOPAUSE', '-dNOOUTERSAVE', '-sColorConversionStrategy=CMYK', '-sDEVICE=pdfwrite', '-dAutoRotatePages=/None', '-sOutputFile=output_file.pdf', os.path.join(working_dir, 'PDFX_def.ps'), input_file, cwd=working_dir)
    if pdfopt:
        execute_command(CFG_PATH_PDFOPT, outputpdf, output_file)
    else:
        shutil.move(outputpdf, output_file)
    clean_working_dir(working_dir)
    return output_file

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
    input_file, output_file, working_dir = prepare_io(input_file, output_file, '.pdf;pdfa')

    if title is None:
        stdout = execute_command(CFG_PATH_PDFINFO, input_file)
        for line in stdout.split('\n'):
            g = _RE_FIND_TITLE.match(line)
            if g:
                title = g.group(1)
                break
    if not title:
        title = 'No title'

    get_file_converter_logger().debug("Extracted title is %s" % title)

    if os.path.exists(CFG_ICC_PATH):
        shutil.copy(CFG_ICC_PATH, working_dir)
    else:
        raise InvenioWebSubmitFileConverterError('ERROR: ISOCoatedsb.icc file missing. Have you run "make install-pdfa-helper-files" as part of your Invenio deployment?')
    pdfa_header = open(CFG_PDFA_DEF_PATH).read()
    pdfa_header = pdfa_header.replace('<<<<TITLEMARKER>>>>', title)
    inputps = os.path.join(working_dir, 'input.ps')
    outputpdf = os.path.join(working_dir, 'output_file.pdf')
    open(os.path.join(working_dir, 'PDFA_def.ps'), 'w').write(pdfa_header)
    execute_command(CFG_PATH_PDFTOPS, '-level3', input_file, inputps)
    execute_command(CFG_PATH_GS, '-sProcessColorModel=DeviceCMYK', '-dPDFA', '-dBATCH', '-dNOPAUSE', '-dNOOUTERSAVE', '-dUseCIEColor', '-sDEVICE=pdfwrite', '-dAutoRotatePages=/None', '-sOutputFile=output_file.pdf', os.path.join(working_dir, 'PDFA_def.ps'), 'input.ps', cwd=working_dir)
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


def ps2pdfx(input_file, output_file=None, title=None, pdfopt=False, profile="pdf/x-3:2002", **dummy):
    """
    Transform any PS into a PDF/X (see: <http://en.wikipedia.org/wiki/PDF/X>)
    @param input_file [string] the input file name
    @param output_file [string] the output_file file name, None for temporary generated
    @param title [string] the title of the document. None for autodiscovery.
    @param pdfopt [bool] whether to linearize the pdf, too.
    @param profile: [string] the PDFX profile to use. Supports: 'pdf/x-1a:2001', 'pdf/x-1a:2003', 'pdf/x-3:2002'
    @return [string] output_file input_file
    raise InvenioWebSubmitFileConverterError in case of errors.
    """

    input_file, output_file, working_dir = prepare_io(input_file, output_file, '.pdf')
    if input_file.endswith('.gz'):
        new_input_file = os.path.join(working_dir, 'input.ps')
        execute_command(CFG_PATH_GUNZIP, '-c', input_file, filename_out=new_input_file)
        input_file = new_input_file
    if not title:
        title = 'No title'

    shutil.copy(CFG_ICC_PATH, working_dir)
    pdfx_header = open(CFG_PDFX_DEF_PATH).read()
    pdfx_header = pdfx_header.replace('<<<<TITLEMARKER>>>>', title)
    icc_iso_profile_def = ''
    if profile == 'pdf/x-1a:2001':
        pdfx_version = 'PDF/X-1a:2001'
        pdfx_conformance = 'PDF/X-1a:2001'
    elif profile == 'pdf/x-1a:2003':
        pdfx_version = 'PDF/X-1a:2003'
        pdfx_conformance = 'PDF/X-1a:2003'
    elif profile == 'pdf/x-3:2002':
        icc_iso_profile_def = '/ICCProfile (ISOCoatedsb.icc)'
        pdfx_version = 'PDF/X-3:2002'
        pdfx_conformance = 'PDF/X-3:2002'
    pdfx_header = pdfx_header.replace('<<<<ICCPROFILEDEF>>>>', icc_iso_profile_def)
    pdfx_header = pdfx_header.replace('<<<<GTS_PDFXVersion>>>>', pdfx_version)
    pdfx_header = pdfx_header.replace('<<<<TITLEMARKER>>>>', title)
    outputpdf = os.path.join(working_dir, 'output_file.pdf')
    open(os.path.join(working_dir, 'PDFX_def.ps'), 'w').write(pdfx_header)
    if profile in ['pdf/x-3:2002']:
        execute_command(CFG_PATH_GS, '-sProcessColorModel=DeviceCMYK', '-dPDFX', '-dBATCH', '-dNOPAUSE', '-dNOOUTERSAVE', '-dUseCIEColor', '-sDEVICE=pdfwrite', '-dAutoRotatePages=/None', '-sOutputFile=output_file.pdf', os.path.join(working_dir, 'PDFX_def.ps'), 'input.ps', cwd=working_dir)
    elif profile in ['pdf/x-1a:2001', 'pdf/x-1a:2003']:
        execute_command(CFG_PATH_GS, '-sProcessColorModel=DeviceCMYK', '-dPDFX', '-dBATCH', '-dNOPAUSE', '-dNOOUTERSAVE', '-sColorConversionStrategy=CMYK', '-dAutoRotatePages=/None', '-sDEVICE=pdfwrite', '-sOutputFile=output_file.pdf', os.path.join(working_dir, 'PDFX_def.ps'), 'input.ps', cwd=working_dir)
    if pdfopt:
        execute_command(CFG_PATH_PDFOPT, outputpdf, output_file)
    else:
        shutil.move(outputpdf, output_file)
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

    input_file, output_file, working_dir = prepare_io(input_file, output_file, '.pdf;pdfa')
    if input_file.endswith('.gz'):
        new_input_file = os.path.join(working_dir, 'input.ps')
        execute_command(CFG_PATH_GUNZIP, '-c', input_file, filename_out=new_input_file)
        input_file = new_input_file
    if not title:
        title = 'No title'

    shutil.copy(CFG_ICC_PATH, working_dir)
    pdfa_header = open(CFG_PDFA_DEF_PATH).read()
    pdfa_header = pdfa_header.replace('<<<<TITLEMARKER>>>>', title)
    outputpdf = os.path.join(working_dir, 'output_file.pdf')
    open(os.path.join(working_dir, 'PDFA_def.ps'), 'w').write(pdfa_header)
    execute_command(CFG_PATH_GS, '-sProcessColorModel=DeviceCMYK', '-dPDFA', '-dBATCH', '-dNOPAUSE', '-dNOOUTERSAVE', '-dUseCIEColor', '-sDEVICE=pdfwrite', '-dAutoRotatePages=/None', '-sOutputFile=output_file.pdf', os.path.join(working_dir, 'PDFA_def.ps'), input_file, cwd=working_dir)
    if pdfopt:
        execute_command(CFG_PATH_PDFOPT, outputpdf, output_file)
    else:
        shutil.move(outputpdf, output_file)
    clean_working_dir(working_dir)
    return output_file

def ps2pdf(input_file, output_file=None, pdfopt=None, **dummy):
    """
    Transform any PS into a PDF
    @param input_file [string] the input file name
    @param output_file [string] the output_file file name, None for temporary generated
    @param pdfopt [bool] whether to linearize the pdf, too.
    @return [string] output_file input_file
    raise InvenioWebSubmitFileConverterError in case of errors.
    """
    if pdfopt is None:
        pdfopt = bool(CFG_PATH_PDFOPT)

    input_file, output_file, working_dir = prepare_io(input_file, output_file, '.pdf')
    if input_file.endswith('.gz'):
        new_input_file = os.path.join(working_dir, 'input.ps')
        execute_command(CFG_PATH_GUNZIP, '-c', input_file, filename_out=new_input_file)
        input_file = new_input_file
    outputpdf = os.path.join(working_dir, 'output_file.pdf')
    execute_command(CFG_PATH_PS2PDF, input_file, outputpdf, cwd=working_dir)
    if pdfopt:
        execute_command(CFG_PATH_PDFOPT, outputpdf, output_file)
    else:
        shutil.move(outputpdf, output_file)
    clean_working_dir(working_dir)
    return output_file

def pdf2pdfhocr(input_pdf, text_hocr, output_pdf, rotations=None, font='Courier', draft=False):
    """
    Adds the OCRed text to the original pdf.
    @param rotations: a list of angles by which pages should be rotated
    """
    def _get_page_rotation(i):
        if len(rotations) > i:
            return rotations[i]
        return 0

    if rotations is None:
        rotations = []
    input_pdf, hocr_pdf, dummy = prepare_io(input_pdf, output_ext='.pdf', need_working_dir=False)
    create_pdf(extract_hocr(open(text_hocr).read()), hocr_pdf, font, draft)
    input1 = PdfFileReader(file(input_pdf, "rb"))
    input2 = PdfFileReader(file(hocr_pdf, "rb"))
    output = PdfFileWriter()

    info = input1.getDocumentInfo()
    if info:
        infoDict = output._info.getObject()
        infoDict.update(info)

    for i in range(0, input1.getNumPages()):
        orig_page = input1.getPage(i)
        text_page = input2.getPage(i)
        angle = _get_page_rotation(i)
        if angle != 0:
            print("Rotating page %d by %d degrees." % (i, angle), file=sys.stderr)
            text_page = text_page.rotateClockwise(angle)
        if draft:
            below, above = orig_page, text_page
        else:
            below, above = text_page, orig_page
        below.mergePage(above)
        if angle != 0 and not draft:
            print("Rotating back page %d by %d degrees." % (i, angle), file=sys.stderr)
            below.rotateCounterClockwise(angle)
        output.addPage(below)
    outputStream = file(output_pdf, "wb")
    output.write(outputStream)
    outputStream.close()
    os.remove(hocr_pdf)
    return output_pdf


def pdf2hocr2pdf(input_file, output_file=None, ln='en', return_working_dir=False, extract_only_text=False, pdfopt=True, font='Courier', draft=False, **dummy):
    """
    Return the text content in input_file.
    @param ln is a two letter language code to give the OCR tool a hint.
    @param return_working_dir if set to True, will return output_file path and the working_dir path, instead of deleting the working_dir. This is useful in case you need the intermediate images to build again a PDF.
    """

    def _perform_rotate(working_dir, imagefile, angle):
        """Rotate imagefile of the corresponding angle. Creates a new file
        with rotated.ppm."""
        get_file_converter_logger().debug('Performing rotate on %s by %s degrees' % (imagefile, angle))
        if not angle:
            #execute_command('%s %s %s', CFG_PATH_CONVERT, os.path.join(working_dir, imagefile), os.path.join(working_dir, 'rotated-%s' % imagefile))
            shutil.copy(os.path.join(working_dir, imagefile), os.path.join(working_dir, 'rotated.ppm'))
        else:
            execute_command(CFG_PATH_CONVERT, os.path.join(working_dir, imagefile), '-rotate', str(angle), '-depth', str(8), os.path.join(working_dir, 'rotated.ppm'))
        return True

    def _perform_deskew(working_dir):
        """Perform ocroscript deskew. Expect to work on rotated-imagefile.
        Creates deskewed.ppm.
        Return True if deskewing was fine."""
        get_file_converter_logger().debug('Performing deskew')
        try:
            dummy, stderr = execute_command_with_stderr(CFG_PATH_OCROSCRIPT, os.path.join(CFG_ETCDIR, 'websubmit', 'file_converter_templates', 'deskew.lua'), os.path.join(working_dir, 'rotated.ppm'), os.path.join(working_dir, 'deskewed.ppm'))
            if stderr.strip():
                get_file_converter_logger().debug('Errors found during deskewing')
                return False
            else:
                return True
        except InvenioWebSubmitFileConverterError as err:
            get_file_converter_logger().debug('Deskewing error: %s' % err)
            return False

    def _perform_recognize(working_dir):
        """Perform ocroscript recognize. Expect to work on deskewed.ppm.
        Creates recognized.out Return True if recognizing was fine."""
        get_file_converter_logger().debug('Performing recognize')
        if extract_only_text:
            output_mode = 'text'
        else:
            output_mode = 'hocr'
        try:
            dummy, stderr = execute_command_with_stderr(CFG_PATH_OCROSCRIPT, 'recognize', '--tesslanguage=%s' % ln, '--output-mode=%s' % output_mode, os.path.join(working_dir, 'deskewed.ppm'), filename_out=os.path.join(working_dir, 'recognize.out'))
            if stderr.strip():
                ## There was some output on stderr
                get_file_converter_logger().debug('Errors found in recognize.err')
                return False
            return not guess_ocropus_produced_garbage(os.path.join(working_dir, 'recognize.out'), not extract_only_text)
        except InvenioWebSubmitFileConverterError as err:
            get_file_converter_logger().debug('Recognizer error: %s' % err)
            return False

    def _perform_dummy_recognize(working_dir):
        """Return an empty text or an empty hocr referencing the image."""
        get_file_converter_logger().debug('Performing dummy recognize')
        if extract_only_text:
            out = ''
        else:
            out = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml"><head><meta content="ocr_line ocr_page" name="ocr-capabilities"/><meta content="en" name="ocr-langs"/><meta content="Latin" name="ocr-scripts"/><meta content="" name="ocr-microformats"/><title>OCR Output</title></head>
<body><div class="ocr_page" title="bbox 0 0 1 1; image deskewed.ppm">
</div></body></html>"""
        open(os.path.join(working_dir, 'recognize.out'), 'w').write(out)

    def _find_image_file(working_dir, imageprefix, page):
        ret = '%s-%d.ppm' % (imageprefix, page)
        if os.path.exists(os.path.join(working_dir, ret)):
            return ret
        ret = '%s-%02d.ppm' % (imageprefix, page)
        if os.path.exists(os.path.join(working_dir, ret)):
            return ret
        ret = '%s-%03d.ppm' % (imageprefix, page)
        if os.path.exists(os.path.join(working_dir, ret)):
            return ret
        ret = '%s-%04d.ppm' % (imageprefix, page)
        if os.path.exists(os.path.join(working_dir, ret)):
            return ret
        ret = '%s-%05d.ppm' % (imageprefix, page)
        if os.path.exists(os.path.join(working_dir, ret)):
            return ret
        ret = '%s-%06d.ppm' % (imageprefix, page)
        if os.path.exists(os.path.join(working_dir, ret)):
            return ret
        ## I guess we won't have documents with more than million pages
        return None

    def _ocr(tmp_output_file):
        """
        Append to tmp_output_file the partial results of OCROpus recognize.
        Return a list of rotations.
        """
        page = 0
        rotations = []
        while True:
            page += 1
            get_file_converter_logger().debug('Page %d.' % page)
            execute_command(CFG_PATH_PDFTOPPM, '-f', str(page), '-l', str(page), '-r', str(CFG_PPM_RESOLUTION), '-aa', 'yes', '-freetype', 'yes', input_file, os.path.join(working_dir, 'image'))
            imagefile = _find_image_file(working_dir, 'image', page)
            if imagefile == None:
                break
            for angle in (0, 180, 90, 270):
                get_file_converter_logger().debug('Trying %d degrees...' % angle)
                if _perform_rotate(working_dir, imagefile, angle) and _perform_deskew(working_dir) and _perform_recognize(working_dir):
                    rotations.append(angle)
                    break
            else:
                get_file_converter_logger().debug('Dummy recognize')
                rotations.append(0)
                _perform_dummy_recognize(working_dir)
            open(tmp_output_file, 'a').write(open(os.path.join(working_dir, 'recognize.out')).read())
            # clean
            os.remove(os.path.join(working_dir, imagefile))
        return rotations


    if CFG_PATH_OCROSCRIPT:
        if len(ln) == 2:
            ln = CFG_TWO2THREE_LANG_CODES.get(ln, 'eng')
        if extract_only_text:
            input_file, output_file, working_dir = prepare_io(input_file, output_file, output_ext='.txt')
            _ocr(output_file)
        else:
            input_file, tmp_output_hocr, working_dir = prepare_io(input_file, output_ext='.hocr')
            rotations = _ocr(tmp_output_hocr)
            if pdfopt:
                input_file, tmp_output_pdf, dummy = prepare_io(input_file, output_ext='.pdf', need_working_dir=False)
                tmp_output_pdf, output_file, dummy = prepare_io(tmp_output_pdf, output_file, output_ext='.pdf', need_working_dir=False)
                pdf2pdfhocr(input_file, tmp_output_hocr, tmp_output_pdf, rotations=rotations, font=font, draft=draft)
                pdf2pdfopt(tmp_output_pdf, output_file)
                os.remove(tmp_output_pdf)
            else:
                input_file, output_file, dummy = prepare_io(input_file, output_file, output_ext='.pdf', need_working_dir=False)
                pdf2pdfhocr(input_file, tmp_output_hocr, output_file, rotations=rotations, font=font, draft=draft)
        clean_working_dir(working_dir)
        return output_file
    else:
        raise InvenioWebSubmitFileConverterError("It's impossible to generate HOCR output from PDF. OCROpus is not available.")

def pdf2text(input_file, output_file=None, perform_ocr=True, ln='en', **dummy):
    """
    Return the text content in input_file.
    """
    input_file, output_file, dummy = prepare_io(input_file, output_file, '.txt', need_working_dir=False)
    execute_command(CFG_PATH_PDFTOTEXT, '-enc', 'UTF-8', '-eol', 'unix', '-nopgbrk', input_file, output_file)
    if perform_ocr and can_perform_ocr():
        ocred_output = pdf2hocr2pdf(input_file, ln=ln, extract_only_text=True)
        try:
            output = open(output_file, 'a')
            for row in open(ocred_output):
                output.write(row)
            output.close()
        finally:
            silent_remove(ocred_output)
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
        try:
            execute_command(CFG_PATH_DJVUPS, input_file, os.path.join(working_dir, 'output.ps'))
            execute_command(CFG_PATH_GZIP, '-c', os.path.join(working_dir, 'output.ps'), filename_out=output_file)
        finally:
            clean_working_dir(working_dir)
    else:
        try:
            input_file, output_file, working_dir = prepare_io(input_file, output_file, output_ext='.ps')
            execute_command(CFG_PATH_DJVUPS, '-level=%i' % level, input_file, output_file)
        finally:
            clean_working_dir(working_dir)
    return output_file


def tiff2pdf(input_file, output_file=None, pdfopt=True, pdfa=True, perform_ocr=True, **args):
    """
    Convert a .tiff into a .pdf
    """
    if pdfa or pdfopt or perform_ocr:
        input_file, output_file, working_dir = prepare_io(input_file, output_file, '.pdf')
        try:
            partial_output = os.path.join(working_dir, 'output.pdf')
            execute_command(CFG_PATH_TIFF2PDF, '-o', partial_output, input_file)
            if perform_ocr:
                pdf2hocr2pdf(partial_output, output_file, pdfopt=pdfopt, **args)
            elif pdfa:
                pdf2pdfa(partial_output, output_file, pdfopt=pdfopt, **args)
            else:
                pdfopt(partial_output, output_file)
        finally:
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
    try:
        if input_file.endswith('.gz'):
            new_input_file = os.path.join(working_dir, 'input.ps')
            execute_command(CFG_PATH_GUNZIP, '-c', input_file, filename_out=new_input_file)
            input_file = new_input_file
        execute_command(CFG_PATH_PSTOTEXT, '-output', output_file, input_file)
    finally:
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
    from invenio.legacy.bibdocfile.api import decompose_file
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
    from invenio.legacy.bibdocfile.api import decompose_file, normalize_format
    output_ext = normalize_format(output_ext)
    get_file_converter_logger().debug('Preparing IO for input=%s, output=%s, output_ext=%s' % (input_file, output_file, output_ext))
    if output_ext is None:
        if output_file is None:
            output_ext = '.tmp'
        else:
            output_ext = decompose_file(output_file, skip_version=True)[2]
    if output_file is None:
        try:
            (fd, output_file) = tempfile.mkstemp(suffix=output_ext, dir=CFG_TMPDIR)
            os.close(fd)
        except IOError as err:
            raise InvenioWebSubmitFileConverterError("It's impossible to create a temporary file: %s" % err)
    else:
        output_file = os.path.abspath(output_file)
        if os.path.exists(output_file):
            os.remove(output_file)

    if need_working_dir:
        try:
            working_dir = tempfile.mkdtemp(dir=CFG_TMPDIR, prefix='conversion')
        except IOError as err:
            raise InvenioWebSubmitFileConverterError("It's impossible to create a temporary directory: %s" % err)

        input_ext = decompose_file(input_file, skip_version=True)[2]
        new_input_file = os.path.join(working_dir, 'input' + input_ext)
        shutil.copy(input_file, new_input_file)
        input_file = new_input_file
    else:
        working_dir = None
        input_file = os.path.abspath(input_file)

    get_file_converter_logger().debug('IO prepared: input_file=%s, output_file=%s, working_dir=%s' % (input_file, output_file, working_dir))
    return (input_file, output_file, working_dir)


def clean_working_dir(working_dir):
    """
    Remove the working_dir.
    """
    get_file_converter_logger().debug('Cleaning working_dir: %s' % working_dir)
    shutil.rmtree(working_dir)


def execute_command(*args, **argd):
    """Wrapper to run_process_with_timeout."""
    get_file_converter_logger().debug("Executing: %s" % (args, ))
    args = [str(arg) for arg in args]
    sudo = argd.get('sudo') or None
    if sudo:
        pass
        # May be forbidden by sudo
        # args = ['CFG_OPENOFFICE_TMPDIR="%s"' % CFG_OPENOFFICE_TMPDIR] + args
    else:
        os.putenv('CFG_OPENOFFICE_TMPDIR', CFG_OPENOFFICE_TMPDIR)
    res, stdout, stderr = run_process_with_timeout(args,
                                        cwd=argd.get('cwd'),
                                        filename_out=argd.get('filename_out'),
                                        filename_err=argd.get('filename_err'),
                                        sudo=sudo)
    get_file_converter_logger().debug('res: %s, stdout: %s, stderr: %s' % (res, stdout, stderr))
    if res != 0:
        message = "ERROR: Error in running %s\n stdout:\n%s\nstderr:\n%s\n" % (args, stdout, stderr)
        get_file_converter_logger().error(message)
        raise InvenioWebSubmitFileConverterError(message)
    return stdout


def execute_command_with_stderr(*args, **argd):
    """Wrapper to run_process_with_timeout."""
    get_file_converter_logger().debug("Executing: %s" % (args, ))
    res, stdout, stderr = run_process_with_timeout(args, cwd=argd.get('cwd'), filename_out=argd.get('filename_out'), sudo=argd.get('sudo'))
    if res != 0:
        message = "ERROR: Error in running %s\n stdout:\n%s\nstderr:\n%s\n" % (args, stdout, stderr)
        get_file_converter_logger().error(message)
        raise InvenioWebSubmitFileConverterError(message)
    return stdout, stderr

def silent_remove(path):
    """Remove without errors a path."""
    if os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass

__CONVERSION_MAP = get_conversion_map()


def main_cli():
    """
    main function when the library behaves as a normal CLI tool.
    """
    from invenio.legacy.bibdocfile.api import normalize_format
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
        from logging import basicConfig
        basicConfig()
        get_file_converter_logger().setLevel(DEBUG)
    if options.can_convert:
        if options.can_convert:
            input_format = normalize_format(options.can_convert)
            if input_format == '.pdf':
                if can_pdfopt(True):
                    print("PDF linearization supported")
                else:
                    print("No PDF linearization support")
                if can_pdfa(True):
                    print("PDF/A generation supported")
                else:
                    print("No PDF/A generation support")
            if can_perform_ocr(True):
                print("OCR supported")
            else:
                print("OCR not supported")
            print('Can convert from "%s" to:' % input_format[1:], end=' ')
            for output_format in __CONVERSION_MAP:
                if can_convert(input_format, output_format):
                    print('"%s"' % output_format[1:], end=' ')
            print()
    elif options.check_ocr_is_needed:
        print("Checking if OCR is needed on %s..." % options.check_ocr_is_needed, end=' ')
        sys.stdout.flush()
        if guess_is_OCR_needed(options.check_ocr_is_needed):
            print("needed.")
        else:
            print("not needed.")
    elif options.ocrize:
        try:
            output = pdf2hocr2pdf(options.ocrize, output_file=options.output_name, title=options.title, ln=options.ln)
            print("Output stored in %s" % output)
        except InvenioWebSubmitFileConverterError as err:
            print("ERROR: %s" % err)
            sys.exit(1)
    else:
        try:
            if not options.output_name and not options.output_format:
                parser.error("Either --format, --output should be specified")
            if not options.input_name:
                parser.error("An input should be specified!")
            output = convert_file(options.input_name, output_file=options.output_name, output_format=options.output_format, pdfopt=options.pdfopt, pdfa=options.pdf_a, title=options.title, ln=options.ln)
            print("Output stored in %s" % output)
        except InvenioWebSubmitFileConverterError as err:
            print("ERROR: %s" % err)
            sys.exit(1)


if __name__ == "__main__":
    main_cli()
