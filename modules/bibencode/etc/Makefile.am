# This file is part of Invenio.
# Copyright (C) 2011 CERN.
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

etcdir = $(sysconfdir)/bibencode

etc_DATA = encoding_profiles.json \
           extract_profiles.json \
           batch_template_new_formats.json \
           batch_template_submission.json \
           pbcore_mappings.json \
           pbcore_to_marc.xsl \
           pbcore_to_marc_nons.xsl

EXTRA_DIST = $(etc_DATA)

CLEANFILES = *~ *.tmp
