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

dnl Initialize autoconf and automake:
AC_INIT(cdsware, 0.01-pre5, cds.support@cern.ch)
AM_INIT_AUTOMAKE(cdsware, 0.01-pre5)

dnl Check for install:
AC_PROG_INSTALL

dnl Check for WML:
AC_PATH_PROG(WML, wml)
if test -z "$WML"; then
   AC_MSG_ERROR([
   WML (Website META Language) was not found in your PATH.  Please install it first.  
   Available from <http://www.engelschall.com/sw/wml/>.])
fi

dnl Check for MySQL client:
AC_PATH_PROG(MYSQL, mysql)
if test -z "$MYSQL"; then
   AC_MSG_ERROR([
   MySQL command-line client was not found in your PATH.  Please install it first.
   Available from <http://mysql.com/>.])
fi

dnl Check for PHP:
AC_PATH_PROG(PHP, php)
if test -z "$PHP"; then
   AC_MSG_ERROR([
   PHP standalone command-line executable (i.e. not compiled as Apache module!) 
   was not found in your PATH.  Please install it first.
   Available from <http://www.php.net/manual/en/install.commandline.php>.])
fi

dnl Check for Python:
AC_PATH_PROG(PYTHON, python)
if test -z "$PYTHON"; then
   AC_MSG_ERROR([
   Python was not found in your path.  Please install it first.
   Available from <http://python.org/>.])
fi

dnl Check for Acrobat Reader:
AC_PATH_PROG(ACROREAD, acroread)
if test -z "$ACROREAD"; then
   AC_MSG_WARN([
   Acrobat Reader was not found in your path.  It is used in 
   the WebSubmit module for automatic conversion of submitted documents.  
   You can continue without it but you will miss some CDSware 
   functionality.  We recommend you to install it first and to rerun 
   the configure script.  Acrobat Reader is available from
   <http://www.adobe.com/products/acrobat/readstep.html>.])
fi

dnl Check for Lynx:
AC_PATH_PROG(LYNX, lynx)
if test -z "$LYNX"; then
   AC_MSG_WARN([
   Lynx was not found in your path.  It is used in 
   the WebSubmit module to fetch files from URLs given by
   submitters.
   You can continue without it but you will miss some CDSware 
   functionality.  We recommend you to install it first and to rerun 
   the configure script.  Lynx is available from
   <http://lynx.browser.org/>.])
fi

dnl Check for Gzip:
AC_PATH_PROG(GZIP, gzip)
if test -z "$GZIP"; then
   AC_MSG_WARN([
   Gzip was not found in your path.  It is used in 
   the WebSubmit module to compress the data submitted in an archive.
   You can continue without it but you will miss some CDSware 
   functionality.  We recommend you to install it first and to rerun 
   the configure script.  Gzip is available from
   <http://www.gzip.org/>.])
fi

dnl Check for Gunzip:
AC_PATH_PROG(GUNZIP, gunzip)
if test -z "$GUNZIP"; then
   AC_MSG_WARN([
   Gunzip was not found in your path.  It is used in 
   the WebSubmit module to correctly deal with submitted compressed
   files.
   You can continue without it but you will miss some CDSware 
   functionality.  We recommend you to install it first and to rerun 
   the configure script.  Gunzip is available from
   <http://www.gzip.org/>.])
fi

dnl Check for Tar:
AC_PATH_PROG(TAR, tar)
if test -z "$TAR"; then
   AC_MSG_WARN([
   Tar was not found in your path.  It is used in 
   the WebSubmit module to pack the submitted data into an archive.
   You can continue without it but you will miss some CDSware 
   functionality.  We recommend you to install it first and to rerun 
   the configure script.  Tar is available from
   <ftp://prep.ai.mit.edu/pub/gnu/tar/>.])
fi

dnl Check for Ps2pdf:
AC_PATH_PROG(PS2PDF, ps2pdf)
if test -z "$PS2PDF"; then
   AC_MSG_WARN([
   Ps2pdf was not found in your path.  It is used in 
   the WebSubmit module to convert submitted PostScripts into PDF.
   You can continue without it but you will miss some CDSware 
   functionality.  We recommend you to install it first and to rerun 
   the configure script.  Ps2pdf is available from
   <http://www.cs.wisc.edu/~ghost/doc/AFPL/6.50/Ps2pdf.htm>.])
fi

dnl Check for File:
AC_PATH_PROG(FILE, file)
if test -z "$FILE"; then
   AC_MSG_WARN([
   File was not found in your path.  It is used in 
   the WebSubmit module to check the validity of the submitted files.
   You can continue without it but you will miss some CDSware 
   functionality.  We recommend you to install it first and to rerun 
   the configure script.  File is available from
   <ftp://ftp.astron.com/pub/file/>.])
fi

dnl Check for Djpeg:
AC_PATH_PROG(DJPEG, djpeg)
if test -z "$DJPEG"; then
   AC_MSG_WARN([
   Djpeg was not found in your path.  It is used in 
   the WebSubmit module to create an icon from a submitted picture.
   You can continue without it but you will miss some CDSware 
   functionality.  We recommend you to install it first and to rerun 
   the configure script.  Djpeg is available from
   <http://www.ijg.org/files>.])
fi

dnl Check for Convert:
AC_PATH_PROG(CONVERT, convert)
if test -z "$CONVERT"; then
   AC_MSG_WARN([
   Convert was not found in your path.  It is used in 
   the WebSubmit module to create an icon from a submitted picture.
   You can continue without it but you will miss some CDSware 
   functionality.  We recommend you to install it first and to rerun 
   the configure script.  Convert is available from
   <http://www.imagemagick.org/>.])
fi

dnl Check for Giftext:
AC_PATH_PROG(GIFTEXT, giftext)
if test -z "$GIFTEXT"; then
   AC_MSG_WARN([
   Giftext was not found in your path.  It is used in 
   the WebSubmit module to create an icon from a submitted picture.
   You can continue without it but you will miss some CDSware 
   functionality.  We recommend you to install it first and to rerun 
   the configure script.  Giftext is available from
   <http://prtr-13.ucsc.edu/~badger/software/libungif/getting.shtml>.])
fi

dnl Check for Gifinter:
AC_PATH_PROG(GIFINTER, gifinter)
if test -z "$GIFINTER"; then
   AC_MSG_WARN([
   Gifinter was not found in your path.  It is used in 
   the WebSubmit module to create an icon from a submitted picture.
   You can continue without it but you will miss some CDSware 
   functionality.  We recommend you to install it first and to rerun 
   the configure script.  Gifinter is available from
   <http://prtr-13.ucsc.edu/~badger/software/libungif/getting.shtml>.])
fi

dnl Check for Gifrsize:
AC_PATH_PROG(GIFRSIZE, gifrsize)
if test -z "$GIFRSIZE"; then
   AC_MSG_WARN([
   Gifrsize was not found in your path.  It is used in 
   the WebSubmit module to create an icon from a submitted picture.
   You can continue without it but you will miss some CDSware 
   functionality.  We recommend you to install it first and to rerun 
   the configure script.  Gifrsize is available from
   <http://prtr-13.ucsc.edu/~badger/software/libungif/getting.shtml>.])
fi

dnl Check for jpegsize:
AC_PATH_PROG(JPEGSIZE, jpegsize)
if test -z "$JPEGSIZE"; then
   AC_MSG_WARN([
   jpegsize was not found in your path.  It is used in 
   the WebSubmit module to create an icon from a submitted picture.
   You can continue without it but you will miss some CDSware 
   functionality.  We recommend you to install it first and to rerun 
   the configure script.  Jpegsize is available from
   <http://www.squarebox.co.uk/download/>.])
fi

dnl Check for Ppmtogif:
AC_PATH_PROG(PPM2GIF, ppm2gif)
if test -z "$PPM2GIF"; then
   AC_MSG_WARN([
   ppm2gif was not found in your path.  It is used in 
   the WebSubmit module to create an icon from a submitted picture.
   You can continue without it but you will miss some CDSware 
   functionality.  We recommend you to install it first and to rerun 
   the configure script.  Ppm2gif is available from
   <http://www.acme.com/software/pbmplus/>.])
fi

dnl Check for Ppmquant:
AC_PATH_PROG(PPMQUANT, ppmquant)
if test -z "$PPMQUANT"; then
   AC_MSG_WARN([
   ppmquant was not found in your path.  It is used in 
   the WebSubmit module to create an icon from a submitted picture.
   You can continue without it but you will miss some CDSware 
   functionality.  We recommend you to install it first and to rerun 
   the configure script.  Ppmquant is available from
   <http://www.acme.com/software/pbmplus/>.])
fi

dnl Check for Pnmscale:
AC_PATH_PROG(PNMSCALE, pnmscale)
if test -z "$PNMSCALE"; then
   AC_MSG_WARN([
   pnmscale was not found in your path.  It is used in 
   the WebSubmit module to create an icon from a submitted picture.
   You can continue without it but you will miss some CDSware 
   functionality.  We recommend you to install it first and to rerun 
   the configure script.  Pnmscale is available from
   <http://www.acme.com/software/pbmplus/>.])
fi

dnl Define HTDOCSDIR directory:
AC_ARG_WITH(htdocsdir, AC_HELP_STRING([--with-htdocsdir], [specify where htdocs files go (e.g. /soft/httpd/host/cdsdev/htdocs/MPI/)]), HTDOCSDIR=${withval})
if test -z "$HTDOCSDIR"; then
   AC_MSG_ERROR([
   You have not used the "--with-htdocsdir" argument that should define the installation directory for HTML documents.  
   Example: "--with-htdocsdir=/soft/httpd/host/cdsdev/htdocs/MPI/".])
fi   

dnl Define CGIBIDIR directory:
AC_ARG_WITH(cgibindir, AC_HELP_STRING([--with-cgibindir], [specify where cgibin files go (e.g. /soft/httpd/host/cdsdev/cgi-bin/MPI/)]), CGIBINDIR=${withval})
if test -z "$CGIBINDIR"; then
   AC_MSG_ERROR([
   You have not used the "--with-cgibindir" argument that should define the installation directory for CGI scripts.  
   Example: "--with-cgibindir=/soft/httpd/host/cdsdev/cgi-bin/MPI/".])
fi   

dnl Define DBUTILDIR directory:
AC_ARG_WITH(dbutildir, AC_HELP_STRING([--with-dbutildir], [specify where dbutil files go (e.g. /usr/local/bin/MPI/)]), DBUTILDIR=${withval})
if test -z "$DBUTILDIR"; then
   AC_MSG_ERROR([
   You have not used the "--with-dbutil" argument that should define the installation directory for DB utilitites.  
   Example: "--with-dbutildir=/usr/local/bin/MPI/".])
fi   

dnl Define HTDOCSURL URL:
AC_ARG_WITH(htdocsurl, AC_HELP_STRING([--with-htdocsurl], [specify URL where htdocs files will be reached (e.g. http://cdsdev.cern.ch/MPI/)]), HTDOCSURL=${withval})
if test -z "$HTDOCSURL"; then
   AC_MSG_ERROR([
   You have not used the "--with-htdocsurl" argument that should define the URL where the HTML documents will be reached.  
   Example: "--with-htdocsurl=http://cdsdev.cern.ch/MPI/".])
fi   

dnl Define CGIBINURL URL:
AC_ARG_WITH(cgibinurl, AC_HELP_STRING([--with-cgibinurl], [specify URL where CGI scripts will be reached (e.g. http://cdsdev.cern.ch/cgi-bin/MPI/)]), CGIBINURL=${withval})
if test -z "$CGIBINURL"; then
   AC_MSG_ERROR([
   You have not used the "--with-cgibinurl" argument that should define the URL where the HTML documents will be reached.  
   Example: "--with-cgibinurl=http://cdsdev.cern.ch/cgi-bin/MPI/".])
fi   

dnl Define DBHOST database host:
AC_ARG_WITH(dbhost, AC_HELP_STRING([--with-dbhost], [specify DB server (e.g. cdsdb.cern.ch)]), DBHOST=${withval})
if test -z "$DBHOST"; then
   AC_MSG_ERROR([
   You have not used the "--with-dbhost" argument that should define which DB server to use.  
   Example: "--with-dbhost=cdsdb.cern.ch".])
fi   

dnl Define DBNAME database name:
AC_ARG_WITH(dbname, AC_HELP_STRING([--with-dbname], [specify DB name (e.g. cdsware)]), DBNAME=${withval})
if test -z "$DBNAME"; then
   AC_MSG_ERROR([
   You have not used the "--with-dbname" argument that should define DB name.  
   Example: "--with-dbname=cdsware".])
fi   

dnl Define DBUSER user name:
AC_ARG_WITH(dbuser, AC_HELP_STRING([--with-dbuser], [specify DB user name (e.g. cdsware)]), DBUSER=${withval})
if test -z "$DBUSER"; then
   AC_MSG_ERROR([
   You have not used the "--with-dbuser" argument that should define DB user name.  
   Example: "--with-dbuser=cdsware".])
fi   

dnl Define DBPASS user password:
AC_ARG_WITH(dbpass, AC_HELP_STRING([--with-dbpass], [specify DB user password (e.g. myp1ss)]), DBPASS=${withval})
if test -z "$DBPASS"; then
   AC_MSG_ERROR([
   You have not used the "--with-dbpass" argument that should define DB user password.  
   Example: "--with-dbpass=myp1ss".])
fi   

dnl Test supplied DB user credentials:

dnl Substitute variables:
AC_SUBST(VERSION)
AC_SUBST(WML)
AC_SUBST(MYSQL)
AC_SUBST(PHP)
AC_SUBST(PERL)
AC_SUBST(PYTHON)
AC_SUBST(HTDOCSDIR)
AC_SUBST(CGIBINDIR)
AC_SUBST(DBUTILDIR)
AC_SUBST(HTDOCSURL)
AC_SUBST(CGIBINURL)
AC_SUBST(DBHOST)
AC_SUBST(DBNAME)
AC_SUBST(DBUSER)
AC_SUBST(DBPASS)

dnl Write help:
AC_OUTPUT_COMMANDS([echo "****************************************************************************************"])
AC_OUTPUT_COMMANDS([echo "** Good, the CERN Document Server Software (CDSware) is now ready for installation!   **"])
AC_OUTPUT_COMMANDS([echo "** You have entered the following parameters:                                         **"])
AC_OUTPUT_COMMANDS([echo "**   - HTML documents install directory: $X1"],X1=$HTDOCSDIR)
AC_OUTPUT_COMMANDS([echo "**   - CGI scripts install directory: $X2"],X2=$CGIBINDIR)
AC_OUTPUT_COMMANDS([echo "**   - DB utilities install directory: $X3"],X3=$DBUTILDIR)
AC_OUTPUT_COMMANDS([echo "**   - HTML documents home URL: $X4"],X4=$HTDOCSURL)
AC_OUTPUT_COMMANDS([echo "**   - CGI scripts home URL: $X5"],X5=$CGIBINURL)
AC_OUTPUT_COMMANDS([echo "**   - DB server: $X6"],X6=$DBHOST)
AC_OUTPUT_COMMANDS([echo "**   - DB name: $X7"],X7=$DBNAME)
AC_OUTPUT_COMMANDS([echo "**   - DB username: $X8"],X8=$DBUSER)
AC_OUTPUT_COMMANDS([echo "**   - DB password: $X9"],X9=$DBPASS)
AC_OUTPUT_COMMANDS([echo "** Here are the steps to continue the building process:                               **"])
AC_OUTPUT_COMMANDS([echo "**   - Firstly, customize the self-explanatory config file './config/config.wml'.     **"])
AC_OUTPUT_COMMANDS([echo "**   - Secondly, type 'make' to build your customized CDSware installation.           **"])
AC_OUTPUT_COMMANDS([echo "**   - Thirdly, type 'make create-tables' if you have not created CDSware tables yet. **"])
AC_OUTPUT_COMMANDS([echo "**   - Finally, type 'make install' to install the system.                            **"])
AC_OUTPUT_COMMANDS([echo "** Good luck, and thanks for choosing the CERN Document Server Software.              **"])
AC_OUTPUT_COMMANDS([echo "**              -- CDS Development Group <cds.support@cern.ch>                        **"])
AC_OUTPUT_COMMANDS([echo "****************************************************************************************"])

dnl Write output files:
AC_OUTPUT(Makefile \
	  config/Makefile \
	  config/configbis.wml \
	  cgibin/Makefile \
	  dbutil/Makefile \
	  htdocs/Makefile \
	  htdocs/img/Makefile \
	  htdocs/errors/Makefile \
	  htdocs/submit/Makefile \
	  htdocs/submit/docs/Makefile \
	  htdocs/submit/docs/english/Makefile \
	  htdocs/submit/access/Makefile \
	  htdocs/submit/access/protected/Makefile \
	  htdocs/submit/MESS/Makefile \
	  htdocs/submit/MESS/functions/Makefile \
	  htdocs/submit/mycds/Makefile \
	  htdocs/submit/bibformat/Makefile \
	  htdocs/submit/bibformat/config/Makefile \
	  htdocs/submit/publiline/Makefile \
	  htdocs/submit/publiline/inotes/Makefile \
	  htdocs/personalize/Makefile \
	  htdocs/docs/Makefile \
	  htdocs/bibformat/Makefile \
	  htdocs/bibformat/core/Makefile \
	  htdocs/bibformat/common/Makefile \
	  htdocs/admin/Makefile \
	  htdocs/admin/howto/Makefile \
	  htdocs/admin/bibconvert/Makefile \
	  htdocs/admin/bibdata/Makefile \
	  htdocs/admin/bibformat/Makefile \
	  htdocs/admin/bibharvest/Makefile \
	  htdocs/admin/bibupload/Makefile \
	  htdocs/admin/bibwords/Makefile \
	  htdocs/admin/webaccess/Makefile \
	  htdocs/admin/websearch/Makefile \
	  htdocs/admin/websubmit/Makefile \
	  htdocs/admin/websubmit/docs/Makefile \
	  htdocs/admin/websubmit/docs/english/Makefile \
	  htdocs/admin/webperso/Makefile)

## end of file
