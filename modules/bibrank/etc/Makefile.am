## $Id$

## This file is part of the CERN Document Server Software (CDSware).
## Copyright (C) 2002, 2003, 2004, 2005 CERN.
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

etcdir = $(sysconfdir)/bibrank

etc_DATA = bibrankgkb.cfg \
           bibrankgkb_jif_conv.kb \
           bibrankgkb_jif_example.kb \
           demo_jif.cfg \
           demo_jif.kb \
           stopwords.de.kb \
           stopwords.kb \
           template_citation.cfg \
           template_combine_method.cfg \
           template_download_similarity.cfg \
           template_download_total.cfg \
           template_download_users.cfg \
           template_single_tag_rank_method.cfg \
           template_word_similarity.cfg \
           wrd.cfg

EXTRA_DIST = bibrankgkb.cfg.in \
             bibrankgkb_jif_conv.kb \
             bibrankgkb_jif_example.kb \
             demo_jif.cfg.in \
             demo_jif.kb \
             stopwords.de.kb \
             stopwords.kb \
             template_citation.cfg \
             template_combine_method.cfg \
             template_download_similarity.cfg \
             template_download_total.cfg \
             template_download_users.cfg \
             template_single_tag_rank_method.cfg.in \
             template_word_similarity.cfg.wml \
             wrd.cfg.wml

CLEANFILES = template_word_similarity.cfg wrd.cfg *.tmp

wrd.cfg: wrd.cfg.wml $(top_srcdir)/config/config.wml $(top_builddir)/config/configbis.wml $(top_srcdir)/config/cdspage.wml
	$(WML) -o $@ $<

template_word_similarity.cfg: template_word_similarity.cfg.wml $(top_srcdir)/config/config.wml $(top_builddir)/config/configbis.wml $(top_srcdir)/config/cdspage.wml
	$(WML) -o $@ $<
