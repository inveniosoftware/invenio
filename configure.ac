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
AC_INIT(cdsware, 0.01-pre1, cds.support@cern.ch)
AM_INIT_AUTOMAKE(cdsware, 0.01-pre1)

dnl Check for install:
AC_PROG_INSTALL

dnl Check for WML:
AC_PATH_PROG(WML, wml)
if test -z "$WML"; then
   AC_MSG_ERROR([
   WML (Website META Language) is required.  Available from <http://www.engelschall.com/sw/wml/>.])
fi

dnl Check for MySQL client:
AC_PATH_PROG(MYSQL, mysql)
if test -z "$MYSQL"; then
   AC_MSG_ERROR([
   MySQL client is required.  Available from <http://mysql.com/>.])
fi

dnl Check for PHP:
AC_PATH_PROG(PHP, php)
if test -z "$PHP"; then
   AC_MSG_ERROR([
   PHP standalone command-line executable (i.e. not compiled as Apache module!) is required too.  
   Available from <http://www.php.net/manual/en/install.commandline.php>.])
fi

dnl Check for Perl:
AC_PATH_PROG(PERL, perl)
if test -z "$PERL"; then
   AC_MSG_ERROR([
   Perl is required.  Available from <http://cpan.org/>.])
fi

dnl Check for Python:
AC_PATH_PROG(PYTHON, python)
if test -z "$PYTHON"; then
   AC_MSG_ERROR([
   Python is required.  Available from <http://python.org/>.])
fi

dnl Define HTDOCSDIR directory:
AC_ARG_WITH(htdocsdir, AC_HELP_STRING([--with-htdocsdir], [specify where htdocs files go (e.g. /soft/httpd/host/cdsdev/htdocs/MPI/)]), HTDOCSDIR=${withval})
if test -z "$HTDOCSDIR"; then
   AC_MSG_ERROR([
   You have not used "--with-htdocsdir" argument that defines the installation directory for HTML documents.  
   Example: "--with-htdocsdir=/soft/httpd/host/cdsdev/htdocs/MPI/".])
fi   

dnl Define CGIBIDIR directory:
AC_ARG_WITH(cgibindir, AC_HELP_STRING([--with-cgibindir], [specify where cgibin files go (e.g. /soft/httpd/host/cdsdev/cgi-bin/MPI/)]), CGIBINDIR=${withval})
if test -z "$CGIBINDIR"; then
   AC_MSG_ERROR([
   You have not used "--with-cgibindir" argument that defines the installation directory for CGI scripts.  
   Example: "--with-cgibindir=/soft/httpd/host/cdsdev/cgi-bin/MPI/".])
fi   

dnl Define DBUTILDIR directory:
AC_ARG_WITH(dbutildir, AC_HELP_STRING([--with-dbutildir], [specify where dbutil files go (e.g. /usr/local/bin/MPI/)]), DBUTILDIR=${withval})
if test -z "$DBUTILDIR"; then
   AC_MSG_ERROR([
   You have not used "--with-dbutil" argument that defines the installation directory for DB utilitites.  
   Example: "--with-dbutildir=/usr/local/bin/MPI/".])
fi   

dnl Define HTDOCSURL URL:
AC_ARG_WITH(htdocsurl, AC_HELP_STRING([--with-htdocsurl], [specify URL where htdocs files will be reached (e.g. http://cdsdev.cern.ch/MPI/)]), HTDOCSURL=${withval})
if test -z "$HTDOCSURL"; then
   AC_MSG_ERROR([
   You have not used "--with-htdocsurl" argument that defines the URL where the HTML documents will be reached.  
   Example: "--with-htdocsurl=http://cdsdev.cern.ch/MPI/".])
fi   

dnl Define CGIBINURL URL:
AC_ARG_WITH(cgibinurl, AC_HELP_STRING([--with-cgibinurl], [specify URL where CGI scripts will be reached (e.g. http://cdsdev.cern.ch/cgi-bin/MPI/)]), CGIBINURL=${withval})
if test -z "$CGIBINURL"; then
   AC_MSG_ERROR([
   You have not used "--with-cgibinurl" argument that defines the URL where the HTML documents will be reached.  
   Example: "--with-cgibinurl=http://cdsdev.cern.ch/cgi-bin/MPI/".])
fi   

dnl Define DBHOST database host:
AC_ARG_WITH(dbhost, AC_HELP_STRING([--with-dbhost], [specify DB server (e.g. cdsdb.cern.ch)]), DBHOST=${withval})
if test -z "$DBHOST"; then
   AC_MSG_ERROR([
   You have not used "--with-dbhost" argument that defines which DB server to use.  
   Example: "--with-dbhost=cdsdb.cern.ch".])
fi   

dnl Define DBNAME database name:
AC_ARG_WITH(dbname, AC_HELP_STRING([--with-dbname], [specify DB name (e.g. cdsware)]), DBNAME=${withval})
if test -z "$DBNAME"; then
   AC_MSG_ERROR([
   You have not used "--with-dbname" argument that defines CDSware database name.  
   Example: "--with-dbname=cdsware".])
fi   

dnl Define DBUSER user name:
AC_ARG_WITH(dbuser, AC_HELP_STRING([--with-dbuser], [specify DB user name (e.g. cdsware)]), DBUSER=${withval})
if test -z "$DBUSER"; then
   AC_MSG_ERROR([
   You have not used "--with-dbuser" argument that defines DB user name.  
   Example: "--with-dbuser=cdsware".])
fi   

dnl Define DBPASS user password:
AC_ARG_WITH(dbpass, AC_HELP_STRING([--with-dbpass], [specify DB user password (e.g. myp1ss)]), DBPASS=${withval})
if test -z "$DBPASS"; then
   AC_MSG_ERROR([
   You have not used "--with-dbpass" argument that defines DB user password.  
   Example: "--with-dbpass=myp1ss".])
fi   

dnl Test supplied DB user credentials:

dnl Substitute variables:
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
AC_OUTPUT_COMMANDS([echo "**   - DB table name: $X7"],X7=$DBNAME)
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
	  htdocs/submit/Makefile \
	  htdocs/personalize/Makefile \
	  htdocs/docs/Makefile \
	  htdocs/admin/Makefile)

## end of file
