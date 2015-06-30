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
            width: 50%;
            margin: 0 auto;
           }
           #search_form {
            width: 100%;
           }

           #result_area {
            margin-top: 20px;
            border-collapse: collapse;
            overflow: hidden;
            padding: 1px;
            border-bottom: 1px solid #B9B9B9;
           }
            #arrow {
             text-align: center;
             display:block;
            }

            #serverarrow {
             width:100%;
             padding: 5px;
            }
            .fullwidth {
             width:100%;
            }
           .server_area {
            display:none;
            background-color: #F8F8F8;
            padding-top:5px;
            padding-bottom:5px;
            border-collapse: collapse;
            border: 1px solid #B9B9B9;
            white-space: nowrap;
            width: 100%;
            border-radius: 5px;
           }
            input[type="text"] {
                width: 90%;
                padding: 3px 0px 3px 5px;
                margin-top: 2px;
                margin-right: 6px;
                margin-bottom: 16px;
                border: 1px solid #e5e5e5;
                height: 25px;
                line-height:15px;
                outline: 0;
            }
            .submitbutton {
              padding: 5px;
              text-align:right;
            }
            td {
                padding: 5px;
                margin:5px;
                font-size:10px;
                font-weight:300;
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

           removable {
            display:none;
           }
           </style>
           """


def get_javascript():
    """
    Get all required scripts
    """
    js_scripts = """
                    <link rel="stylesheet" href="//maxcdn.bootstrapcdn.com/font-awesome/4.3.0/css/font-awesome.min.css">
                    <script type="text/javascript" src="%(site_url)s/js/jquery.min.js">
                    </script>
                    <script type="text/javascript" src="%(site_url)s/js/jquery-ui.min.js">
                    </script>
                    <script type="text/javascript" src="%(site_url)s/js/bibz39.js">
                    </script>
                    <script type="text/javascript">
                        function showxml(identifier) {
                            if($("#removable" + identifier).length) {
                                $(".animated").slideUp();
                                $(".removable").remove();
                            } else {
                                $(".removable").remove();
                                $("#result_area tr:eq(" + (identifier + 1) + ")").after("<tr class='removable'><td colspan='4'><div id='removable"+ identifier+"' class='animated'><pre>" + gAllMarcXml[identifier].replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;') + "</div></pre></td></tr>");
                                $(".animated").slideDown();
                            }
                            return false;
                        }

                        function server_area_print () {
                            console.log("show");
                            if( $(".server_area").is(":visible"))  {
                                $(".server_area").slideUp();
                                $("#fullwidth").attr('class', 'fa fa-angle-double-down');
                            } else {
                                $(".server_area").slideDown();
                                $("#fullwidth").attr('class', 'fa fa-angle-double-down fa-rotate-180');
                            }
                        }
                    </script>
                 """ % {'site_url': CFG_SITE_URL}
    return js_scripts
