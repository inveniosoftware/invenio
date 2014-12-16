<?xml version="1.0" encoding="UTF-8"?>
<!-- $Id$

     This file is part of Invenio.
     Copyright (C) 2006, 2007, 2008, 2010, 2011 CERN.

     Invenio is free software; you can redistribute it and/or
     modify it under the terms of the GNU General Public License as
     published by the Free Software Foundation; either version 2 of the
     License, or (at your option) any later version.

     Invenio is distributed in the hope that it will be useful, but
     WITHOUT ANY WARRANTY; without even the implied warranty of
     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
     General Public License for more details.

     You should have received a copy of the GNU General Public License
     along with Invenio; if not, write to the Free Software Foundation, Inc.,
     59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
-->
<!-- This transformation keeps the same source file, with the following exceptions:
     - OAI envelope is removed
     - Records marked with status='deleted' are returned as deleted for Invenio
     - subfield 980 $w is removed
     - Adds OAI identifier in field 909CO

     This stylesheet is provided only as an example of transformation.
     Please look for 'CUSTOMIZEME' labels in this stylesheet in order to find
     key parts that you should customize to fit your installation needs.

     Also note that this stylesheet expect source file to correctly refers to
        http://www.loc.gov/MARC21/slim and
        http://www.openarchives.org/OAI/2.0/ namespaces
-->
<xsl:stylesheet version="1.0"
xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
xmlns:OAI-PMH="http://www.openarchives.org/OAI/2.0/"
xmlns:marc="http://www.loc.gov/MARC21/slim"
xmlns:OAI-provenance="http://www.openarchives.org/OAI/2.0/provenance"
xmlns:fn="http://cdsweb.cern.ch/bibconvert/fn"
exclude-result-prefixes="OAI-PMH marc OAI-provenance fn">
  <xsl:output method="xml" encoding="UTF-8" />
  <xsl:template match="/">
    <collection>
      <xsl:for-each select="//OAI-PMH:record">
        <xsl:choose>
          <xsl:when test="./OAI-PMH:header[@status='deleted']">
            <record>
              <xsl:if test="./OAI-PMH:header/OAI-PMH:identifier | ./OAI-PMH:header/OAI-PMH:setSpec">
                <!-- CUSTOMIZEME: Modify the datafield below with tag and indicators used
                                      in your Invenio installation for the OAI Provenance Field -->
                <datafield tag="035" ind1=" " ind2=" ">
                  <subfield code="a"><xsl:value-of select="./OAI-PMH:header/OAI-PMH:identifier" /></subfield>
                  <subfield code="u"><xsl:value-of select="//OAI-PMH:request" /></subfield>
                  <!-- Set this to a more semantic string if you prefer... -->
                  <subfield code="9"><xsl:value-of select="//OAI-PMH:request" /></subfield>
                  <subfield code="d"><xsl:value-of select="./OAI-PMH:header/OAI-PMH:datestamp" /></subfield>
                  <subfield code="h"><xsl:value-of select="//OAI-PMH:responseDate" /></subfield>
                  <subfield code="m"><xsl:value-of select="//OAI-PMH:request/@metadataPrefix" /></subfield>
                  <xsl:if test="./OAI-PMH:about/OAI-provenance:provenance/OAI-provenance:originDescription">
                    <xsl:variable name="origin" select="./OAI-PMH:about/OAI-provenance:provenance/OAI-provenance:originDescription" />
                    <subfield code="o"><value-of select="fn:escape($origin)" /></subfield>
                  </xsl:if>
                  <subfield code="t">false</subfield>
                </datafield>
              </xsl:if>
              <datafield tag="980" ind1="" ind2="">
                <subfield code="c">DELETED</subfield>
              </datafield>
            </record>
          </xsl:when>
          <xsl:otherwise>
            <record>
              <xsl:for-each select="./OAI-PMH:metadata/marc:record/marc:datafield">
                <!-- CUSTOMIZEME: Modify below in order to choose which
                                             datafield/subfield will be kept
                                             and which will be dropped

                                             Sample below: -keep if tag is not 980__ and has subfields
                                                           -if tag is 980__ , keep datafield only if some
                                                            subfield with code != 'w' exist. Remove
                                                            subfield 980__w.
                                                -->
                <xsl:choose>
                  <xsl:when test="not(@tag='980' and (@ind1='' or @ind1=' ') and (@ind2='' or @ind2=' ') and ./marc:subfield)">

                    <xsl:element name="{local-name(.)}">
                      <xsl:copy-of select="@*" />
                      <xsl:for-each select="./marc:subfield">
                        <xsl:element name="{local-name(.)}">
                          <xsl:copy-of select="@*" />
                          <xsl:value-of select="." />
                        </xsl:element>
                      </xsl:for-each>
                    </xsl:element>
                  </xsl:when>
                  <xsl:otherwise>
                    <xsl:if test="./marc:subfield[@code!='w']">
                      <xsl:element name="{local-name(.)}">
                        <xsl:copy-of select="@*" />
                        <xsl:for-each select="./marc:subfield[@code!='w']">
                          <xsl:element name="{local-name(.)}">
                            <xsl:copy-of select="@*" />
                            <xsl:value-of select="." />
                          </xsl:element>
                        </xsl:for-each>
                      </xsl:element>
                    </xsl:if>
                  </xsl:otherwise>
                </xsl:choose>
              </xsl:for-each>
              <xsl:if test="./OAI-PMH:header/OAI-PMH:identifier">
                <!-- CUSTOMIZEME: Modify the datafield below with tag and indicators used
                                      in your Invenio installation for the OAI Provenance Field -->
                <datafield tag="035" ind1=" " ind2=" ">
                  <subfield code="a"><xsl:value-of select="./OAI-PMH:header/OAI-PMH:identifier" /></subfield>
                  <subfield code="u"><xsl:value-of select="//OAI-PMH:request" /></subfield>
                  <!-- Set this to a more semantic string if you prefer... -->
                  <subfield code="9"><xsl:value-of select="//OAI-PMH:request" /></subfield>
                  <subfield code="d"><xsl:value-of select="./OAI-PMH:header/OAI-PMH:datestamp" /></subfield>
                  <subfield code="h"><xsl:value-of select="//OAI-PMH:responseDate" /></subfield>
                  <subfield code="m"><xsl:value-of select="//OAI-PMH:request/@metadataPrefix" /></subfield>
                  <xsl:if test="./OAI-PMH:about/OAI-provenance:provenance/OAI-provenance:originDescription">
                    <xsl:variable name="origin" select="./OAI-PMH:about/OAI-provenance:provenance/OAI-provenance:originDescription" />
                    <subfield code="o"><xsl:value-of select="fn:escape($origin)" /></subfield>
                  </xsl:if>
                  <subfield code="t">false</subfield>
                </datafield>
              </xsl:if>
            </record>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:for-each>
    </collection>
  </xsl:template>
</xsl:stylesheet>
