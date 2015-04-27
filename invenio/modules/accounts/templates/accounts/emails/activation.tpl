{#
# This file is part of Invenio.
# Copyright (C) 2015 CERN.
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
#}
{% trans site_name=config.CFG_SITE_NAME_INTL.get(g.ln) %}Thanks for registering with {{site_name}}! To complete the registration, please validate your email address by clicking the link below:{% endtrans %}

{{activation_link|safe}}

{% trans %}Please note that this URL will only remain valid for about {{days}} days. If this request was not made by you, please ignore this message.{% endtrans %}
