<?xml version="1.0" encoding="ISO-8859-1"?>
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
<!-- This transformation does the following:
     - Select various OAI fields and map each of them
       to corresponding marc field
     - Adds OAI identifier in field 909CO

    This stylesheet is optimized for records coming from OpenAIRE at:
        <http://www.openaire.eu/>

    as harvested from:
        <www.openaire.eu:8280/is/mvc/oai/oai.do> with dmf prefix.
-->
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:OAI-PMH="http://www.openarchives.org/OAI/2.0/" xmlns:oaidc="http://www.openarchives.org/OAI/2.0/oai_dc/" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dmf="http://www.driver-repository.eu/OAI/2.0/DMF/" xmlns:oaf="http://namespace.openaire.eu/oaf" version="1.0" exclude-result-prefixes="OAI-PMH oaidc dc dmf oaf">
  <xsl:output method="xml" encoding="UTF-8"/>
  <xsl:template match="/">
    <collection>
      <xsl:for-each select="//OAI-PMH:record">
        <xsl:choose>
          <xsl:when test="OAI-PMH:header[@status='deleted']">
            <record>
              <xsl:if test="./OAI-PMH:header/OAI-PMH:identifier | ./OAI-PMH:header/OAI-PMH:setSpec">
                <!-- CUSTOMIZEME: Modify the datafield below with tag and indicators used
                                              in your Invenio installation for the OAI identifier -->
                <datafield tag="035" ind1=" " ind2=" ">
                  <subfield code="a">
                    <xsl:value-of select="./OAI-PMH:header/OAI-PMH:identifier"/>
                  </subfield>
                  <subfield code="p">
                    <xsl:value-of select="./OAI-PMH:header/OAI-PMH:setSpec"/>
                  </subfield>
                </datafield>
              </xsl:if>
              <datafield tag="980" ind1=" " ind2=" ">
                <subfield code="c">DELETED</subfield>
              </datafield>
            </record>
          </xsl:when>
          <xsl:otherwise>
            <record>
              <xsl:for-each select="./OAI-PMH:metadata/dmf:dmf_record/dc:language">
                <datafield tag="041" ind1=" " ind2=" ">
                  <subfield code="a">
                    <xsl:value-of select="."/>
                  </subfield>
                </datafield>
              </xsl:for-each>
              <xsl:if test="./OAI-PMH:metadata/dmf:dmf_record/dc:creator[1]">
                <datafield tag="100" ind1=" " ind2=" ">
                  <subfield code="a">
                    <xsl:value-of select="./OAI-PMH:metadata/dmf:dmf_record/dc:creator[1]"/>
                  </subfield>
                </datafield>
              </xsl:if>
              <xsl:for-each select="./OAI-PMH:metadata/dmf:dmf_record/dc:creator[position()&gt;1]">
                <datafield tag="700" ind1=" " ind2=" ">
                  <subfield code="a">
                    <xsl:value-of select="."/>
                  </subfield>
                </datafield>
              </xsl:for-each>
              <xsl:for-each select="./OAI-PMH:metadata/dmf:dmf_record/dc:title">
                <datafield tag="245" ind1=" " ind2=" ">
                  <subfield code="a">
                    <xsl:value-of select="."/>
                  </subfield>
                </datafield>
              </xsl:for-each>
              <xsl:for-each select="./OAI-PMH:metadata/dmf:dmf_record/dc:description">
                <datafield tag="520" ind1=" " ind2=" ">
                  <subfield code="a">
                    <xsl:value-of select="."/>
                  </subfield>
                </datafield>
              </xsl:for-each>
              <xsl:if test="./OAI-PMH:metadata/dmf:dmf_record/dc:publisher | ./OAI-PMH:metadata/dmf:dmf_record/oaf:publicationdate">
                <datafield tag="909" ind1="C" ind2="4">
                  <xsl:for-each select="./OAI-PMH:metadata/dmf:dmf_record/dc:publisher">
                    <subfield code="p">
                      <xsl:value-of select="."/>
                    </subfield>
                  </xsl:for-each>
                  <xsl:for-each select="./OAI-PMH:metadata/dmf:dmf_record/oaf:publicationyear">
                    <subfield code="y">
                      <xsl:value-of select="."/>
                    </subfield>
                  </xsl:for-each>
                </datafield>
              </xsl:if>
              <xsl:for-each select="./OAI-PMH:metadata/dmf:dmf_record/oaf:publicationdate">
                <datafield tag="260" ind1=" " ind2=" ">
                  <subfield code="c">
                    <xsl:value-of select="."/>
                  </subfield>
                </datafield>
              </xsl:for-each>
              <xsl:for-each select="./OAI-PMH:metadata/dmf:dmf_record/oaf:embargoenddate">
                <datafield tag="942" ind1=" " ind2=" ">
                  <subfield code="a">
                    <xsl:value-of select="."/>
                  </subfield>
                </datafield>
              </xsl:for-each>
              <xsl:for-each select="./OAI-PMH:metadata/dmf:dmf_record/oaf:accessmode">
                <datafield tag="542" ind1=" " ind2=" ">
                  <subfield code="l">
                    <xsl:value-of select="."/>
                  </subfield>
                </datafield>
              </xsl:for-each>
              <xsl:for-each select="./OAI-PMH:metadata/dmf:dmf_record/oaf:projectgrantagreementnumber">
                <datafield tag="536" ind1=" " ind2=" ">
                  <subfield code="c">
                    <xsl:value-of select="."/>
                  </subfield>
                </datafield>
              </xsl:for-each>
              <xsl:for-each select="./OAI-PMH:metadata/dmf:dmf_record/dc:identifier">
                <datafield tag="856" ind1="4" ind2=" ">
                  <subfield code="u">
                    <xsl:value-of select="."/>
                  </subfield>
                </datafield>
              </xsl:for-each>
              <xsl:if test="./OAI-PMH:header/OAI-PMH:identifier">
                <!-- CUSTOMIZEME: Modify the datafield below with tag and indicators used
                                      in your Invenio installation for the OAI identifier -->
                <datafield tag="035" ind1=" " ind2=" ">
                  <subfield code="a">
                    <xsl:value-of select="./OAI-PMH:header/OAI-PMH:identifier"/>
                  </subfield>
                  <subfield code="p">
                    <xsl:value-of select="./OAI-PMH:header/OAI-PMH:setSpec"/>
                  </subfield>
                </datafield>
              </xsl:if>
              <datafield tag="980" ind1=" " ind2=" ">
                <!--- CUSTOMIZEME: Produce a 980__a field in order to classify this record
                                   in a collection. The value for 980__a can either come
                                   from the DC metadata, or be a fixed value.
                                   A knowledge base can also be used to transform source data.
                                   Harvesting from qualified OAI source might be easier to select
                                   the right source data.  -->
                <subfield code="a">DARK</subfield>
              </datafield>
            </record>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:for-each>
    </collection>
  </xsl:template>
</xsl:stylesheet>
