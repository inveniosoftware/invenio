# This file is part of Invenio.
# Copyright (C) 2011, 2012 CERN.
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

# pylint: disable=C0103
"""Invenio bibz39 live view engine implementation"""

from invenio.config import CFG_SITE_URL


def get_css():
    """
    Get css styles
    """
    return """
           <style type="text/css">
           #search_area {
            text-align: center;
           }
           #result_area {
            width: 50%;
            margin: 0 auto;
            margin-top: 20px;
            border-collapse: collapse;
            overflow: hidden;
            padding: 1px;
            border: 1px solid #F0F0F0;
           }
            td {
                padding: 5px;
            }
            tr, th {
            border-collapse: collapse;
            border: 1px solid #F0F0F0;
            }

           .coloredrow {
            background-color: #F0F0F0;
           }
           pre{
            white-space: pre-wrap;
           }
           </style>
           """


def get_javascript():
    """
    Get all required scripts
    """
    js_scripts = """<script type="text/javascript" src="%(site_url)s/js/jquery.min.js">
                    </script>
                    <script type="text/javascript" src="%(site_url)s/js/jquery-ui.min.js">
                    </script>
                    <script type="text/javascript" src="%(site_url)s/js/bibz39.js">
                    </script>
                    <script type="text/javascript">
                        function showxml(identifier) {
                            if($("#removable" + identifier).length) {
                                $(".removable").remove();
                            } else {
                                $(".removable").remove();
                                $("#result_area tr:eq(" + (identifier + 1) + ")").after("<tr class='removable'><td colspan='4'><div id='removable"+ identifier+"' class='animated'><pre>" + gAllMarcXml[identifier].replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;') + "</div></pre></td></tr>");
                                $(".animated").hide();
                                $(".animated").slideDown();
                            }
                        }
                    </script>
                 """ % {'site_url': CFG_SITE_URL}
    return js_scripts
