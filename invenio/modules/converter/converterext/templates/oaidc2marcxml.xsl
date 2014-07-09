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
<!-- This transformation does the following:
     - Select various OAI fields and map each of them
       to corresponding marc field
     - Adds OAI identifier in field 909CO

     This stylesheet is provided only as an example of transformation.
     Please look for 'CUSTOMIZEME' labels in this stylesheet in order to find
     key parts that you should customize to fit your installation needs.

     Also note that this stylesheet expect source file to correctly refers to
        http://www.loc.gov/MARC21/slim and
        http://www.openarchives.org/OAI/2.0/oai_dc/ and
        http://purl.org/dc/elements/1.1/ namespaces
-->
<xsl:stylesheet version="1.0"
xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
xmlns:OAI-PMH="http://www.openarchives.org/OAI/2.0/"
xmlns:oaidc="http://www.openarchives.org/OAI/2.0/oai_dc/"
xmlns:dc="http://purl.org/dc/elements/1.1/"
exclude-result-prefixes="OAI-PMH oaidc dc">
  <xsl:output method="xml" encoding="UTF-8" />
  <xsl:template match="/">
    <collection>
      <xsl:for-each select="//OAI-PMH:record">
        <xsl:choose>
          <xsl:when test="OAI-PMH:header[@status='deleted']">
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
                  <xsl:if test="./OAI-PMH:about/provenance/originDescription">
                    <subfield code="o"><xsl:copy-of select="./OAI-PMH:about/provenance/originDescription" /></subfield>
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
              <xsl:if test="./OAI-PMH:metadata/oaidc:dc/dc:language">

                <datafield tag="041" ind1="" ind2="">
                  <subfield code="a">
                    <xsl:value-of select="./OAI-PMH:metadata/oaidc:dc/dc:language" />
                  </subfield>
                </datafield>
              </xsl:if>
              <xsl:if test="./OAI-PMH:metadata/oaidc:dc/dc:creator[1]">

                <datafield tag="100" ind1="" ind2="">
                  <subfield code="a">
                    <xsl:value-of select="./OAI-PMH:metadata/oaidc:dc/dc:creator[1]" />
                  </subfield>
                </datafield>
              </xsl:if>
              <xsl:if test="./OAI-PMH:metadata/oaidc:dc/dc:title">
                <datafield tag="245" ind1="" ind2="">
                  <subfield code="a">
                    <xsl:value-of select="./OAI-PMH:metadata/oaidc:dc/dc:title" />
                  </subfield>
                </datafield>
              </xsl:if>
              <xsl:if test="./OAI-PMH:metadata/oaidc:dc/dc:title | ./OAI-PMH:metadata/oaidc:dc/dc:date">

                <datafield tag="260" ind1="" ind2="">
                  <xsl:if test="./OAI-PMH:metadata/oaidc:dc/dc:publisher">

                    <subfield code="b">
                      <xsl:value-of select="./OAI-PMH:metadata/oaidc:dc/dc:publisher" />
                    </subfield>
                  </xsl:if>
                  <xsl:if test="./OAI-PMH:metadata/oaidc:dc/dc:date">

                    <subfield code="c">
                      <xsl:value-of select="./OAI-PMH:metadata/oaidc:dc/dc:date" />
                    </subfield>
                  </xsl:if>
                </datafield>
              </xsl:if>
              <xsl:if test="./OAI-PMH:metadata/oaidc:dc/dc:coverage">

                <datafield tag="500" ind1="" ind2="">
                  <subfield code="a">
                    <xsl:value-of select="./OAI-PMH:metadata/oaidc:dc/dc:coverage" />
                  </subfield>
                </datafield>
              </xsl:if>
              <xsl:if test="./OAI-PMH:metadata/oaidc:dc/dc:description">

                <datafield tag="520" ind1="" ind2="">
                  <subfield code="a">
                    <xsl:value-of select="./OAI-PMH:metadata/oaidc:dc/dc:description" />
                  </subfield>
                </datafield>
              </xsl:if>
              <xsl:if test="./OAI-PMH:metadata/oaidc:dc/dc:rights">
                <datafield tag="540" ind1="" ind2="">
                  <subfield code="a">
                    <xsl:value-of select="./OAI-PMH:metadata/oaidc:dc/dc:rights" />
                  </subfield>
                </datafield>
              </xsl:if>
              <xsl:if test="./OAI-PMH:metadata/oaidc:dc/dc:subject">

                <datafield tag="650" ind1="1" ind2="7">
                  <subfield code="a">
                    <xsl:value-of select="./OAI-PMH:metadata/oaidc:dc/dc:subject" />
                  </subfield>
                </datafield>
              </xsl:if>
              <xsl:if test="./OAI-PMH:metadata/oaidc:dc/dc:type">
                <datafield tag="655" ind1="7" ind2="">
                  <subfield code="a">
                    <xsl:value-of select="./OAI-PMH:metadata/oaidc:dc/dc:type" />
                  </subfield>
                </datafield>
              </xsl:if>
              <xsl:for-each select="./OAI-PMH:metadata/oaidc:dc/dc:creator[position()&gt;1]">

                <datafield tag="700" ind1="" ind2="">
                  <subfield code="a">
                    <xsl:value-of select="." />
                  </subfield>
                </datafield>
              </xsl:for-each>
              <xsl:if test="./OAI-PMH:metadata/oaidc:dc/dc:contributor">

                <datafield tag="720" ind1="" ind2="">
                  <subfield code="a">
                    <xsl:value-of select="./OAI-PMH:metadata/oaidc:dc/dc:contributor" />
                  </subfield>
                </datafield>
              </xsl:if>
              <xsl:if test="./OAI-PMH:metadata/oaidc:dc/dc:source">
                <datafield tag="786" ind1="0" ind2="">
                  <subfield code="n">
                    <xsl:value-of select="./OAI-PMH:metadata/oaidc:dc/dc:source" />
                  </subfield>
                </datafield>
              </xsl:if>
              <xsl:if test="./OAI-PMH:metadata/oaidc:dc/dc:relation">

                <datafield tag="786" ind1="0" ind2="">
                  <subfield code="n">
                    <xsl:value-of select="./OAI-PMH:metadata/oaidc:dc/dc:relation" />
                  </subfield>
                </datafield>
              </xsl:if>
              <xsl:if test="./OAI-PMH:metadata/oaidc:dc/dc:format">
                <datafield tag="856" ind1="" ind2="">
                  <subfield code="q">
                    <xsl:value-of select="./OAI-PMH:metadata/oaidc:dc/dc:format" />
                  </subfield>
                </datafield>
              </xsl:if>
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
                  <xsl:if test="./OAI-PMH:about/provenance/originDescription">
                    <subfield code="o"><xsl:copy-of select="./OAI-PMH:about/provenance/originDescription" /></subfield>
                  </xsl:if>
                  <subfield code="t">false</subfield>
                </datafield>
              </xsl:if>
              <datafield tag="980" ind1="" ind2="">
                <!--- CUSTOMIZEME: Produce a 980__a field in order to classify this record
                                   in a collection. The value for 980__a can either come
                                   from the DC metadata, or be a fixed value.
                                   A knowledge base can also be used to transform source data.
                                   Harvesting from qualified OAI source might be easier to select
                                   the right source data.  -->
                <subfield code="a">PREPRINT</subfield>
              </datafield>
            </record>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:for-each>
    </collection>
  </xsl:template>
</xsl:stylesheet>
