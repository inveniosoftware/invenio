## $Id$
## Purpose: CERN Document Server Software (CDSware) main configure.ac file.
## Note: If you change this file, please run "autoreconf" to regenerate the "configure" script.

## This file is part of the CERN Document Server Software (CDSware).
## Copyright (C) 2002 CERN.
##
## The CDSware is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## The CDSware is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.  
##
## You should have received a copy of the GNU General Public License
## along with CDSware; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

## Initialize autoconf and automake:
AC_INIT(cdsware, 0.1.2.20040119, cds.support@cern.ch)
AM_INIT_AUTOMAKE(cdsware, 0.1.2.20040119)

## Check for install:
AC_PROG_INSTALL

## Define WEBDIR directory:
AC_ARG_WITH(webdir, AC_HELP_STRING([--with-webdir], [specify where the web files go (e.g. /var/www/cdsware/)]), WEBDIR=${withval})
if test -z "$WEBDIR"; then
   AC_MSG_ERROR([
   You have not used the "--with-webdir" argument that should define the installation directory for Web programs and documents.  
   Example: "--with-webdir=/var/www/cdsware/".])
fi   

## Define WEBURL URL:
AC_ARG_WITH(weburl, AC_HELP_STRING([--with-weburl], [specify URL where web files will be reached (e.g. http://cdsdev.cern.ch/cdsware/)]), WEBURL=${withval})
if test -z "$WEBURL"; then
   AC_MSG_ERROR([
   You have not used the "--with-weburl" argument that should define the corresponding URL where the site will be reached.  
   Example: "--with-weburl=http://webserver.domain.com/cdsware/".])
fi   

## Define DBHOST database host:
AC_ARG_WITH(dbhost, AC_HELP_STRING([--with-dbhost], [specify DB server (e.g. cdsdb.cern.ch)]), DBHOST=${withval})
if test -z "$DBHOST"; then
   AC_MSG_ERROR([
   You have not used the "--with-dbhost" argument that should define which DB server to use.  
   Example: "--with-dbhost=sqlserver.domain.com".])
fi   

## Define DBNAME database name:
AC_ARG_WITH(dbname, AC_HELP_STRING([--with-dbname], [specify DB name (e.g. cdsware)]), DBNAME=${withval})
if test -z "$DBNAME"; then
   AC_MSG_ERROR([
   You have not used the "--with-dbname" argument that should define DB name.  
   Example: "--with-dbname=cdsware".])
fi   

## Define DBUSER user name:
AC_ARG_WITH(dbuser, AC_HELP_STRING([--with-dbuser], [specify DB user name (e.g. cdsware)]), DBUSER=${withval})
if test -z "$DBUSER"; then
   AC_MSG_ERROR([
   You have not used the "--with-dbuser" argument that should define DB user name.  
   Example: "--with-dbuser=cdsware".])
fi   

## Define DBPASS user password:
AC_ARG_WITH(dbpass, AC_HELP_STRING([--with-dbpass], [specify DB user password (e.g. myp1ss)]), DBPASS=${withval})
if test -z "$DBPASS"; then
   AC_MSG_ERROR([
   You have not used the "--with-dbpass" argument that should define DB user password.  
   Example: "--with-dbpass=myp1ss".])
fi   

## Check for WML:
AC_PATH_PROG(WML, wml)
if test -z "$WML"; then
   AC_MSG_ERROR([
   WML (Website META Language) was not found in your PATH.  Please install it first.  
   Available from <http://www.engelschall.com/sw/wml/>.])
fi

## Check for MySQL client:
AC_PATH_PROG(MYSQL, mysql)
if test -z "$MYSQL"; then
   AC_MSG_ERROR([
   MySQL command-line client was not found in your PATH.  Please install it first.
   Available from <http://mysql.com/>.])
fi

## Check for Python:
AC_MSG_CHECKING(for python)
AC_ARG_WITH(python, AC_HELP_STRING([--with-python], [path to a specific Python binary [optional]]), PYTHON=${withval})
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

## Check for Python version and modules:
AC_MSG_CHECKING(for required Python modules)
$PYTHON configure-tests.py
if test $? -ne 0; then
   AC_MSG_ERROR([Please fix the above Python problems before continuing.])
fi
AC_MSG_RESULT(found)

## Check for PHP:
AC_PATH_PROG(PHP, php)
if test -z "$PHP"; then
   AC_MSG_ERROR([
   PHP standalone command-line executable (i.e. not compiled as Apache module!) 
   was not found in your PATH.  Please install it first.
   Available from <http://www.php.net/manual/en/install.commandline.php>.])
fi

## Check for Acrobat Reader:
AC_PATH_PROG(ACROREAD, acroread)
if test -z "$ACROREAD"; then
   AC_MSG_WARN([
   Acrobat Reader was not found in your PATH.  It is used in 
   the WebSubmit module for automatic conversion of submitted documents.  
   You can continue without it but you will miss some CDSware 
   functionality.  We recommend you to install it first and to rerun 
   the configure script.  Acrobat Reader is available from
   <http://www.adobe.com/products/acrobat/readstep.html>.])
fi

## Check for Lynx:
AC_PATH_PROG(LYNX, lynx)
if test -z "$LYNX"; then
   AC_MSG_WARN([
   Lynx was not found in your PATH.  It is used in 
   the WebSubmit module to fetch files from URLs given by
   submitters.
   You can continue without it but you will miss some CDSware 
   functionality.  We recommend you to install it first and to rerun 
   the configure script.  Lynx is available from
   <http://lynx.browser.org/>.])
fi

## Check for Gzip:
AC_PATH_PROG(GZIP, gzip)
if test -z "$GZIP"; then
   AC_MSG_WARN([
   Gzip was not found in your PATH.  It is used in 
   the WebSubmit module to compress the data submitted in an archive.
   You can continue without it but you will miss some CDSware 
   functionality.  We recommend you to install it first and to rerun 
   the configure script.  Gzip is available from
   <http://www.gzip.org/>.])
fi

## Check for Gunzip:
AC_PATH_PROG(GUNZIP, gunzip)
if test -z "$GUNZIP"; then
   AC_MSG_WARN([
   Gunzip was not found in your PATH.  It is used in 
   the WebSubmit module to correctly deal with submitted compressed
   files.
   You can continue without it but you will miss some CDSware 
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
   You can continue without it but you will miss some CDSware 
   functionality.  We recommend you to install it first and to rerun 
   the configure script.  Tar is available from
   <ftp://prep.ai.mit.edu/pub/gnu/tar/>.])
fi

## Check for ps2pdf:
AC_PATH_PROG(PS2PDF, ps2pdf)
if test -z "$PS2PDF"; then
   AC_MSG_WARN([
   ps2pdf was not found in your PATH.  It is used in 
   the WebSubmit module to convert submitted PostScripts into PDF.
   You can continue without it but you will miss some CDSware 
   functionality.  We recommend you to install it first and to rerun 
   the configure script.  PS2PDF is available from
   <http://www.cs.wisc.edu/~ghost/doc/AFPL/6.50/Ps2pdf.htm>.])
fi

## Check for pdftotext:
AC_PATH_PROG(PDFTOTEXT, pdftotext)
if test -z "$PDFTOTEXT"; then
   AC_MSG_WARN([
   pdftotext was not found in your PATH.  It is used for the fulltext indexation 
   of PDF files.
   You can continue without it but you may miss fulltext searching capability 
   of CDSware.  We recomend you to install it first and to rerun the configure 
   script.  pdftotext is available from <http://www.foolabs.com/xpdf/home.html>. 
   ])
fi

## Check for pstotext:
AC_PATH_PROG(PSTOTEXT, pstotext)
if test -z "$PSTOTEXT"; then
   AC_MSG_WARN([
   pstotext was not found in your PATH.  It is used for the fulltext indexation 
   of PDF and PostScript files.
   You can continue without it but you may miss fulltext searching capability 
   of CDSware.  We recomend you to install it first and to rerun the configure 
   script.  pstotext is available from <http://www.cs.wisc.edu/~ghost/doc/AFPL/>.
   ])
fi

## Check for ps2ascii:
AC_PATH_PROG(PSTOASCII, ps2ascii)
if test -z "$PSTOASCII"; then
   AC_MSG_WARN([
   ps2ascii was not found in your PATH.  It is used for the fulltext indexation 
   of PostScript files.
   You can continue without it but you may miss fulltext searching capability 
   of CDSware.  We recomend you to install it first and to rerun the configure 
   script.  ps2ascii is available from <http://www.cs.wisc.edu/~ghost/doc/AFPL/>.
   ])
fi

## Check for antiword:
AC_PATH_PROG(ANTIWORD, antiword)
if test -z "$ANTIWORD"; then
   AC_MSG_WARN([
   antiword was not found in your PATH.  It is used for the fulltext indexation 
   of Microsoft Word files.
   You can continue without it but you may miss fulltext searching capability 
   of CDSware.  We recomend you to install it first and to rerun the configure 
   script.  antiword is available from <http://www.winfield.demon.nl/index.html>. 
   ])
fi

## Check for catdoc:
AC_PATH_PROG(CATDOC, catdoc)
if test -z "$CATDOC"; then
   AC_MSG_WARN([
   catdoc was not found in your PATH.  It is used for the fulltext indexation 
   of Microsoft Word files.
   You can continue without it but you may miss fulltext searching capability 
   of CDSware.  We recomend you to install it first and to rerun the configure 
   script.  catdoc is available from <http://www.ice.ru/~vitus/catdoc/index.html>.
   ])
fi

## Check for wvText:
AC_PATH_PROG(WVTEXT, wvText)
if test -z "$WVTEXT"; then
   AC_MSG_WARN([
   wvText was not found in your PATH.  It is used for the fulltext indexation 
   of Microsoft Word files.
   You can continue without it but you may miss fulltext searching capability 
   of CDSware.  We recomend you to install it first and to rerun the configure 
   script.  wvText is available from <http://sourceforge.net/projects/wvware>.
   ])
fi     

## Check for ppthtml:
AC_PATH_PROG(PPTHTML, ppthtml)
if test -z "$PPTHTML"; then
   AC_MSG_WARN([
   ppthtml was found in your PATH. It is used for the fulltext indexation 
   of Microsoft PowerPoint files.
   You can continue without it but you may miss fulltext searching capability 
   of CDSware.  We recomend you to install it first and to rerun the configure 
   script.  ppthtml is available from <http://www.xlhtml.org/>.
   ])
fi

## Check for xlhtml:
AC_PATH_PROG(XLHTML, xlhtml)
if test -z "$XLHTML"; then
   AC_MSG_WARN([
   xlhtml was found in your PATH. It is used for the fulltext indexation 
   of Microsoft Excel files.
   You can continue without it but you may miss fulltext searching capability 
   of CDSware.  We recomend you to install it first and to rerun the configure 
   script.  xlhtml is available from <http://chicago.sourceforge.net/xlhtml/>.
   ])
fi

## Check for html2text:
AC_PATH_PROG(HTMLTOTEXT, html2text)
if test -z "$HTMLTOTEXT"; then
   AC_MSG_WARN([
   html2text was found in your PATH. It is used for the fulltext indexation 
   of Microsoft PowerPoint and Excel files.
   You can continue without it but you may miss fulltext searching capability 
   of CDSware.  We recomend you to install it first and to rerun the configure 
   script.  html2text is available from <http://userpage.fu-berlin.de/~mbayer/tools/html2text.html>.
   ])
fi

## Check for Giftext:
AC_PATH_PROG(GIFTEXT, giftext)
if test -z "$GIFTEXT"; then
   AC_MSG_WARN([
   Giftext was not found in your PATH.  It is used in 
   the WebSubmit module to create an icon from a submitted picture.
   You can continue without it but you will miss some CDSware 
   functionality.  We recommend you to install it first and to rerun 
   the configure script.  Giftext is available from
   <http://prtr-13.ucsc.edu/~badger/software/libungif/getting.shtml>.])
fi

## Check for File:
AC_PATH_PROG(FILE, file)
if test -z "$FILE"; then
   AC_MSG_WARN([
   File was not found in your PATH.  It is used in 
   the WebSubmit module to check the validity of the submitted files.
   You can continue without it but you will miss some CDSware 
   functionality.  We recommend you to install it first and to rerun 
   the configure script.  File is available from
   <ftp://ftp.astron.com/pub/file/>.])
fi

## Check for Djpeg:
AC_PATH_PROG(DJPEG, djpeg)
if test -z "$DJPEG"; then
   AC_MSG_WARN([
   Djpeg was not found in your PATH.  It is used in 
   the WebSubmit module to create an icon from a submitted picture.
   You can continue without it but you will miss some CDSware 
   functionality.  We recommend you to install it first and to rerun 
   the configure script.  Djpeg is available from
   <http://www.ijg.org/files>.])
fi

## Check for Convert:
AC_PATH_PROG(CONVERT, convert)
if test -z "$CONVERT"; then
   AC_MSG_WARN([
   Convert was not found in your PATH.  It is used in 
   the WebSubmit module to create an icon from a submitted picture.
   You can continue without it but you will miss some CDSware 
   functionality.  We recommend you to install it first and to rerun 
   the configure script.  Convert is available from
   <http://www.imagemagick.org/>.])
fi

## Check for Giftext:
AC_PATH_PROG(GIFTEXT, giftext)
if test -z "$GIFTEXT"; then
   AC_MSG_WARN([
   Giftext was not found in your PATH.  It is used in 
   the WebSubmit module to create an icon from a submitted picture.
   You can continue without it but you will miss some CDSware 
   functionality.  We recommend you to install it first and to rerun 
   the configure script.  Giftext is available from
   <http://prtr-13.ucsc.edu/~badger/software/libungif/getting.shtml>.])
fi

## Check for Gifinter:
AC_PATH_PROG(GIFINTER, gifinter)
if test -z "$GIFINTER"; then
   AC_MSG_WARN([
   Gifinter was not found in your PATH.  It is used in 
   the WebSubmit module to create an icon from a submitted picture.
   You can continue without it but you will miss some CDSware 
   functionality.  We recommend you to install it first and to rerun 
   the configure script.  Gifinter is available from
   <http://prtr-13.ucsc.edu/~badger/software/libungif/getting.shtml>.])
fi

## Check for Gifrsize:
AC_PATH_PROG(GIFRSIZE, gifrsize)
if test -z "$GIFRSIZE"; then
   AC_MSG_WARN([
   Gifrsize was not found in your PATH.  It is used in 
   the WebSubmit module to create an icon from a submitted picture.
   You can continue without it but you will miss some CDSware 
   functionality.  We recommend you to install it first and to rerun 
   the configure script.  Gifrsize is available from
   <http://prtr-13.ucsc.edu/~badger/software/libungif/getting.shtml>.])
fi

## Check for jpegsize:
AC_PATH_PROG(JPEGSIZE, jpegsize)
if test -z "$JPEGSIZE"; then
   AC_MSG_WARN([
   jpegsize was not found in your PATH.  It is used in 
   the WebSubmit module to create an icon from a submitted picture.
   You can continue without it but you will miss some CDSware 
   functionality.  We recommend you to install it first and to rerun 
   the configure script.  Jpegsize is available from
   <http://www.squarebox.co.uk/download/>.])
fi

## Check for Ppmtogif:
AC_PATH_PROG(PPMTOGIF, ppmtogif)
if test -z "$PPMTOGIF"; then
   AC_MSG_WARN([
   ppmtogif was not found in your PATH.  It is used in 
   the WebSubmit module to create an icon from a submitted picture.
   You can continue without it but you will miss some CDSware 
   functionality.  We recommend you to install it first and to rerun 
   the configure script.  Ppmtogif is available from
   <http://www.acme.com/software/pbmplus/>.])
fi

## Check for Ppmquant:
AC_PATH_PROG(PPMQUANT, ppmquant)
if test -z "$PPMQUANT"; then
   AC_MSG_WARN([
   ppmquant was not found in your PATH.  It is used in 
   the WebSubmit module to create an icon from a submitted picture.
   You can continue without it but you will miss some CDSware 
   functionality.  We recommend you to install it first and to rerun 
   the configure script.  Ppmquant is available from
   <http://www.acme.com/software/pbmplus/>.])
fi

## Check for Pnmscale:
AC_PATH_PROG(PNMSCALE, pnmscale)
if test -z "$PNMSCALE"; then
   AC_MSG_WARN([
   pnmscale was not found in your PATH.  It is used in 
   the WebSubmit module to create an icon from a submitted picture.
   You can continue without it but you will miss some CDSware 
   functionality.  We recommend you to install it first and to rerun 
   the configure script.  Pnmscale is available from
   <http://www.acme.com/software/pbmplus/>.])
fi

## Substitute variables:
AC_SUBST(VERSION)
AC_SUBST(WML)
AC_SUBST(MYSQL)
AC_SUBST(PHP)
AC_SUBST(PYTHON)
AC_SUBST(WEBDIR)
AC_SUBST(CLIDIR)
AC_SUBST(WEBURL)
AC_SUBST(DBHOST)
AC_SUBST(DBNAME)
AC_SUBST(DBUSER)
AC_SUBST(DBPASS)
AC_SUBST(PDFTOTEXT)
AC_SUBST(PSTOTEXT)
AC_SUBST(PSTOASCII)
AC_SUBST(ANTIWORD)
AC_SUBST(CATDOC)
AC_SUBST(WVTEXT)
AC_SUBST(PPTHTML)
AC_SUBST(XLHTML)
AC_SUBST(HTMLTOTEXT)

## Define output files:
AC_CONFIG_FILES([Makefile \
	  config/Makefile \
	  config/configbis.wml \
	  modules/Makefile \
	  modules/bibconvert/Makefile \
	  modules/bibconvert/bin/Makefile \
	  modules/bibconvert/doc/Makefile \
	  modules/bibconvert/doc/admin/Makefile \
	  modules/bibharvest/Makefile \
	  modules/bibharvest/bin/Makefile \
	  modules/bibharvest/lib/Makefile \
	  modules/bibharvest/web/Makefile \
	  modules/bibsched/Makefile \
	  modules/bibsched/bin/Makefile \
	  modules/bibwords/Makefile \
	  modules/bibwords/bin/Makefile \
	  modules/bibupload/Makefile \
	  modules/bibupload/bin/Makefile \
	  modules/bibformat/Makefile \
	  modules/bibformat/bin/Makefile \
	  modules/bibformat/lib/Makefile \
	  modules/bibformat/lib/core/Makefile \
	  modules/bibformat/lib/common/Makefile \
	  modules/bibformat/doc/Makefile \
	  modules/bibformat/web/Makefile \
	  modules/bibformat/web/admin/Makefile \
	  modules/webhelp/Makefile \
	  modules/webhelp/web/Makefile \
	  modules/webhelp/web/hacking/Makefile \
	  modules/webhelp/web/admin/Makefile \
	  modules/webhelp/web/admin/howto/Makefile \
	  modules/websearch/Makefile \
	  modules/websearch/bin/Makefile \
	  modules/websearch/doc/Makefile \
	  modules/websearch/doc/admin/Makefile \
	  modules/websearch/doc/hacking/Makefile \
	  modules/websearch/lib/Makefile \
	  modules/websearch/web/Makefile \
	  modules/websearch/web/admin/Makefile \
	  modules/websession/Makefile \
	  modules/websession/bin/Makefile \
	  modules/websession/lib/Makefile \
	  modules/websession/web/Makefile \
	  modules/webstyle/Makefile \
	  modules/webstyle/css/Makefile \
	  modules/webstyle/img/Makefile \
	  modules/webstyle/lib/Makefile \
	  modules/webbasket/Makefile \
	  modules/webbasket/lib/Makefile \
	  modules/webbasket/web/Makefile \
	  modules/webalert/Makefile \
	  modules/webalert/lib/Makefile \
	  modules/webalert/web/Makefile \
	  modules/webalert/bin/Makefile \
	  modules/websubmit/Makefile \
	  modules/websubmit/bin/Makefile \
	  modules/websubmit/etc/Makefile \
	  modules/websubmit/etc/bibconvert/Makefile \
	  modules/websubmit/etc/bibconvert/KB/Makefile \
	  modules/websubmit/etc/bibconvert/config/Makefile \
	  modules/websubmit/doc/Makefile \
	  modules/websubmit/doc/admin/Makefile \
	  modules/websubmit/lib/Makefile \
	  modules/websubmit/lib/functions/Makefile \
	  modules/websubmit/web/Makefile \
	  modules/websubmit/web/access/Makefile \
	  modules/websubmit/web/access/protected/Makefile \
	  modules/websubmit/web/admin/Makefile \
	  modules/websubmit/web/publiline/Makefile \
	  modules/websubmit/web/publiline/inotes/Makefile \
	  modules/websubmit/web/personal/Makefile \
	  modules/webaccess/Makefile \
	  modules/webaccess/bin/Makefile \
	  modules/webaccess/doc/Makefile \
	  modules/webaccess/doc/admin/Makefile \
	  modules/webaccess/doc/hacking/Makefile \
	  modules/webaccess/lib/Makefile \
	  modules/webaccess/web/Makefile \
	  modules/webaccess/web/admin/Makefile \
	  modules/miscutil/Makefile \
	  modules/miscutil/bin/Makefile \
	  modules/miscutil/lib/Makefile \
	  modules/miscutil/demo/Makefile \
	  modules/miscutil/sql/Makefile \
	  ])

## Finally, write output files:
AC_OUTPUT

## Write help:
AC_MSG_RESULT([****************************************************************************])
AC_MSG_RESULT([** Your CERN Document Server Software (CDSware) installation is now ready **]) 
AC_MSG_RESULT([** for building.  You have entered the following parameters:              **]) 
AC_MSG_RESULT([**   - CDSware main install directory: ${prefix}])
AC_MSG_RESULT([**   - Web install directory: $WEBDIR])
AC_MSG_RESULT([**   - Web home URL: $WEBURL])
AC_MSG_RESULT([**   - DB server: $DBHOST])
AC_MSG_RESULT([**   - DB name: $DBNAME])
AC_MSG_RESULT([**   - DB username: $DBUSER])
AC_MSG_RESULT([**   - DB password: $DBPASS])
AC_MSG_RESULT([**   - Python executable: $PYTHON])
AC_MSG_RESULT([** Here are the steps to continue the building process:                   **])
AC_MSG_RESULT([**   1) Customize self-explanatory config file './config/config.wml'.     **])
AC_MSG_RESULT([**   2) Type 'make' to build your customized CDSware installation.        **])
AC_MSG_RESULT([**   3) Type 'make create-tables' if you have not created tables before.  **])
AC_MSG_RESULT([**   4) Type 'make install' to install the system.                        **])
AC_MSG_RESULT([**   5) Type 'make create-demo-site' to install and test the demo site.   **])
AC_MSG_RESULT([** Good luck, and thanks for choosing the CERN Document Server Software.  **])
AC_MSG_RESULT([**              -- CDS Development Group <cds.support@cern.ch>            **])
AC_MSG_RESULT([****************************************************************************])

## end of file
