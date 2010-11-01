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

submission_templatesdir = $(sysconfdir)/bibconvert/config
submission_templates_DATA = DEMOPIC.tpl DEMOPICcreate.tpl DEMOPICmodify.tpl \
           DEMOTHE.tpl DEMOTHEcreate.tpl DEMOTHEmodify.tpl \
           DEMOART.tpl DEMOARTcreate.tpl DEMOARTmodify.tpl \
           DEMOPOE.tpl DEMOPOEcreate.tpl DEMOPOEmodify.tpl \
           DEMOBOO.tpl DEMOBOOcreate.tpl DEMOBOOmodify.tpl \
           DEMOJRN.tpl DEMOJRNcreate.tpl DEMOJRNmodify.tpl

stamper_templatesdir = $(sysconfdir)/websubmit/file_stamper_templates
stamper_templates_DATA = demo-stamp-left.tex demo-stamp-left-logo.png

converter_templatesdir = $(sysconfdir)/websubmit/file_converter_templates
converter_templates_DATA = PDFA_def.ps deskew.lua

EXTRA_DIST = $(submission_templates_DATA) $(stamper_templates_DATA) $(converter_templates_DATA)

CLEANFILES = *~ *.tmp

