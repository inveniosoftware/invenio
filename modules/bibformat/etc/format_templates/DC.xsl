<?xml version="1.0" encoding="UTF-8"?>
<!-- $Id$

     This file is part of Invenio.
     Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010 CERN.

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
<name>DC</name>
<description>XML Dublin Core</description>
-->

<!-- 

This stylesheet transforms a MARCXML input into an DC output.     
This stylesheet is provided only as an example of transformation.

-->
<xsl:stylesheet version="1.0"
xmlns:xsl="http://www.w3.org/1999/XSL/Transform" 
xmlns:marc="http://www.loc.gov/MARC21/slim" 
xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
xmlns:dc="http://purl.org/dc/elements/1.1/" 
xmlns:fn="http://cdsweb.cern.ch/bibformat/fn"
exclude-result-prefixes="marc fn">
        <xsl:output method="xml"  indent="yes" encoding="UTF-8" omit-xml-declaration="yes"/>
        <xsl:template match="/">
		<xsl:if test="collection">
			<dc:collection xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/oai_dc/ http://www.openarchives.org/OAI/2.0/oai_dc.xsd">
				<xsl:for-each select="collection">
					<xsl:for-each select="record">
						<dc:dc>
							<xsl:apply-templates select="."/>
						</dc:dc>
					</xsl:for-each>
				</xsl:for-each>
			</dc:collection>
		</xsl:if>
		<xsl:if test="record">
			<dc:dc xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/oai_dc/ http://www.openarchives.org/OAI/2.0/oai_dc.xsd" xmlns:dc="http://purl.org/dc/elements/1.1/">
				<xsl:apply-templates/>
			</dc:dc>
		</xsl:if>
        </xsl:template>
        <xsl:template match="record">
	        <xsl:for-each select="datafield[@tag=041]">
			<dc:language>
                                <xsl:value-of select="subfield[@code='a']"/>
			</dc:language>
		</xsl:for-each>
	        <xsl:for-each select="datafield[@tag=100]">
			<dc:creator>
                                <xsl:value-of select="subfield[@code='a']"/>
			</dc:creator>
		</xsl:for-each>
	        <xsl:for-each select="datafield[@tag=700]">
			<dc:creator>
                                <xsl:value-of select="subfield[@code='a']"/>
			</dc:creator>
		</xsl:for-each>
	        <xsl:for-each select="datafield[@tag=245]">
			<dc:title>
                                <xsl:value-of select="subfield[@code='a']"/>
                                <xsl:if test="subfield[@code='b']">
                                    <xsl:text>: </xsl:text><xsl:value-of select="subfield[@code='b']"/>
                                </xsl:if>
			</dc:title>
		</xsl:for-each>
	        <xsl:for-each select="datafield[@tag=111]">
			<dc:title>
                                <xsl:value-of select="subfield[@code='a']"/>
			</dc:title>
		</xsl:for-each>
	        <xsl:for-each select="datafield[@tag=650 and @ind1=1 and @ind2=7]">
			<dc:subject>
                                <xsl:value-of select="subfield[@code='a']"/>
			</dc:subject>
		</xsl:for-each>
	        <xsl:for-each select="datafield[@tag=856 and @ind1=4]">
			<dc:identifier>
                                <xsl:value-of select="subfield[@code='u']"/>
			</dc:identifier>
		</xsl:for-each>
	        <xsl:for-each select="datafield[@tag=520]">
			<dc:description>
                                <xsl:value-of select="subfield[@code='a']"/>
			</dc:description>
		</xsl:for-each>
                <dc:date>
                        <xsl:value-of select="fn:creation_date(controlfield[@tag=001])"/>
                </dc:date>
        </xsl:template>
</xsl:stylesheet>