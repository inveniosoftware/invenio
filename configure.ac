## This file is part of Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013 CERN.
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

## This is Invenio main configure.ac file.  If you change this
## file, then please run "autoreconf" to regenerate the "configure"
## script.

## Initialize autoconf and automake:
AC_INIT([invenio],
        m4_esyscmd([./git-version-gen .tarball-version]),
        [info@invenio-software.org])
AM_INIT_AUTOMAKE([tar-ustar])

## By default we shall install into /opt/invenio.  (Do not use
## AC_PREFIX_DEFAULT for this, because it would not work well with
## the localstatedir hack below.)
test "${prefix}" = NONE && prefix=/opt/invenio

## Remove eventual trailing slashes from the prefix value:
test "${prefix%/}" != "" && prefix=${prefix%/}

## Check for install:
AC_PROG_INSTALL

## Check for gettext support:
AM_GNU_GETTEXT(external)
AM_GNU_GETTEXT_VERSION(0.14.4)

## Check for MySQL client:
AC_MSG_CHECKING(for mysql)
AC_ARG_WITH(mysql, AC_HELP_STRING([--with-mysql], [path to a specific MySQL binary (optional)]), MYSQL=${withval})
if test -n "$MYSQL"; then
   AC_MSG_RESULT($MYSQL)
else
   AC_PATH_PROG(MYSQL, mysql)
   if test -z "$MYSQL"; then
      AC_MSG_ERROR([
      MySQL command-line client was not found in your PATH.
      Please install it first.
      Available from <http://mysql.com/>.])
   fi
fi

## Check for Python:
AC_MSG_CHECKING(for python)
AC_ARG_WITH(python, AC_HELP_STRING([--with-python], [path to a specific Python binary (optional)]), PYTHON=${withval})
if test -n "$PYTHON"; then
   AC_MSG_RESULT($PYTHON)
else
   AC_PATH_PROG(PYTHON, python)
   if test -z "$PYTHON"; then
      AC_MSG_ERROR([
      Python was not found in your PATH.  Please either install it
      in your PATH or specify --with-python configure option.
      Python is available from <http://python.org/>.])
   fi
fi

## Check for OpenOffice.org Python binary:
AC_MSG_CHECKING(for OpenOffice.org Python binary)
AC_ARG_WITH(openoffice-python, AC_HELP_STRING([--with-openoffice-python], [path to a specific OpenOffice.org Python binary (optional)]), OPENOFFICE_PYTHON=`which ${withval}`)

if test -z "$OPENOFFICE_PYTHON"; then
   OPENOFFICE_PYTHON=`locate -l 1 -r "o.*office/program/python$"`
   OPENOFFICE_PYTHON="$PYTHON $OPENOFFICE_PYTHON"
   if test -n "$OPENOFFICE_PYTHON" && ($OPENOFFICE_PYTHON -c "import uno" 2> /dev/null); then
      AC_MSG_RESULT($OPENOFFICE_PYTHON)
   else
      AC_MSG_WARN([
      You have not specified the path ot the OpenOffice.org Python binary.
      OpenOffice.org and Microsoft Office document conversion and fulltext indexing
      will not be available.  We recommend you to install OpenOffice.org first
      and to rerun the configure script. OpenOffice.org is available from
      <http://www.openoffice.org/>.])
   fi
elif ($OPENOFFICE_PYTHON -c "import uno" 2> /dev/null); then
   AC_MSG_RESULT($OPENOFFICE_PYTHON)
else
   AC_MSG_ERROR([
   The specified OpenOffice.org Python binary is not correctly configured.
   Please specify the correct path to the specific OpenOffice Python binary
   (OpenOffice.org is available from <http://www.openoffice.org/>).])
fi

## Check for Python version and modules:
AC_MSG_CHECKING(for required Python modules)
$PYTHON ${srcdir}/configure-tests.py
if test $? -ne 0; then
   AC_MSG_ERROR([Please fix the above Python problem before continuing.])
fi
AC_MSG_RESULT(found)

## Check for PHP:
AC_PATH_PROG(PHP, php)

## Check for gzip:
AC_PATH_PROG(GZIP, gzip)
if test -z "$GZIP"; then
   AC_MSG_WARN([
   Gzip was not found in your PATH.  It is used in
   the WebSubmit module to compress the data submitted in an archive.
   You can continue without it but you will miss some Invenio
   functionality.  We recommend you to install it first and to rerun
   the configure script.  Gzip is available from
   <http://www.gzip.org/>.])
fi

## Check for gunzip:
AC_PATH_PROG(GUNZIP, gunzip)
if test -z "$GUNZIP"; then
   AC_MSG_WARN([
   Gunzip was not found in your PATH.  It is used in
   the WebSubmit module to correctly deal with submitted compressed
   files.
   You can continue without it but you will miss some Invenio
   functionality.  We recommend you to install it first and to rerun
   the configure script.  Gunzip is available from
   <http://www.gzip.org/>.])
fi

## Check for tar:
AC_PATH_PROG(TAR, tar)
if test -z "$TAR"; then
   AC_MSG_WARN([
   Tar was not found in your PATH.  It is used in
   the WebSubmit module to pack the submitted data into an archive.
   You can continue without it but you will miss some Invenio
   functionality.  We recommend you to install it first and to rerun
   the configure script.  Tar is available from
   <ftp://prep.ai.mit.edu/pub/gnu/tar/>.])
fi

## Check for wget:
AC_PATH_PROG(WGET, wget)
if test -z "$WGET"; then
   AC_MSG_WARN([
   wget was not found in your PATH.  It is used for the fulltext file
   retrieval.
   You can continue without it but we recomend you to install it first
   and to rerun the configure script.  wget is available from
   <http://www.gnu.org/software/wget/>.])
fi

## Check for md5sum:
AC_PATH_PROG(MD5SUM, md5sum)
if test -z "$MD5SUM"; then
   AC_MSG_WARN([
   md5sum was not found in your PATH.  It is used for the fulltext file
   checksum verification.
   You can continue without it but we recomend you to install it first
   and to rerun the configure script.  md5sum is available from
   <http://www.gnu.org/software/coreutils/>.])
fi

## Check for ps2pdf:
AC_PATH_PROG(PS2PDF, ps2pdf)
if test -z "$PS2PDF"; then
   AC_MSG_WARN([
   ps2pdf was not found in your PATH.  It is used in
   the WebSubmit module to convert submitted PostScripts into PDF.
   You can continue without it but you will miss some Invenio
   functionality.  We recommend you to install it first and to rerun
   the configure script.  ps2pdf is available from
   <http://www.cs.wisc.edu/~ghost/doc/AFPL/>.])
fi

## Check for pdflatex:
AC_PATH_PROG(PDFLATEX, pdflatex)
if test -z "$PDFLATEX"; then
   AC_MSG_WARN([
   pdflatex was not found in your PATH.  It is used in
   the WebSubmit module to stamp PDF files.
   You can continue without it but you will miss some Invenio
   functionality.  We recommend you to install it first and to rerun
   the configure script.])
fi


## Check for tiff2pdf:
AC_PATH_PROG(TIFF2PDF, tiff2pdf)
if test -z "$TIFF2PDF"; then
   AC_MSG_WARN([
   tiff2pdf was not found in your PATH.  It is used in
   the WebSubmit module to convert submitted TIFF file into PDF.
   You can continue without it but you will miss some Invenio
   functionality.  We recommend you to install it first and to rerun
   the configure script.  tiff2pdf is available from
   <http://www.remotesensing.org/libtiff/>.])
fi

## Check for gs:
AC_PATH_PROG(GS, gs)
if test -z "$GS"; then
   AC_MSG_WARN([
   gs was not found in your PATH.  It is used in
   the WebSubmit module to convert submitted PostScripts into PDF.
   You can continue without it but you will miss some Invenio
   functionality.  We recommend you to install it first and to rerun
   the configure script.  gs is available from
   <http://www.cs.wisc.edu/~ghost/doc/AFPL/>.])
fi

## Check for pdftotext:
AC_PATH_PROG(PDFTOTEXT, pdftotext)
if test -z "$PDFTOTEXT"; then
   AC_MSG_WARN([
   pdftotext was not found in your PATH.  It is used for the fulltext indexation
   of PDF files.
   You can continue without it but you may miss fulltext searching capability
   of Invenio.  We recomend you to install it first and to rerun the configure
   script.  pdftotext is available from <http://www.foolabs.com/xpdf/home.html>.
   ])
fi

## Check for pdftotext:
AC_PATH_PROG(PDFINFO, pdfinfo)
if test -z "$PDFINFO"; then
   AC_MSG_WARN([
   pdfinfo was not found in your PATH.  It is used for gathering information on
   PDF files.
   You can continue without it but you may miss this feature of Invenio.
   We recomend you to install it first and to rerun the configure
   script.  pdftotext is available from <http://www.foolabs.com/xpdf/home.html>.
   ])
fi

## Check for pdftk:
AC_PATH_PROG(PDFTK, pdftk)
if test -z "$PDFTK"; then
   AC_MSG_WARN([
   pdftk was not found in your PATH.  It is used for the fulltext file stamping.
   You can continue without it but you may miss this feature of Invenio.
   We recomend you to install it first and to rerun the configure
   script.  pdftk is available from <http://www.accesspdf.com/pdftk/>.
   ])
fi

## Check for pdf2ps:
AC_PATH_PROG(PDF2PS, pdf2ps)
if test -z "$PDF2PS"; then
   AC_MSG_WARN([
   pdf2ps was not found in your PATH.  It is used in
   the WebSubmit module to convert submitted PDFs into PostScript.
   You can continue without it but you will miss some Invenio
   functionality.  We recommend you to install it first and to rerun
   the configure script.  pdf2ps is available from
   <http://www.cs.wisc.edu/~ghost/doc/AFPL/>.])
fi

## Check for pdftops:
AC_PATH_PROG(PDFTOPS, pdftops)
if test -z "$PDFTOPS"; then
   AC_MSG_WARN([
   pdftops was not found in your PATH.  It is used in
   the WebSubmit module to convert submitted PDFs into PostScript.
   You can continue without it but you will miss some Invenio
   functionality.  We recommend you to install it first and to rerun
   the configure script.  pdftops is available from
   <http://poppler.freedesktop.org/>.])
fi

## Check for pdfopt:
AC_PATH_PROG(PDFOPT, pdfopt)
if test -z "$PDFOPT"; then
   AC_MSG_WARN([
   pdfopt was not found in your PATH.  It is used in
   the WebSubmit module to linearized submitted PDFs.
   You can continue without it but you will miss some Invenio
   functionality.  We recommend you to install it first and to rerun
   the configure script.  pdfopt is available from
   <http://www.cs.wisc.edu/~ghost/doc/AFPL/>.])
fi

## Check for pdfimages:
AC_PATH_PROG(PDFTOPPM, pdftoppm)
if test -z "$PDFTOPPM"; then
   AC_MSG_WARN([
   pdftoppm was not found in your PATH.  It is used in
   the WebSubmit module to extract images from PDFs for OCR.
   You can continue without it but you will miss some Invenio
   functionality.  We recommend you to install it first and to rerun
   the configure script.  pdftoppm is available from
   <http://poppler.freedesktop.org/>.])
fi

## Check for pdfimages:
AC_PATH_PROG(PAMFILE, pdftoppm)
if test -z "$PAMFILE"; then
   AC_MSG_WARN([
   pamfile was not found in your PATH.  It is used in
   the WebSubmit module to retrieve the size of images extracted from PDFs
   for OCR.
   You can continue without it but you will miss some Invenio
   functionality.  We recommend you to install it first and to rerun
   the configure script.  pamfile is available as part of the netpbm utilities
   from:
   <http://netpbm.sourceforge.net/>.])
fi

## Check for ocroscript:
AC_PATH_PROG(OCROSCRIPT, ocroscript)
if test -z "$OCROSCRIPT"; then
   AC_MSG_WARN([
   If you plan to run OCR on your PDFs, then please install
   ocroscript now.  Otherwise you can safely continue.  You have also an
   option to install ocroscript later and edit invenio-local.conf to let
   Invenio know the path to ocroscript.
   ocroscript is available as part of OCROpus from
   <http://code.google.com/p/ocropus/>.
   NOTE: Since OCROpus is being actively developed and its api is continuosly
   changing, please install relase 0.3.1])
fi

## Check for pstotext:
AC_PATH_PROG(PSTOTEXT, pstotext)
if test -z "$PSTOTEXT"; then
   AC_MSG_WARN([
   pstotext was not found in your PATH.  It is used for the fulltext indexation
   of PDF and PostScript files.
   Please install pstotext.  Otherwise you can safely continue.  You have also an
   option to install pstotext later and edit invenio-local.conf to let
   Invenio know the path to pstotext.
   pstotext is available from <http://www.cs.wisc.edu/~ghost/doc/AFPL/>.
   ])
fi

## Check for ps2ascii:
AC_PATH_PROG(PSTOASCII, ps2ascii)
if test -z "$PSTOASCII"; then
   AC_MSG_WARN([
   ps2ascii was not found in your PATH.  It is used for the fulltext indexation
   of PostScript files.
   Please install ps2ascii.  Otherwise you can safely continue.  You have also an
   option to install ps2ascii later and edit invenio-local.conf to let
   Invenio know the path to ps2ascii.
   ps2ascii is available from <http://www.cs.wisc.edu/~ghost/doc/AFPL/>.
   ])
fi

## Check for any2djvu:
AC_PATH_PROG(ANY2DJVU, any2djvu)
if test -z "$ANY2DJVU"; then
   AC_MSG_WARN([
   any2djvu was not found in your PATH.  It is used in
   the WebSubmit module to convert documents to DJVU.
   Please install any2djvu.  Otherwise you can safely continue.  You have also an
   option to install any2djvu later and edit invenio-local.conf to let
   Invenio know the path to any2djvu.
   any2djvu is available from
   <http://djvu.sourceforge.net/>.])
fi

## Check for DJVUPS:
AC_PATH_PROG(DJVUPS, djvups)
if test -z "$DJVUPS"; then
   AC_MSG_WARN([
   djvups was not found in your PATH.  It is used in
   the WebSubmit module to convert documents from DJVU.
   Please install djvups.  Otherwise you can safely continue.  You have also an
   option to install djvups later and edit invenio-local.conf to let
   Invenio know the path to djvups.
   djvups is available from
   <http://djvu.sourceforge.net/>.])
fi

## Check for DJVUTXT:
AC_PATH_PROG(DJVUTXT, djvutxt)
if test -z "$DJVUTXT"; then
   AC_MSG_WARN([
   djvutxt was not found in your PATH.  It is used in
   the WebSubmit module to extract text from DJVU documents.
   You can continue without it but you will miss some Invenio
   functionality.  We recommend you to install it first and to rerun
   the configure script.  djvutxt is available from
   <http://djvu.sourceforge.net/>.])
fi

## Check for file:
AC_PATH_PROG(FILE, file)
if test -z "$FILE"; then
   AC_MSG_WARN([
   File was not found in your PATH.  It is used in
   the WebSubmit module to check the validity of the submitted files.
   You can continue without it but you will miss some Invenio
   functionality.  We recommend you to install it first and to rerun
   the configure script.  File is available from
   <ftp://ftp.astron.com/pub/file/>.])
fi

## Check for convert:
AC_PATH_PROG(CONVERT, convert)
if test -z "$CONVERT"; then
   AC_MSG_WARN([
   Convert was not found in your PATH.  It is used in
   the WebSubmit module to create an icon from a submitted picture.
   You can continue without it but you will miss some Invenio
   functionality.  We recommend you to install it first and to rerun
   the configure script.  Convert is available from
   <http://www.imagemagick.org/>.])
fi

## Check for CLISP:
AC_MSG_CHECKING(for clisp)
AC_ARG_WITH(clisp, AC_HELP_STRING([--with-clisp], [path to a specific CLISP binary (optional)]), CLISP=${withval})
if test -n "$CLISP"; then
   AC_MSG_RESULT($CLISP)
else
   AC_PATH_PROG(CLISP, clisp)
   if test -z "$CLISP"; then
      AC_MSG_WARN([
      GNU CLISP was not found in your PATH.  It is used by the WebStat
      module to produce statistics about Invenio usage.  (Alternatively,
      SBCL or CMUCL can be used instead of CLISP.)
      You can continue without it but you will miss this feature.  We
      recommend you to install it first (if you don't have neither CMUCL
      nor SBCL) and to rerun the configure script.
      GNU CLISP is available from <http://clisp.cons.org/>.])
   fi
fi

## Check for CMUCL:
AC_MSG_CHECKING(for cmucl)
AC_ARG_WITH(cmucl, AC_HELP_STRING([--with-cmucl], [path to a specific CMUCL binary (optional)]), CMUCL=${withval})
if test -n "$CMUCL"; then
   AC_MSG_RESULT($CMUCL)
else
   AC_PATH_PROG(CMUCL, cmucl)
   if test -z "$CMUCL"; then
      AC_MSG_CHECKING(for lisp) # CMUCL can also be installed under `lisp' exec name
      AC_PATH_PROG(CMUCL, lisp)
   fi
   if test -z "$CMUCL"; then
      AC_MSG_WARN([
      CMUCL was not found in your PATH.  It is used by the WebStat
      module to produce statistics about Invenio usage.  (Alternatively,
      CLISP or SBCL can be used instead of CMUCL.)
      You can continue without it but you will miss this feature.  We
      recommend you to install it first (if you don't have neither CLISP
      nor SBCL) and to rerun the configure script.
      CMUCL is available from <http://www.cons.org/cmucl/>.])
   fi
fi

## Check for SBCL:
AC_MSG_CHECKING(for sbcl)
AC_ARG_WITH(sbcl, AC_HELP_STRING([--with-sbcl], [path to a specific SBCL binary (optional)]), SBCL=${withval})
if test -n "$SBCL"; then
   AC_MSG_RESULT($SBCL)
else
   AC_PATH_PROG(SBCL, sbcl)
   if test -z "$SBCL"; then
      AC_MSG_WARN([
      SBCL was not found in your PATH.  It is used by the WebStat
      module to produce statistics about Invenio usage.  (Alternatively,
      CLISP or CMUCL can be used instead of SBCL.)
      You can continue without it but you will miss this feature.  We
      recommend you to install it first (if you don't have neither CLISP
      nor CMUCL) and to rerun the configure script.
      SBCL is available from <http://sbcl.sourceforge.net/>.])
   fi
fi

## Check for gnuplot:
AC_PATH_PROG(GNUPLOT, gnuplot)
if test -z "$GNUPLOT"; then
   AC_MSG_WARN([
   Gnuplot was not found in your PATH.  It is used by the BibRank
   module to produce graphs about download and citation history.
   You can continue without it but you will miss these graphs.  We
   recommend you to install it first and to rerun the configure script.
   Gnuplot is available from <http://www.gnuplot.info/>.])
fi

## Check for ffmpeg:
AC_PATH_PROG(FFMPEG, ffmpeg)
AC_PATH_PROG(FFPROBE, ffprobe)
if test -z "$FFMPEG"; then
   AC_MSG_WARN([
   FFmpeg was not found in your PATH. It is used by the BibEncode
   module to for video encoding.
   You can continue without but you will not be able to use BibEncode
   and no video submission workflows are thereby possible.
   We recommend you to install it first if you would like to support video
   submissions and to rerun the configure script.
   FFmpeg is available from <http://www.ffmpeg.org/>.])
fi

## Check for mediainfo:
AC_PATH_PROG(MEDIAINFO, mediainfo)
if test -z "$MEDIAINFO"; then
   AC_MSG_WARN([
   Mediainfo was not found in your PATH. It is used by the BibEncode
   module to for video encoding and media metadata handling.
   You can continue without but you will not be able to use BibEncode
   and no video submission workflows are thereby possible.
   We recommend you to install it first if you would like to support video
   submissions and to rerun the configure script.
   Mediainfo is available from <http://mediainfo.sourceforge.net/>.])
fi

## Check for ffmpeg

## Substitute variables:
AC_SUBST(VERSION)
AC_SUBST(OPENOFFICE_PYTHON)
AC_SUBST(MYSQL)
AC_SUBST(PYTHON)
AC_SUBST(GZIP)
AC_SUBST(GUNZIP)
AC_SUBST(TAR)
AC_SUBST(WGET)
AC_SUBST(MD5SUM)
AC_SUBST(PS2PDF)
AC_SUBST(GS)
AC_SUBST(PDFTOTEXT)
AC_SUBST(PDFTK)
AC_SUBST(PDF2PS)
AC_SUBST(PDFTOPS)
AC_SUBST(PDFOPT)
AC_SUBST(PDFTOPPM)
AC_SUBST(OCROSCRIPT)
AC_SUBST(PSTOTEXT)
AC_SUBST(PSTOASCII)
AC_SUBST(ANY2DJVU)
AC_SUBST(DJVUPS)
AC_SUBST(DJVUTXT)
AC_SUBST(FILE)
AC_SUBST(CONVERT)
AC_SUBST(GNUPLOT)
AC_SUBST(CLISP)
AC_SUBST(CMUCL)
AC_SUBST(SBCL)
AC_SUBST(CACHEDIR)
AC_SUBST(FFMPEG)
AC_SUBST(MEDIAINFO)
AC_SUBST(FFPROBE)
AC_SUBST(localstatedir, `eval echo "${localstatedir}"`)

## Define output files:
AC_CONFIG_FILES([config.nice  \
     Makefile \
     po/Makefile.in \
     config/Makefile \
     config/invenio-autotools.conf \
     modules/Makefile \
     modules/webauthorprofile/Makefile \
     modules/webauthorprofile/lib/Makefile \
     modules/webauthorprofile/bin/Makefile \
     modules/webauthorprofile/bin/webauthorprofile \
     modules/bibauthorid/Makefile \
     modules/bibauthorid/bin/Makefile \
     modules/bibauthorid/bin/bibauthorid \
     modules/bibauthorid/doc/Makefile \
     modules/bibauthorid/doc/admin/Makefile \
     modules/bibauthorid/doc/hacking/Makefile \
     modules/bibauthorid/lib/Makefile \
     modules/bibauthorid/etc/Makefile \
     modules/bibauthorid/etc/name_authority_files/Makefile \
     modules/bibauthorid/etc/templates/Makefile \
     modules/bibauthorid/web/Makefile \
     modules/bibauthorid/css/Makefile \
     modules/bibauthorid/fonts/Makefile \
     modules/bibauthority/Makefile \
     modules/bibauthority/bin/Makefile \
     modules/bibauthority/doc/Makefile \
     modules/bibauthority/doc/admin/Makefile \
     modules/bibauthority/doc/hacking/Makefile \
     modules/bibauthority/lib/Makefile \
     modules/bibauthority/web/Makefile \
     modules/bibcatalog/Makefile \
     modules/bibcatalog/bin/Makefile \
     modules/bibcatalog/bin/bibcatalog \
     modules/bibcatalog/doc/Makefile \
     modules/bibcatalog/doc/admin/Makefile \
     modules/bibcatalog/doc/hacking/Makefile
     modules/bibcatalog/lib/Makefile \
     modules/bibcatalog/lib/ticket_templates/Makefile \
     modules/bibcheck/Makefile \
     modules/bibcheck/doc/Makefile \
     modules/bibcheck/doc/hacking/Makefile \
     modules/bibcheck/etc/Makefile \
     modules/bibcheck/bin/Makefile \
     modules/bibcheck/lib/Makefile \
     modules/bibcheck/lib/plugins/Makefile \
     modules/bibcheck/bin/bibcheck \
     modules/bibcirculation/Makefile \
     modules/bibcirculation/bin/Makefile \
     modules/bibcirculation/bin/bibcircd \
     modules/bibcirculation/doc/Makefile \
     modules/bibcirculation/doc/admin/Makefile \
     modules/bibcirculation/doc/hacking/Makefile
     modules/bibcirculation/lib/Makefile \
     modules/bibcirculation/web/Makefile \
     modules/bibcirculation/web/admin/Makefile \
     modules/bibclassify/Makefile \
     modules/bibclassify/bin/Makefile \
     modules/bibclassify/bin/bibclassify \
     modules/bibclassify/doc/Makefile \
     modules/bibclassify/doc/admin/Makefile \
     modules/bibclassify/doc/hacking/Makefile \
     modules/bibclassify/etc/Makefile \
     modules/bibclassify/lib/Makefile \
     modules/bibconvert/Makefile \
     modules/bibconvert/bin/Makefile \
     modules/bibconvert/bin/bibconvert \
     modules/bibconvert/doc/Makefile \
     modules/bibconvert/doc/admin/Makefile \
     modules/bibconvert/doc/hacking/Makefile \
     modules/bibconvert/etc/Makefile \
     modules/bibconvert/lib/Makefile \
     modules/bibdocfile/Makefile \
     modules/bibdocfile/bin/bibdocfile \
     modules/bibdocfile/bin/Makefile \
     modules/bibdocfile/doc/Makefile \
     modules/bibdocfile/doc/hacking/Makefile \
     modules/bibdocfile/lib/Makefile \
     modules/bibrecord/Makefile \
     modules/bibrecord/bin/Makefile \
     modules/bibrecord/bin/xmlmarc2textmarc \
     modules/bibrecord/bin/textmarc2xmlmarc \
     modules/bibrecord/bin/xmlmarclint \
     modules/bibrecord/doc/Makefile \
     modules/bibrecord/doc/admin/Makefile \
     modules/bibrecord/doc/hacking/Makefile \
     modules/bibrecord/etc/Makefile \
     modules/bibrecord/lib/Makefile \
     modules/bibedit/Makefile \
     modules/bibedit/bin/Makefile \
     modules/bibedit/bin/bibedit \
     modules/bibedit/doc/Makefile \
     modules/bibedit/doc/admin/Makefile \
     modules/bibedit/doc/hacking/Makefile \
     modules/bibedit/etc/Makefile \
     modules/bibedit/lib/Makefile \
     modules/bibedit/lib/ticket_templates/Makefile \
     modules/bibedit/web/Makefile \
     modules/bibencode/Makefile \
     modules/bibencode/bin/Makefile \
     modules/bibencode/bin/bibencode \
     modules/bibencode/lib/Makefile \
     modules/bibencode/etc/Makefile \
     modules/bibencode/www/Makefile \
     modules/bibexport/Makefile \
     modules/bibexport/bin/Makefile \
     modules/bibexport/bin/bibexport \
     modules/bibexport/doc/Makefile \
     modules/bibexport/doc/admin/Makefile \
     modules/bibexport/doc/hacking/Makefile
     modules/bibexport/etc/Makefile \
     modules/bibexport/lib/Makefile \
     modules/bibexport/web/Makefile \
     modules/bibexport/web/admin/Makefile \
     modules/bibfield/Makefile \
     modules/bibfield/lib/Makefile \
     modules/bibfield/lib/functions/Makefile \
     modules/bibfield/etc/Makefile \
     modules/bibformat/Makefile \
     modules/bibformat/bin/Makefile \
     modules/bibformat/bin/bibreformat \
     modules/bibformat/doc/Makefile \
     modules/bibformat/doc/admin/Makefile \
     modules/bibformat/doc/hacking/Makefile \
     modules/bibformat/etc/Makefile \
     modules/bibformat/etc/format_templates/Makefile \
     modules/bibformat/etc/output_formats/Makefile \
     modules/bibformat/lib/Makefile \
     modules/bibformat/lib/elements/Makefile \
     modules/bibformat/web/Makefile \
     modules/bibformat/web/admin/Makefile \
     modules/oaiharvest/Makefile \
     modules/oaiharvest/bin/Makefile \
     modules/oaiharvest/bin/oaiharvest \
     modules/oaiharvest/doc/Makefile \
     modules/oaiharvest/doc/admin/Makefile \
     modules/oaiharvest/doc/hacking/Makefile \
     modules/oaiharvest/lib/Makefile \
     modules/oaiharvest/web/Makefile \
     modules/oaiharvest/web/admin/Makefile \
     modules/oairepository/Makefile \
     modules/oairepository/bin/Makefile \
     modules/oairepository/bin/oairepositoryupdater \
     modules/oairepository/doc/Makefile \
     modules/oairepository/doc/admin/Makefile \
     modules/oairepository/doc/hacking/Makefile \
     modules/oairepository/etc/Makefile \
     modules/oairepository/lib/Makefile \
     modules/oairepository/web/Makefile \
     modules/oairepository/web/admin/Makefile \
     modules/pdfchecker/Makefile \
     modules/pdfchecker/bin/Makefile \
     modules/pdfchecker/bin/arxiv-pdf-checker \
     modules/pdfchecker/lib/Makefile \
     modules/bibindex/Makefile \
     modules/bibindex/bin/Makefile \
     modules/bibindex/bin/bibindex \
     modules/bibindex/bin/bibstat \
     modules/bibindex/doc/Makefile \
     modules/bibindex/doc/admin/Makefile \
     modules/bibindex/doc/hacking/Makefile \
     modules/bibindex/lib/Makefile \
     modules/bibindex/lib/tokenizers/Makefile \
     modules/bibindex/web/Makefile \
     modules/bibindex/web/admin/Makefile \
     modules/bibknowledge/Makefile \
     modules/bibknowledge/lib/Makefile \
     modules/bibknowledge/doc/Makefile \
     modules/bibknowledge/doc/admin/Makefile \
     modules/bibknowledge/doc/hacking/Makefile \
     modules/bibmatch/Makefile \
     modules/bibmatch/bin/Makefile \
     modules/bibmatch/bin/bibmatch \
     modules/bibmatch/doc/Makefile \
     modules/bibmatch/doc/admin/Makefile \
     modules/bibmatch/doc/hacking/Makefile \
     modules/bibmatch/etc/Makefile \
     modules/bibmatch/lib/Makefile \
     modules/bibmerge/Makefile \
     modules/bibmerge/bin/Makefile \
     modules/bibmerge/doc/Makefile \
     modules/bibmerge/doc/admin/Makefile \
     modules/bibmerge/doc/hacking/Makefile \
     modules/bibmerge/lib/Makefile \
     modules/bibmerge/web/Makefile \
     modules/bibmerge/web/admin/Makefile \
     modules/bibrank/Makefile \
     modules/bibrank/bin/Makefile \
     modules/bibrank/bin/bibrank \
     modules/bibrank/bin/bibrankgkb \
     modules/bibrank/doc/Makefile \
     modules/bibrank/doc/admin/Makefile \
     modules/bibrank/doc/hacking/Makefile \
     modules/bibrank/etc/Makefile \
     modules/bibrank/etc/bibrankgkb.cfg \
     modules/bibrank/etc/demo_jif.cfg \
     modules/bibrank/etc/template_single_tag_rank_method.cfg \
     modules/bibrank/lib/Makefile \
     modules/bibrank/web/Makefile \
     modules/bibrank/web/admin/Makefile \
     modules/bibsched/Makefile \
     modules/bibsched/bin/Makefile \
     modules/bibsched/bin/bibsched \
     modules/bibsched/bin/bibtaskex \
     modules/bibsched/bin/bibtasklet \
     modules/bibsched/doc/Makefile \
     modules/bibsched/doc/admin/Makefile \
     modules/bibsched/doc/hacking/Makefile \
     modules/bibsched/lib/Makefile \
     modules/bibsched/lib/tasklets/Makefile \
     modules/bibupload/Makefile \
     modules/bibsort/Makefile \
     modules/bibsort/bin/Makefile \
     modules/bibsort/bin/bibsort \
     modules/bibsort/lib/Makefile \
     modules/bibsort/etc/Makefile \
     modules/bibsort/doc/Makefile \
     modules/bibsort/doc/admin/Makefile \
     modules/bibsort/doc/hacking/Makefile \
     modules/bibsort/web/Makefile \
     modules/bibsort/web/admin/Makefile \
     modules/bibsword/Makefile \
     modules/bibsword/bin/Makefile \
     modules/bibsword/bin/bibsword \
     modules/bibsword/doc/Makefile \
     modules/bibsword/doc/admin/Makefile \
     modules/bibsword/doc/hacking/Makefile \
     modules/bibsword/lib/Makefile \
     modules/bibsword/etc/Makefile \
     modules/bibupload/bin/Makefile \
     modules/bibupload/bin/bibupload \
     modules/bibupload/bin/batchuploader \
     modules/bibupload/doc/Makefile \
     modules/bibupload/doc/admin/Makefile \
     modules/bibupload/doc/hacking/Makefile \
     modules/bibupload/lib/Makefile \
     modules/elmsubmit/Makefile \
     modules/elmsubmit/bin/Makefile \
     modules/elmsubmit/bin/elmsubmit \
     modules/elmsubmit/doc/Makefile \
     modules/elmsubmit/doc/admin/Makefile \
     modules/elmsubmit/doc/hacking/Makefile \
     modules/elmsubmit/etc/Makefile \
     modules/elmsubmit/etc/elmsubmit.cfg \
     modules/elmsubmit/lib/Makefile \
     modules/miscutil/Makefile \
     modules/miscutil/bin/Makefile \
     modules/miscutil/bin/dbdump \
     modules/miscutil/bin/dbexec \
     modules/miscutil/bin/inveniocfg \
     modules/miscutil/bin/plotextractor \
     modules/miscutil/bin/hepdataharvest \
     modules/miscutil/bin/bibtex \
     modules/miscutil/demo/Makefile \
     modules/miscutil/doc/Makefile \
     modules/miscutil/doc/hacking/Makefile \
     modules/miscutil/etc/Makefile \
     modules/miscutil/etc/bash_completion.d/Makefile \
     modules/miscutil/etc/bash_completion.d/inveniocfg \
     modules/miscutil/etc/ckeditor_scientificchar/Makefile \
     modules/miscutil/etc/ckeditor_scientificchar/dialogs/Makefile \
     modules/miscutil/etc/ckeditor_scientificchar/lang/Makefile \
     modules/miscutil/lib/Makefile \
     modules/miscutil/lib/upgrades/Makefile \
     modules/miscutil/sql/Makefile \
     modules/miscutil/web/Makefile \
     modules/webaccess/Makefile \
     modules/webaccess/bin/Makefile \
     modules/webaccess/bin/authaction \
     modules/webaccess/bin/webaccessadmin \
     modules/webaccess/doc/Makefile \
     modules/webaccess/doc/admin/Makefile \
     modules/webaccess/doc/hacking/Makefile \
     modules/webaccess/lib/Makefile \
     modules/webaccess/web/Makefile \
     modules/webaccess/web/admin/Makefile \
     modules/webalert/Makefile \
     modules/webalert/bin/Makefile \
     modules/webalert/bin/alertengine \
     modules/webalert/doc/Makefile \
     modules/webalert/doc/admin/Makefile \
     modules/webalert/doc/hacking/Makefile \
     modules/webalert/lib/Makefile \
     modules/webalert/web/Makefile \
     modules/webauthorlist/Makefile \
     modules/webauthorlist/lib/Makefile \
     modules/webauthorlist/web/Makefile \
     modules/webbasket/Makefile \
     modules/webbasket/doc/Makefile \
     modules/webbasket/doc/admin/Makefile \
     modules/webbasket/doc/hacking/Makefile \
     modules/webbasket/lib/Makefile \
     modules/webbasket/web/Makefile \
     modules/webcomment/Makefile \
     modules/webcomment/doc/Makefile \
     modules/webcomment/doc/admin/Makefile \
     modules/webcomment/doc/hacking/Makefile \
     modules/webcomment/lib/Makefile \
     modules/webcomment/web/Makefile \
     modules/webcomment/web/admin/Makefile \
     modules/webhelp/Makefile \
     modules/webhelp/web/Makefile \
     modules/webhelp/web/admin/Makefile \
     modules/webhelp/web/admin/howto/Makefile \
     modules/webhelp/web/hacking/Makefile \
     modules/webjournal/Makefile \
     modules/webjournal/etc/Makefile \
     modules/webjournal/doc/Makefile \
     modules/webjournal/doc/admin/Makefile \
     modules/webjournal/doc/hacking/Makefile \
     modules/webjournal/lib/Makefile \
     modules/webjournal/lib/elements/Makefile \
     modules/webjournal/lib/widgets/Makefile \
     modules/webjournal/web/Makefile \
     modules/webjournal/web/admin/Makefile \
     modules/weblinkback/Makefile \
     modules/weblinkback/lib/Makefile \
     modules/weblinkback/web/Makefile \
     modules/weblinkback/web/admin/Makefile \
     modules/webmessage/Makefile \
     modules/webmessage/bin/Makefile \
     modules/webmessage/bin/webmessageadmin \
     modules/webmessage/doc/Makefile \
     modules/webmessage/doc/admin/Makefile \
     modules/webmessage/doc/hacking/Makefile \
     modules/webmessage/lib/Makefile \
     modules/webmessage/web/Makefile \
     modules/websearch/Makefile \
     modules/websearch/bin/Makefile \
     modules/websearch/bin/webcoll \
     modules/websearch/doc/Makefile \
     modules/websearch/doc/admin/Makefile \
     modules/websearch/doc/hacking/Makefile \
     modules/websearch/lib/Makefile \
     modules/websearch/lib/services/Makefile \
     modules/websearch/web/Makefile \
     modules/websearch/web/admin/Makefile \
     modules/websession/Makefile \
     modules/websession/bin/Makefile \
     modules/websession/bin/inveniogc \
     modules/websession/doc/Makefile \
     modules/websession/doc/admin/Makefile \
     modules/websession/doc/hacking/Makefile \
     modules/websession/lib/Makefile \
     modules/websession/web/Makefile \
     modules/webstat/Makefile \
     modules/webstat/bin/Makefile \
     modules/webstat/bin/webstat \
     modules/webstat/bin/webstatadmin \
     modules/webstat/doc/Makefile \
     modules/webstat/doc/admin/Makefile \
     modules/webstat/doc/hacking/Makefile \
     modules/webstat/etc/Makefile \
     modules/webstat/lib/Makefile \
     modules/webstyle/Makefile \
     modules/webstyle/bin/Makefile \
     modules/webstyle/bin/gotoadmin \
     modules/webstyle/bin/webdoc \
     modules/webstyle/css/Makefile \
     modules/webstyle/doc/Makefile \
     modules/webstyle/doc/admin/Makefile \
     modules/webstyle/doc/hacking/Makefile \
     modules/webstyle/etc/Makefile \
     modules/webstyle/img/Makefile \
     modules/webstyle/lib/Makefile \
     modules/webstyle/lib/goto_plugins/Makefile \
     modules/websubmit/Makefile \
     modules/websubmit/bin/Makefile \
     modules/websubmit/bin/inveniounoconv \
     modules/websubmit/bin/websubmitadmin \
     modules/websubmit/doc/Makefile \
     modules/websubmit/doc/admin/Makefile \
     modules/websubmit/doc/hacking/Makefile \
     modules/websubmit/etc/Makefile \
     modules/websubmit/lib/Makefile \
     modules/websubmit/lib/functions/Makefile \
     modules/websubmit/web/Makefile \
     modules/websubmit/web/admin/Makefile \
     modules/docextract/Makefile \
     modules/docextract/bin/Makefile \
     modules/docextract/bin/docextract \
     modules/docextract/bin/refextract \
     modules/docextract/bin/convert_journals \
     modules/docextract/doc/Makefile \
     modules/docextract/lib/Makefile \
     modules/docextract/etc/Makefile \
     modules/docextract/doc/admin/Makefile \
     modules/docextract/doc/hacking/Makefile \
     ])

## Finally, write output files:
AC_OUTPUT

## Write help:
AC_MSG_RESULT([****************************************************************************])
AC_MSG_RESULT([** Your Invenio installation is now ready for building.                   **])
AC_MSG_RESULT([** You have entered the following parameters:                             **])
AC_MSG_RESULT([**   - Invenio main install directory: ${prefix}])
AC_MSG_RESULT([**   - Python executable: $PYTHON])
AC_MSG_RESULT([**   - MySQL client executable: $MYSQL])
AC_MSG_RESULT([**   - CLISP executable: $CLISP])
AC_MSG_RESULT([**   - CMUCL executable: $CMUCL])
AC_MSG_RESULT([**   - SBCL executable: $SBCL])
AC_MSG_RESULT([** Here are the steps to continue the building process:                   **])
AC_MSG_RESULT([**   1) Type 'make' to build your Invenio system.                         **])
AC_MSG_RESULT([**   2) Type 'make install' to install your Invenio system.               **])
AC_MSG_RESULT([** After that you can start customizing your installation as documented   **])
AC_MSG_RESULT([** in the INSTALL file (i.e. edit invenio.conf, run inveniocfg, etc).     **])
AC_MSG_RESULT([** Good luck, and thanks for choosing Invenio.                            **])
AC_MSG_RESULT([**              -- Invenio Development Team <info@invenio-software.org>   **])
AC_MSG_RESULT([****************************************************************************])

## end of file
