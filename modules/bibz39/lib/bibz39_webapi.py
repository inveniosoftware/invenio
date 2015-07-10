# coding=utf-8
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
           #middle_area {
            width: 60%;
            margin: 0 auto;
           }
           #search_form {
            text-align:center;
            width:100%;
            margin: 0 auto;
            margin-bottom:20px;
           }

           #result_area {
            margin-top: 20px;
            border-collapse: collapse;
            overflow: hidden;
            padding: 1px;
            border-bottom: 1px solid #B9B9B9;
            font-size:12px;
           }

           .fullwidth {
             width:100%;
            }

           .server_area {
            margin-top: 20px;
            padding-top:5px;
            padding-bottom:5px;
            white-space: nowrap;
            font-size:14px;
            float:left;
           }

            td {
                padding: 5px;
                margin:5px;
                border-bottom: 1px solid #B9B9B9;
            }

            th {
             padding: 5px;
             border-collapse: collapse;
             border-bottom: 1px solid #B9B9B9;
            }
           .coloredrow {
            background-color: #F8F8F8;
           }
           pre{
            white-space: pre-wrap;
           }
           #middle_area a  {
            outline: 0;
            color: black;
            text-decoration: none; /* no underline */
           }

           #middle_area th  {
            text-align:left;
           }

           #radiobuttons {
            text-align:center;
            width:100%;
            margin: 0 auto;
            margin-bottom:20px;
           }
           removable {
            display:none;
           }
           #dialog-message pre {
            font-size:11px;
           }
           .bibz39_button_td {
             text-align: center;
           }
           .spinning_wheel {
             margin-top:80px;
             margin-bottom:30px;
             text-align: center;
           }
           .no-close .ui-dialog-titlebar-close {
             display: none;
           }
           pagebodystripemiddle {
            width:100%;
           }
           </style>
           """


def get_javascript():
    """
    Get all required scripts
    """
    js_scripts = """
                    <link rel="stylesheet" href="//maxcdn.bootstrapcdn.com/font-awesome/4.3.0/css/font-awesome.min.css">
                    <link rel="stylesheet" href="//code.jquery.com/ui/1.11.4/themes/smoothness/jquery-ui.css">
                    <script type="text/javascript" src="%(site_url)s/js/jquery.min.js">
                    </script>
                    <script type="text/javascript" src="%(site_url)s/js/jquery-ui.min.js">
                    </script>
                    <script type="text/javascript" src="%(site_url)s/js/bibz39.js">
                    </script>

                    <script type="text/javascript">
                        function showxml(identifier) {
                              $( "#dialog-message" )[0].innerHTML =  "<pre>" + gAllMarcXml[identifier].replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;') + "</pre>"
                              $( "#dialog-message" ).dialog({
                              width: window.innerWidth/2,
                              height: window.innerHeight/1.5,
                              modal: true,
                            });
                        }

                        function spinning() {
                            $("#middle_area > table").remove();
                            $("#middle_area").append("<p class='spinning_wheel'><i class='fa fa-spinner fa-pulse  fa-5x'></i><p><p class='bibz39_button_td'>Searching...</p>");
                        }
                    </script>
                 """ % {'site_url': CFG_SITE_URL}
    return js_scripts
