<?xml version="1.0" encoding="UTF-8"?>
<!-- $Id$

     This file is part of Invenio.
     Copyright (C) 2007, 2008, 2009, 2010, 2011 CERN.

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
<!--
<name>RSS</name>
<description>RSS</description>
-->

<!--

This stylesheet transforms a MARCXML input into a RSS output.
This stylesheet is provided only as an example of transformation.

-->
<xsl:stylesheet version="1.0"
xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
xmlns:marc="http://www.loc.gov/MARC21/slim"
xmlns:fn="http://cdsweb.cern.ch/bibformat/fn"
xmlns:dc="http://purl.org/dc/elements/1.1/"
xmlns:dcterms="http://purl.org/dc/terms/"
exclude-result-prefixes="marc fn dc dcterms">
<xsl:output method="xml"  indent="yes" encoding="UTF-8" omit-xml-declaration="yes"/>
<xsl:template match="/">
	<xsl:if test="collection">
	        <xsl:for-each select="collection">
			<xsl:for-each select="record">
                                <item>
                                        <xsl:apply-templates select="."/>
                                </item>
			</xsl:for-each>
		</xsl:for-each>
	</xsl:if>
	<xsl:if test="record">
                <item>
		        <xsl:apply-templates/>
                </item>
	</xsl:if>
 </xsl:template>

<xsl:template match="record">
        <title>
                <xsl:for-each select="datafield[@tag='245']">
                        <xsl:value-of select="subfield[@code='a']"/>
                        <xsl:if test="subfield[@code='b']">
                                <xsl:text>: </xsl:text><xsl:value-of select="subfield[@code='b']"/>
                        </xsl:if>
                </xsl:for-each>
                <xsl:for-each select="datafield[@tag='111']">
                        <xsl:value-of select="subfield[@code='a']"/>
                </xsl:for-each>
        </title>
        <link>
                <xsl:value-of select="fn:eval_bibformat(controlfield[@tag=001],'&lt;BFE_SERVER_INFO var=&quot;recurl&quot;>')" />
        </link>
        <description>
                <xsl:value-of select="fn:eval_bibformat(controlfield[@tag=001],'&lt;BFE_ABSTRACT print_lang=&quot;auto&quot;  separator_en=&quot; &quot;   separator_fr=&quot; &quot;  escape=&quot;4&quot; >')" />
        </description>

	<xsl:choose>
            <xsl:when test="contains(datafield[(@tag='100' or @tag='110' or @tag='700' or @tag='710')]/subfield[@code='a'], '@')">
                <!-- Email address: we can use author -->
	         <author>
                    <xsl:value-of select="datafield[(@tag='100' or @tag='110' or @tag='700' or @tag='710')]/subfield[@code='a']"/>
                </author>
            </xsl:when>
            <xsl:otherwise>
                <dc:creator>
                    <xsl:value-of select="datafield[(@tag='100' or @tag='110' or @tag='700' or @tag='710')]/subfield[@code='a']"/>
                </dc:creator>
            </xsl:otherwise>
	</xsl:choose>

        <pubDate>
                <xsl:value-of select="fn:creation_date(controlfield[@tag=001], '%a, %d %b %Y %H:%M:%S GMT')"/>
        </pubDate>
        <guid>
                <xsl:value-of select="fn:eval_bibformat(controlfield[@tag=001],'&lt;BFE_SERVER_INFO var=&quot;recurl&quot;>')" />

        </guid>

	<!-- Additionnal Dublic Core tags. Mainly used for books -->

	<xsl:for-each select="datafield[@tag='020' and @ind1=' ' and @ind2=' ']">
	  <!-- ISBN -->
	  <xsl:if test="subfield[@code='a']">
	    <dc:identifier>urn:ISBN:<xsl:value-of select="subfield[@code='a']"/></dc:identifier>
	  </xsl:if>
	</xsl:for-each>

	<xsl:for-each select="datafield[@tag='022' and @ind1=' ' and @ind2=' ']">
	  <!-- ISSN -->
	  <xsl:if test="subfield[@code='a']">
	    <dc:identifier>urn:ISSN:<xsl:value-of select="subfield[@code='a']"/></dc:identifier>
	  </xsl:if>
	</xsl:for-each>

        <xsl:if test="datafield[@tag='260' and @ind1=' ' and @ind2=' ']/subfield[@code='b']">
	  <!-- Publisher -->
          <dc:publisher>
            <xsl:value-of select="datafield[@tag='260' and @ind1=' ' and @ind2=' ']/subfield[@code='b']" />
          </dc:publisher>
        </xsl:if>

        <xsl:if test="datafield[@tag='260' and @ind1=' ' and @ind2=' ']/subfield[@code='c']">
	  <!-- Date -->
          <dcterms:issued>
            <xsl:value-of select="datafield[@tag='260' and @ind1=' ' and @ind2=' ']/subfield[@code='c']" />
          </dcterms:issued>
        </xsl:if>

</xsl:template>
</xsl:stylesheet>
