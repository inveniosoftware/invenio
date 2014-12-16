<?xml version="1.0" encoding="UTF-8"?>
<!-- $Id$

     This file is part of Invenio.
     Copyright (C) 2008, 2010, 2011 CERN.

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
<name>RefWorks</name>
<description>RefWorks</description>
-->

<!--
This stylesheet transforms a MARCXML input into an Refworks output.
This stylesheet is provided only as an example of transformation.
-->

<xsl:stylesheet version="1.0"
xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
xmlns:marc="http://www.loc.gov/MARC21/slim"
exclude-result-prefixes="marc fn">
<xsl:output method="xml"  indent="yes" encoding="UTF-8" omit-xml-declaration="yes"/>
<xsl:template match="/">
	<xsl:if test="record">
		<reference>
			<xsl:apply-templates/>
		</reference>
	</xsl:if>
</xsl:template>

<xsl:template match="record">
                <xsl:for-each select="datafield[(@tag='100') and @ind1=' ' and @ind2=' ']">
	                <a1>
                                <xsl:value-of select="subfield[@code='a']" />
                        </a1>
                </xsl:for-each>
                <xsl:for-each select="datafield[(@tag='700') and @ind1=' ' and @ind2=' ']">
			<a2>
				<xsl:value-of select="subfield[@code='a']" />
			</a2>
		</xsl:for-each>
                        <t1>
                <xsl:for-each select="datafield[@tag='245' and @ind1=' ' and @ind2=' ']">
                        <xsl:value-of select="subfield[@code='a']"/>
                        <xsl:if test="subfield[@code='b']">
                                <xsl:text>: </xsl:text><xsl:value-of select="subfield[@code='b']"/>
                        </xsl:if>
                </xsl:for-each>
                        </t1>
        <t2>
                <xsl:value-of select="datafield[@tag='773' and @ind1=' ' and @ind2=' ']/subfield[@code='p']"/>
        </t2>
	<sn>
		<xsl:value-of select="datafield[@tag='020' and @ind1=' ' and @ind2=' ']/subfield[@code='a']" />
		<xsl:value-of select="datafield[@tag='022' and @ind1=' ' and @ind2=' ']/subfield[@code='a']" />
	</sn>
        <op>
                <xsl:value-of select="datafield[@tag='773' and @ind1=' ' and @ind2=' ']/subfield[@code='c']" />
                <xsl:value-of select="datafield[@tag='909' and @ind1='C' and @ind2='4']/subfield[@code='c']" />
        </op>
        <vo>
                <xsl:value-of select="datafield[@tag='773' and @ind1=' ' and @ind2=' ']/subfield[@code='v']" />
                <xsl:value-of select="datafield[@tag='909' and @ind1='C' and @ind2='4']/subfield[@code='v']" />
        </vo>
        <ab>
            <xsl:value-of select="datafield[@tag='520' and @ind1=' ' and @ind2=' ']/subfield[@code='a']" />
        </ab>
        <la>
            <xsl:value-of select="datafield[@tag='041' and @ind1=' ' and @ind2=' ']/subfield[@code='a']" />
        </la>
        <k1>
                <xsl:for-each select="datafield[@tag='653' and @ind1='1' and @ind2=' ']">
                      <xsl:value-of select="subfield[@code='a']" />;
                </xsl:for-each>
        </k1>
        <pb>
            <xsl:value-of select="datafield[@tag='260' and @ind1=' ' and @ind2=' ']/subfield[@code='b']" />
        </pb>
        <pp>
            <xsl:value-of select="datafield[@tag='260' and @ind1=' ' and @ind2=' ']/subfield[@code='a']" />
        </pp>
        <yr>
            <xsl:value-of select="datafield[@tag='260' and @ind1=' ' and @ind2=' ']/subfield[@code='c']" />
        </yr>
        <ed>
            <xsl:value-of select="datafield[@tag='250' and @ind1=' ' and @ind2=' ']/subfield[@code='a']" />
        </ed>
	<ul>
	<xsl:for-each select="datafield[@tag='856' and @ind1='4' and @ind2=' ']/subfield[@code='u' or @code='q']">
		<xsl:value-of select="." />;
	</xsl:for-each>
	</ul>
	<no>Imported from Invenio.</no>
</xsl:template>
</xsl:stylesheet>
