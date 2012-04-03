# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2010, 2011 CERN.
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

import urllib2, time, os, sys, re
from invenio.config import CFG_TMPDIR, \
                           CFG_PLOTEXTRACTOR_SOURCE_BASE_URL, \
                           CFG_PLOTEXTRACTOR_SOURCE_TARBALL_FOLDER, \
                           CFG_PLOTEXTRACTOR_SOURCE_PDF_FOLDER, \
                           CFG_PLOTEXTRACTOR_DOWNLOAD_TIMEOUT
from invenio.plotextractor_config import CFG_PLOTEXTRACTOR_DESY_BASE, \
                                         CFG_PLOTEXTRACTOR_DESY_PIECE
from invenio.search_engine import get_record
from invenio.bibrecord import record_get_field_instances, \
                              field_get_subfield_values
from invenio.shellutils import run_shell_command
from invenio.plotextractor_output_utils import write_message

PDF_EXTENSION = '.pdf'

ARXIV_HEADER = 'arXiv:'
HEP_EX = ['hep-ex/', 9405, ARXIV_HEADER + 'hep-ex_'] # experimental
# a note about hep-ex: the hep-ex papers from 9403 nad 9404 are stored
# in arXiv's servers as hep-ph
HEP_LAT = ['hep-lat/', 9107, ARXIV_HEADER + 'hep-lat_'] # lattice
HEP_PH = ['hep-ph/', 9203, ARXIV_HEADER + 'hep-ph_'] # phenomenology
HEP_TH = ['hep-th/', 9108, ARXIV_HEADER + 'hep-th_'] # theory

HEP_AREAS = [HEP_EX, HEP_LAT, HEP_PH, HEP_TH]

URL = 0
BEGIN_YEAR_MONTH_INDEX = 1
AREA_STRING_INDEX = 2

URL_MOVE = int('0704')
CENTURY_END = int('9912')
CENTURY_BEGIN = int('0001')
ARBITRARY_FROM_DATE = int('9101')
FIX_FOR_YEAR_END = 88
current_yearmonth = int(('%02d%02d' % (time.localtime().tm_year, \
        time.localtime().tm_mon))[2:])

"""
each of the areas of hep began in a different year and month.

beginning in 0704, i.e. April 2007, arXiv moved its URLS from
ARXIV_BASE + E_PRINT + HEP_AREA + <<numbernodot>>
to
ARXIV_BASE + E_PRINT + <<number.with.dot>>

the papers for a given month are numbered between yymm.0001 and yymm.9999
after the URL move, and before that they are between yymm001 and yymm999
"""

help_param = 'help'
dir_param = 'dir'
from_param = 'from'
from_index_param = 'fromindex'
ref_file_param = 'reffile'
single_param = 'single'
param_abbrs = 'hd:f:i:r:s:'
params = [help_param, dir_param + '=', from_param + '=', from_index_param + '=',
          ref_file_param + '=', single_param + '=']

def harvest(to_dir, from_date, from_index):
    """
        Calls upon arXiv using URLS as described above in order to grab
        all the tarballs from HEP areas.

        @param: dir (string): the directory where everything that gets
            downloaded will sit
        @param: from_date (int): the date from which we would like to harvest,
            in YYMM format
        @param: from_index (int): the index where we want to begin our harvest
            in YYMM.  i.e. we want to start with the 345th record in 1002.

        @output: TONS OF .tar.gz FILES FROM ARXIV
        @return: (none)
    """

    global current_yearmonth

    if from_date > current_yearmonth and from_date < ARBITRARY_FROM_DATE:
        write_message('Please choose a from date that is not in the future!')
        sys.exit(1)
    if from_date % 100 > 12:
        write_message('Please choose a from date in the form YYMM')
        sys.exit(1)

    if from_date >= ARBITRARY_FROM_DATE or from_date < URL_MOVE:
        for area in HEP_AREAS:

            yearmonthindex = area[BEGIN_YEAR_MONTH_INDEX]

            # nasty casing!
            # I find this particularly horrid because we have to wrap dates..
            # i.e. although 9901 is more than 0001, we might want things in
            # 0001 and not from 9901
            if from_date < current_yearmonth:
                # we want to start in the new century; skip the while below
                yearmonthindex = CENTURY_END
            elif from_date < CENTURY_END:
                yearmonthindex = from_date

            # grab stuff from between 92 and 99
            old_URL_harvest(yearmonthindex, CENTURY_END, to_dir, area)

            yearmonthindex = CENTURY_BEGIN

            # more nasty casing
            if from_date < URL_MOVE:
                # that means we want to start sometime before the weird
                # url change
                yearmonthindex = from_date
            elif from_date > URL_MOVE and from_date < ARBITRARY_FROM_DATE:
                # we don't want to start yet
                yearmonthindex = URL_MOVE

            # grab stuff from between 00 and 07
            old_URL_harvest(yearmonthindex, URL_MOVE, to_dir, area)

    # also after the URL move, there was no distinction between
    # papers from different areas.  hence, outside the for loop

    # even more nasty casing!
    if from_date < current_yearmonth and from_date > URL_MOVE:
        # we want to start someplace after the URL move and before now
        yearmonthindex = from_date
    else:
        yearmonthindex = URL_MOVE

    # grab stuff from between 07 and today
    new_URL_harvest(yearmonthindex, from_index, to_dir)


def make_single_directory(to_dir, dirname):
    """
        Makes a subdirectory for the arXiv record we are working with and
        returns its exact location.

        @param: to_dir (string): the name of the directory we want to make it
            in
        @param: dirname (string): the name of the directory we want to create

        @output: a new directory called dirname located in to_dir
        @return: the absolute path to the new directory
    """
    new_dir = os.path.join(to_dir, dirname)

    if not os.path.isdir(new_dir):
        try:
            os.mkdir(new_dir)
        except OSError:
            write_message('Failed to make new dir...')
            return to_dir

    return new_dir

def make_useful_directories(yearmonthindex, to_dir):
    """
        Builds up the hierarchical filestructure for saving these things
        in a useful way.

        @param: yearmonthindex (int): YYMM
        @param: to_dir (string): where we want to build the directories from

        @return month_dir (string): the new directory we are going to put
            stuff in
    """
    year = yearmonthindex / 100
    if year >= (ARBITRARY_FROM_DATE / 100):
        year = '19%02d' % year
    else:
        year = '20%02d' % year

    month = '%02d' % (yearmonthindex % 100)

    year_dir = os.path.join(to_dir, year)
    if not os.path.isdir(year_dir):
        os.mkdir(year_dir)

    month_dir = os.path.join(year_dir, month)
    if not os.path.isdir(month_dir):
        os.mkdir(month_dir)

    return month_dir

def get_list_of_all_matching_files(basedir, filetypes):
    """
    This function uses the os module in order tocrawl
    through the directory tree rooted at basedir and find all the files
    therein that include filetype in their 'file' output.  Returns a list
    of absolute paths to all files.

    @param: basedir (string): the directory where we want to start crawling
    @param: filetypes ([string, string]): something that will be contained in
        the output of running 'file' on the types of files we're looking for

    @return: file_paths ([string, string, ...]): a list of full paths to
        the files that we discovered
    """

    file_paths = []

    for dirpath, dummy0, filenames in os.walk(basedir):
        for filename in filenames:
            full_path = os.path.join(dirpath, filename)
            dummy1, cmd_out, dummy2 = run_shell_command('file %s', (full_path,))
            for filetype in filetypes:
                if cmd_out.find(filetype) > -1:
                    file_paths.append(full_path)

    return file_paths

def tarballs_by_recids(recids, sdir):
    """
    Take a string representing one recid or several and get the associated
    tarballs for those ids.

    @param: recids (string): the record id or ids
    @param: sdir (string): where the tarballs should live

    @return: tarballs ([string, string, ...]): locations of tarballs
    """
    list_of_ids = []

    if ',' in recids:
        recids = recids.split(',')
        for recid in recids:
            if '-' in recid:
                low, high = recid.split('-')
                recid = range(int(low), int(high))
                list_of_ids.extend(recid)
            else:
                recid = int(recid)
                list_of_ids.append(recid)

    else:
        if '-' in recids:
            low, high = recid.split('-')
            list_of_ids = range(int(low), int(high))
        else:
            list_of_ids = int(recid)

    arXiv_ids = []

    for recid in list_of_ids:
        rec = get_record(recid)
        for afieldinstance in record_get_field_instances(rec, tag='037'):
            if 'arXiv' == field_get_subfield_values(afieldinstance, '9')[0]:
                arXiv_id = field_get_subfield_values(afieldinstance, 'a')[0]
                arXiv_ids.append(arXiv_id)

    return tarballs_by_arXiv_id(arXiv_ids, sdir)

def tarballs_by_arXiv_id(arXiv_ids, sdir):
    """
    Takes an list of arXiv ids and downloads their tarballs
    and returns a list of the tarballs' locations.

    @param: arXiv_ids ([string, string, ...]): the arXiv ids you
        would like to have tarballs for
    @param: sdir (string): the place to download these tarballs to

    @return: tarballs ([string, ...]): a list of the tarballs downloaded
    """
    tarballs = []

    for arXiv_id in arXiv_ids:
        if 'arXiv' not in arXiv_id:
            arXiv_id = 'arXiv:' + arXiv_id
        tarball, dummy_pdf = harvest_single(arXiv_id, sdir, ("tarball",))
        if tarball != None:
            tarballs.append(tarball)
            time.sleep(CFG_PLOTEXTRACTOR_DOWNLOAD_TIMEOUT)

    return tarballs

def parse_and_download(infile, sdir):
    """
    Read the write_messageation in the input file and download the corresponding
    tarballs from arxiv.

    @param: infile (string): the name of the file to parse
    @param: sdir (string): where to put the downloaded tarballs
    """

    tarfiles = []

    tardir = os.path.join(sdir, 'tarballs')
    if not os.path.isdir(tardir):
        try:
            os.makedirs(tardir)
        except:
            write_message(sys.exc_info()[0])
            write_message('files will be loose, not in ' + tardir)
            tardir = sdir

    infile = open(infile)
    for line in infile.readlines():
        line = line.strip()
        if line.startswith('http://'):
            # hurray!
            url = line
            filename = url.split('/')[-1]
            if not download(url, tardir, filename):
                write_message(filename + ' may already exist')
                write_message(sys.exc_info()[0])
            filename = os.path.join(tardir, filename)
            tarfiles.append(filename)
            time.sleep(CFG_PLOTEXTRACTOR_DOWNLOAD_TIMEOUT) # be nice!
        elif line.startswith('arXiv'):
            tarfiles.extend(tarballs_by_arXiv_id([line.strip()], sdir))

    return tarfiles

def harvest_single(single, to_dir, selection=("tarball", "pdf")):
    """
    if we only want to harvest one id (arXiv or DESY), we can use this.

    @param: single (string): an id from arXiv or DESY
    @param: to_dir (string): where the output should be saved

    @output: the PDF and source tarball (if applicable) of this single record

    @return: (tarball, pdf): the location of the source tarball and PDF, None
            if not found
    """

    if single.find('arXiv') > -1 and 'arxiv.org' in CFG_PLOTEXTRACTOR_SOURCE_BASE_URL.lower():
        id_str = re.findall('[a-zA-Z\\-]+/\\d+|\\d+\\.\\d+', single)[0]
        idno = id_str.split('/')
        if len(idno) > 0:
            idno = idno[-1]
        yymm = int(idno[:4])
        yymm_dir = make_useful_directories(yymm, to_dir)
        url_for_file = CFG_PLOTEXTRACTOR_SOURCE_BASE_URL + \
                       CFG_PLOTEXTRACTOR_SOURCE_TARBALL_FOLDER + \
                       id_str
        url_for_pdf = CFG_PLOTEXTRACTOR_SOURCE_BASE_URL + \
                      CFG_PLOTEXTRACTOR_SOURCE_PDF_FOLDER + \
                      id_str + '.pdf' # adds '.pdf' to avoid arXiv internal redirect from arXivID to arXivID.pdf
        individual_file = 'arXiv:' + id_str.replace('/', '_')
        individual_dir = make_single_directory(yymm_dir, individual_file)
        abs_path = os.path.join(individual_dir, individual_file)
        tarball = abs_path
        pdf = abs_path + '.pdf'
        write_message('download ' + url_for_file + ' to ' + abs_path)
        if "tarball" in selection and not download(url_for_file, individual_file, individual_dir):
            write_message('download of tarball failed/skipped')
            tarball = None
        if "pdf" in selection and not download(url_for_pdf, individual_file + '.pdf', individual_dir):
            write_message('download of pdf failed/skipped')
            pdf = None
        return (tarball, pdf)

    elif single.find('arXiv') > -1 and CFG_PLOTEXTRACTOR_SOURCE_BASE_URL != '':
        # hmm... is it a filesystem?
        if CFG_PLOTEXTRACTOR_SOURCE_BASE_URL.startswith('/'):
            if not os.path.exists(CFG_PLOTEXTRACTOR_SOURCE_BASE_URL):
                write_message('PROBLEM WITH CFG_PLOTEXTRACTOR_SOURCE_BASE_URL: we cannot ' + \
                        'find this folder!')
                return (None, None)
            for root, files, dummy in os.walk(CFG_PLOTEXTRACTOR_SOURCE_BASE_URL):
                for file_name in files:
                    id_no = single.replace('arXiv', '')
                    if file_name.find(id_no) > -1 or\
                       file_name.find(id_no.replace('/', '_')) > -1 or\
                       file_name.find(id_no.replace('_', '/')) > -1 or\
                       file_name.find(id_no.replace(':', '')) > -1:
                        # that's our file!  probably.
                        return (os.path.join(root, file_name), None)

            # well, no luck there
            return (None, None)

        # okay... is it... a website?
        elif CFG_PLOTEXTRACTOR_SOURCE_BASE_URL.startswith('http') and "tarball" in selection:
            url_for_file = CFG_PLOTEXTRACTOR_SOURCE_BASE_URL + single
            individual_file = os.path.join(to_dir, single)
            download(url_for_file, individual_file, to_dir)
            return (individual_file, None)

        # well, I don't know what to do with it
        else:
            write_message('unsure how to handle CFG_PLOTEXTRACTOR_SOURCE_BASE_URL. ' + \
                  'please fix the harvest_single function in ' + \
                  'miscutil/lib/plotextractor_getter.py')
            return (None, None)

    elif single.find('DESY') > -1 and "pdf" in selection:
        # also okay!
        idno = re.findall('\\d{2,4}-\\d{3}', single)[0]
        year, number = idno.split('-')
        if len(year) < 4:
            if int(year) > 92:
                year = '19' + year
            else:
                year = '20' + year
        year_dir = make_single_directory(to_dir, year)
        desy_dir = make_single_directory(year_dir, 'DESY')
        individual_dir = make_single_directory(desy_dir, number)
        id_no = year[2:] + '-' + number + '.pdf'
        url_for_file = CFG_PLOTEXTRACTOR_DESY_BASE + year + \
                       CFG_PLOTEXTRACTOR_DESY_PIECE + id_no
        individual_file = id_no
        write_message('download ' + url_for_file + ' to ' + \
                os.path.join(individual_dir, individual_file))
        download(url_for_file, individual_file, individual_dir)
        return (None, individual_file)
    write_message('END')
    return (None, None)

def src_pdf_from_marc(marc_file):
    """
    Given a marc file, this function attempts to determine where to find
    a pdf for that record

    @param: marc_file (string): the location of a marc file we can look at

    @return: pdfloc (string): the location of the downloaded PDF source file,
        None if no pdf was downloaded
    """

    if not os.path.exists(marc_file):
        return None

    marc_file = open(marc_file)
    marc_text = marc_file.read()
    marc_file.close()

    arXiv_match = '(([a-zA-Z\\-]+/\\d{7})|(\\d{4}\\.\\d{4}))'
    DESY_match = 'DESY-\\d{2,4}-\\d{3}'

    pdf_loc = None
    to_dir = os.path.join(CFG_TMPDIR, 'plotdata')

    possible_match = re.search(arXiv_match, marc_text)
    if possible_match != None:
        # it's listed on arXiv, hooray!
        arXiv_id = possible_match.group(0)
        dummy1, pdf_loc = harvest_single(arXiv_id, to_dir, ("pdf",))

    possible_match = re.search(DESY_match, marc_text)
    if possible_match != None:
        # it's listed on DESY, hooray!
        desy_id = possible_match.group(0)
        dummy1, pdf_loc = harvest_single(desy_id, to_dir, ("pdf",))

    return pdf_loc


def harvest_from_file(filename, to_dir):
    """
    Harvest from the file Tibor made.
    Format of a single entry:
        oai:arXiv.org:area/YYMMIII
            or
        oai:arXiv.org:YYMM.IIII
    """

    ok_format = '^oai:arXiv.org:(([a-zA-Z\\-]+/\\d+)|(\\d+\\.\\d+))$'

    try:
        names_file = open(filename)
        for arXiv_name in names_file.readlines():
            if re.match(ok_format, arXiv_name) == None:
                write_message('error on ' + arXiv_name + '. continuing.')
                continue
            harvest_single(arXiv_name, to_dir)
            time.sleep(CFG_PLOTEXTRACTOR_DOWNLOAD_TIMEOUT)

    except IOError:
        write_message('Something is wrong with the file!')

def old_URL_harvest(from_date, to_date, to_dir, area):
    """
        Grab all the PDFs and tarballs off arXiv between from_date and to_date,
        where from_date and to_date are in YYMM form, and put them in their own
        separate folders inside of to_dir.  Folder hierarchy will be
            to_dir/YYYY/MM/arXiv_id/stuff_downloaded_from_arXiv
        this obeys the old URL format

        @param: from_date (int): YYMM form of the date where we want to start
            harvesting
        @param: to_date (int): YYMM form of the date where we want to stop
            harvesting
        @param: to_dir (string): the base directory to put all these subdirs in
        @param: area (int): the index in the HEP_AREAS array of the area we are
            currently working on downloading

        @output: PDFs and tarballs from arXiv in a hierarchy rooted at to_dir
        @return: None
    """

    yearmonthindex = from_date

    while yearmonthindex < to_date:

        sub_dir = make_useful_directories(yearmonthindex, to_dir)

        for paperindex in range(1, 1000):
            # for whatever reason, we can't count on these things to
            # start at 1 (in HEP_PH from 9403 to CENTURY_END only).
            # they start at frickin 202.
            #if area == HEP_PH and yearmonthindex < ARBITRARY_FROM_INDEX:
            #   paperindex = paperindex + 201
            # of note: before the URL change happened in 0704, it was
            # also the case that the paper numbers only had 3 digits
            next_to_harvest = '%04d%03d' % (yearmonthindex, paperindex)
            arXiv_id = area[AREA_STRING_INDEX] + next_to_harvest
            individual_dir = make_single_directory(sub_dir, arXiv_id)

            full_url = CFG_PLOTEXTRACTOR_SOURCE_BASE_URL + CFG_PLOTEXTRACTOR_SOURCE_TARBALL_FOLDER + \
                       area[URL] + next_to_harvest
            if not download(full_url, \
                area[AREA_STRING_INDEX] + next_to_harvest, individual_dir):
                break
            full_pdf_url = CFG_PLOTEXTRACTOR_SOURCE_BASE_URL + CFG_PLOTEXTRACTOR_SOURCE_PDF_FOLDER + \
                           area[URL] + next_to_harvest
            download(full_pdf_url, \
                area[AREA_STRING_INDEX] + next_to_harvest + PDF_EXTENSION, \
                individual_dir)
            time.sleep(CFG_PLOTEXTRACTOR_DOWNLOAD_TIMEOUT)
        if yearmonthindex % 100 == 12:
           # we reached the end of the year!
            yearmonthindex = yearmonthindex + FIX_FOR_YEAR_END
        yearmonthindex = yearmonthindex + 1

def new_URL_harvest(from_date, from_index, to_dir):
    """
        Grab all the PDFs and tarballs off arXiv between from_date and to_date,
        where from_date and to_date are in YYMM form, and put them in their own
        separate folders inside of to_dir.  Folder hierarchy will be
            to_dir/YYYY/MM/arXiv_id/stuff_downloaded_from_arXiv
        this obeys the new URL format

        @param: from_date (int): YYMM form of the date where we want to start
            harvesting
        @param: to_date (int): YYMM form of the date where we want to stop
            harvesting
        @param: to_dir (string): the base directory to put all these subdirs in

        @output: PDFs and tarballs from arXiv in a hierarchy rooted at to_dir
        @return: None
    """

    global current_yearmonth
    yearmonthindex = from_date

    while yearmonthindex < current_yearmonth:

        if yearmonthindex == from_date:
            fro = from_index
        else:
            fro = 1

        sub_dir = make_useful_directories(yearmonthindex, to_dir)

        for paperindex in range(fro, 10000):

            # of note: after the URL change happened in 0704, it was
            # the case that paper numbers had 4 digits
            next_to_harvest = '%04d.%04d' % (yearmonthindex, paperindex)
            arXiv_id = ARXIV_HEADER + next_to_harvest
            individual_dir = make_single_directory(sub_dir, arXiv_id)

            full_url = CFG_PLOTEXTRACTOR_SOURCE_BASE_URL + CFG_PLOTEXTRACTOR_SOURCE_TARBALL_FOLDER + \
                       next_to_harvest
            if not download(full_url, ARXIV_HEADER + next_to_harvest, \
                individual_dir):
                break

            full_pdf_url = CFG_PLOTEXTRACTOR_SOURCE_BASE_URL + CFG_PLOTEXTRACTOR_SOURCE_PDF_FOLDER + \
                           next_to_harvest
            download(full_pdf_url, \
                ARXIV_HEADER + next_to_harvest + PDF_EXTENSION, \
                individual_dir)
            time.sleep(CFG_PLOTEXTRACTOR_DOWNLOAD_TIMEOUT) # be nice to remote server

        if yearmonthindex % 100 == 12:
            # we reached the end of the year!
            yearmonthindex = yearmonthindex + FIX_FOR_YEAR_END
        yearmonthindex = yearmonthindex + 1

def download(url, filename, to_dir):
    """
        Actually does the call and download given a URL and desired output
        filename.

        @param: url (string): where the file lives on the interwebs
        @param: filename (string): where the file should live after download
        @param: to_dir (string): the dir where our new files will live

        @output: a file in to_dir

        @return: True on success, False on failure
    """
    new_file = os.path.join(to_dir, filename)

    try:
        conn = urllib2.urlopen(url)
        response = conn.read()
        conn.close()
        new_file_fd = open(new_file, 'w')
        new_file_fd.write(response)
        new_file_fd.close()
        write_message('Downloaded to ' + new_file)
        return True
    except (IOError, urllib2.URLError), e:
        # this could be a permissions error, but it probably means that
        # there's nothing left in that section YYMM
        write_message('Error downloading from %s: \n%s\n' % (url, str(e)))
        return False

