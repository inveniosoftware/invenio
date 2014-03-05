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
<name>EndNote</name>
<description>EndNote</description>
-->

<!--

This stylesheet transforms a MARCXML input into an EndNote output.
This stylesheet is provided only as an example of transformation.

-->
<xsl:stylesheet version="1.0"
xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
xmlns:marc="http://www.loc.gov/MARC21/slim"
xmlns:fn="http://cdsweb.cern.ch/bibformat/fn"
exclude-result-prefixes="marc fn">
<xsl:output method="xml"  indent="yes" encoding="UTF-8" omit-xml-declaration="yes"/>
<xsl:template match="/">
	<xsl:if test="collection">
			<xsl:for-each select="collection">
				<xsl:for-each select="record">
                                        <record>
					        <xsl:apply-templates select="."/>
                                        </record>
				</xsl:for-each>
			</xsl:for-each>
	</xsl:if>
	<xsl:if test="record">
                <record>
			<xsl:apply-templates/>
		</record>
	</xsl:if>
 </xsl:template>

<xsl:template match="record">
        <contributors>
            <xsl:if test="datafield[(@tag='100' or @tag='700') and @ind1=' ' and @ind2=' ']">
            <authors>
            <xsl:for-each select="datafield[(@tag='100' or @tag='700') and @ind1=' ' and @ind2=' ']">
                <author>
                <xsl:value-of select="subfield[@code='a']" />
                </author>
            </xsl:for-each>
            </authors>
            </xsl:if>
        </contributors>
        <titles>
            <title>
                    <xsl:for-each select="datafield[@tag='245' and @ind1=' ' and @ind2=' ']">
                            <xsl:value-of select="subfield[@code='a']"/>
                            <xsl:if test="subfield[@code='b']">
                                    <xsl:text>: </xsl:text><xsl:value-of select="subfield[@code='b']"/>
                            </xsl:if>
                    </xsl:for-each>
            </title>
            <secondary-title>
                    <xsl:value-of select="datafield[@tag='773' and @ind1=' ' and @ind2=' ']/subfield[@code='p']"/>
            </secondary-title>
        </titles>
        <electronic-resource-num>
                <xsl:value-of select="datafield[@tag='024' and @ind1='7' and @ind2=' ']/subfield[@code='a']" />
        </electronic-resource-num>
        <pages>
                <xsl:value-of select="datafield[@tag='773' and @ind1=' ' and @ind2=' ']/subfield[@code='c']" />
                <xsl:value-of select="datafield[@tag='909' and @ind1='C' and @ind2='4']/subfield[@code='c']" />
        </pages>
        <volume>
                <xsl:value-of select="datafield[@tag='773' and @ind1=' ' and @ind2=' ']/subfield[@code='v']" />
                <xsl:value-of select="datafield[@tag='909' and @ind1='C' and @ind2='4']/subfield[@code='v']" />
        </volume>
        <number>
                <xsl:value-of select="datafield[@tag='773' and @ind1=' ' and @ind2=' ']/subfield[@code='n']" />
        </number>
        <xsl:if test="datafield[@tag='653' and @ind1='1' and @ind2=' ']/subfield[@code='a']">
        <keywords>
                <xsl:for-each select="datafield[@tag='653' and @ind1='1' and @ind2=' ']/subfield[@code='a']">
                        <keyword>
                                <xsl:value-of select="." />
                        </keyword>
                </xsl:for-each>
        </keywords>
        </xsl:if>
        <dates>
            <year>
                    <xsl:value-of select="fn:eval_bibformat(controlfield[@tag=001],'&lt;BFE_YEAR date_format=&quot;%Y&quot;>')" />
            </year>
            <xsl:if test="fn:eval_bibformat(controlfield[@tag=001],'&lt;BFE_DATE date_format=&quot;%Y-%m-%d&quot;>')">
            <pub-dates>
                <date>
                        <xsl:value-of select="fn:eval_bibformat(controlfield[@tag=001],'&lt;BFE_DATE date_format=&quot;%Y-%m-%d&quot;>')" />
                </date>
            </pub-dates>
            </xsl:if>
        </dates>
        <abstract>
            <xsl:value-of select="datafield[@tag='520' and @ind1=' ' and @ind2=' ']/subfield[@code='a']" />
        </abstract>
</xsl:template>
</xsl:stylesheet>
