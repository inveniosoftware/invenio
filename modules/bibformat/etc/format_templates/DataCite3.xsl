<?xml version="1.0" encoding="UTF-8"?>
<!-- $Id$

     This file is part of Invenio.
     Copyright (C) 2007, 2008, 2010, 2011 CERN.

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
<name>DataCite</name>
<description>DataCite XML</description>
-->
<!--
This stylesheet transforms a MARCXML input into DataCite output.
-->
<xsl:stylesheet version="1.0"
xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
xmlns:marc="http://www.loc.gov/MARC21/slim"
xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
xmlns:dc="http://purl.org/dc/elements/1.1/"
xmlns:fn="http://cdsweb.cern.ch/bibformat/fn"
xmlns:invenio="http://invenio-software.org/elements/1.0"
exclude-result-prefixes="marc fn dc invenio">
    <xsl:output method="xml"  indent="yes" encoding="UTF-8" omit-xml-declaration="yes"/>
    <xsl:variable name="LOWERCASE" select="'abcdefghijklmnopqrstuvwxyz'"/>
    <xsl:variable name="UPPERCASE" select="'ABCDEFGHIJKLMNOPQRSTUVWXYZ'"/>
    <xsl:template match="/">
        <xsl:if test="collection">
        </xsl:if>
        <xsl:if test="record">
            <resource xmlns="http://datacite.org/schema/kernel-3" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://datacite.org/schema/kernel-3 http://schema.datacite.org/meta/kernel-3/metadata.xsd">
                <xsl:apply-templates />
            </resource>
        </xsl:if>
    </xsl:template>
    <xsl:template match="record" xmlns="http://datacite.org/schema/kernel-3">
        <!-- 1. Identifier -->
        <xsl:choose>
            <xsl:when test="datafield[@tag=024 and @ind1=7]">
                <xsl:for-each select="datafield[@tag=024 and @ind1=7]">
                    <identifier>
                        <xsl:attribute name="identifierType">
                            <xsl:value-of select="subfield[@code='2']"/>
                     </xsl:attribute>
                        <xsl:value-of select="subfield[@code='a']"/>
                    </identifier>
                </xsl:for-each>
            </xsl:when>
            <xsl:otherwise>
                <identifier identifierType="URL"><xsl:value-of select="fn:eval_bibformat(controlfield[@tag=001],'&lt;BFE_RECORD_URL absolute=&quot;yes&quot; with_ln=&quot;no&quot;>')"/></identifier>
            </xsl:otherwise>
        </xsl:choose>
        <!-- 2. Creators -->
        <creators>
            <xsl:for-each select="datafield[@tag=100]">
                <creator>
                <creatorName>
                    <xsl:value-of select="subfield[@code='a']"/>
                </creatorName>
                <xsl:if test="subfield[@code='u']">
                    <affiliation>
                        <xsl:value-of select="subfield[@code='u']"/>
                    </affiliation>
                </xsl:if>
                </creator>
            </xsl:for-each>
            <xsl:for-each select="datafield[@tag=700]">
                <xsl:if test="not(subfield[@code='e'])">
                    <creator>
                        <creatorName>
                            <xsl:value-of select="subfield[@code='a']"/>
                        </creatorName>
                    <xsl:if test="subfield[@code='u']">
                        <affiliation>
                            <xsl:value-of select="subfield[@code='u']"/>
                        </affiliation>
                    </xsl:if>
                    </creator>
                </xsl:if>
            </xsl:for-each>
        </creators>
        <!-- 3. Titles -->
        <titles>
            <xsl:for-each select="datafield[@tag=245]">
                <title>
                    <xsl:value-of select="subfield[@code='a']"/>
                        <xsl:if test="subfield[@code='b']">
                            <xsl:text>: </xsl:text><xsl:value-of select="subfield[@code='b']"/>
                        </xsl:if>
                </title>
            </xsl:for-each>
            <xsl:for-each select="datafield[@tag=246]">
                <title titleType="TranslatedTitle">
                    <xsl:value-of select="subfield[@code='a']"/>
                        <xsl:if test="subfield[@code='b']">
                            <xsl:text>: </xsl:text><xsl:value-of select="subfield[@code='b']"/>
                        </xsl:if>
                </title>
            </xsl:for-each>
            <xsl:if test="datafield[@tag=111]/subfield[@code='a']">
                <title>
                    <xsl:value-of select="datafield[@tag=111]/subfield[@code='a']"/>
                </title>
            </xsl:if>
        </titles>
        <!-- 4. Publisher -->
        <publisher>
            <xsl:choose>
                <xsl:when test="datafield[@tag=260]/subfield[@code='b']">
                    <xsl:value-of select="datafield[@tag=260]/subfield[@code='b']"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:value-of select="fn:eval_bibformat(controlfield[@tag=001],'&lt;BFE_SERVER_INFO var=&quot;CFG_SITE_NAME&quot; >')"/>
                </xsl:otherwise>
            </xsl:choose>
        </publisher>
        <!-- 5. PublicationYear -->
        <publicationYear>
            <xsl:value-of select="fn:eval_bibformat(controlfield[@tag=001],'&lt;BFE_CREATION_DATE date_format=&quot;%Y&quot; >')"/>
        </publicationYear>
        <!-- 6. Subject -->
        <xsl:if test="datafield[@tag=653 and @ind1='1']">
            <subjects>
                <xsl:for-each select="datafield[@tag=653 and @ind1='1']">
                    <subject><xsl:value-of select="subfield[@code='a']"/></subject>
                </xsl:for-each>
            </subjects>
        </xsl:if>
        <!-- 7. Contributor -->
        <xsl:if test="datafield[@tag=700]/subfield[@code='e']">
            <contributors>
                <xsl:for-each select="datafield[@tag=700]">
                    <xsl:if test="subfield[@code='e']">
                        <xsl:choose>
                            <xsl:when test="subfield[@code='e']='dir.'">
                                <contributor contributorType="Supervisor">
                                    <contributorName>
                                    <xsl:value-of select="subfield[@code='a']"/>
                                </contributorName>
                                <xsl:if test="subfield[@code='u']">
                                    <affiliation>
                                        <xsl:value-of select="subfield[@code='u']"/>
                                    </affiliation>
                                </xsl:if>
                            </contributor>
                            </xsl:when>
                            <xsl:otherwise>
                                <contributor contributorType="Other">
                                <contributorName>
                                    <xsl:value-of select="subfield[@code='a']"/>
                                </contributorName>
                                <xsl:if test="subfield[@code='u']">
                                    <affiliation>
                                        <xsl:value-of select="subfield[@code='u']"/>
                                    </affiliation>
                                </xsl:if>
                            </contributor>
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:if>
                </xsl:for-each>
            </contributors>
        </xsl:if>
        <!-- 8. Date -->
        <!-- TODO: decide afterwards what to do what the dates depending on collection and workflow -->

        <!-- 9. Language -->
        <!-- TODO check if it works -->
        <xsl:for-each select="datafield[@tag=041][1]">
            <language>
                <xsl:value-of select="substring(subfield[@code='a']/text(),1,2)"/>
            </language>
        </xsl:for-each>

        <!-- 10 ResourceType -->
        <!-- TODO a knowledge base needs to be created 980 -> casrai dictionary -->

        <!-- 11 AlternateIdentifier -->
        <alternateIdentifiers>
            <alternateIdentifier alternateIdentifierType="URL"><xsl:value-of select="fn:eval_bibformat(controlfield[@tag=001],'&lt;BFE_RECORD_URL absolute=&quot;yes&quot; with_ln=&quot;no&quot;>')"/></alternateIdentifier>
            <xsl:for-each select="datafield[@tag=020]">
                <alternateIdentifier alternateIdentifierType="ISBN"><xsl:value-of select="subfield[@code='a']"/></alternateIdentifier>
            </xsl:for-each>
        </alternateIdentifiers>
        <!-- 12 RelatedIdentifier -->
        <!-- 13 Size -->
        <!-- 14 Format -->
        <!-- 15 Version -->
        <!-- 16 Rights -->
        <xsl:if test="datafield[@tag=540]/subfield[@code='a']">
            <rightsList>
                <xsl:for-each select="datafield[@tag=540]">
                    <rights> <xsl:value-of select="datafield[@tag=540]/subfield[@code='a']"/> </rights>
                </xsl:for-each>
            </rightsList>
        </xsl:if>
        <!-- 17 Description -->
        <descriptions>
            <xsl:for-each select="datafield[@tag=520]">
                <description descriptionType="Abstract">
                    <xsl:value-of select="subfield[@code='a']"/>
                </description>
            </xsl:for-each>
            <xsl:for-each select="datafield[@tag=500]">
                <description descriptionType="Other">
                    <xsl:value-of select="subfield[@code='a']"/>
                </description>
            </xsl:for-each>
            <xsl:if test="datafield[@tag='999' and @ind1='C' and @ind2='5']">
                <description descriptionType="Other">
                    [
                    <xsl:for-each select="datafield[@tag='999' and @ind1='C' and @ind2='5']">
                        "<xsl:value-of select="subfield[@code='x']"/>",
                    </xsl:for-each>
                    ]
                </description>
            </xsl:if>
        </descriptions>
    </xsl:template>
</xsl:stylesheet>
