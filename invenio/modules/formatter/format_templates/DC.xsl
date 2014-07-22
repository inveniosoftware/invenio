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
xmlns:invenio="http://invenio-software.org/elements/1.0"
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
            <dc:dc xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/oai_dc/ http://www.openarchives.org/OAI/2.0/oai_dc.xsd" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:invenio="http://invenio-software.org/elements/1.0">
                <xsl:apply-templates/>
            </dc:dc>
        </xsl:if>
    </xsl:template>
    <xsl:template match="record">
      <!-- DOI -->
      <xsl:if test="datafield[@tag=024 and @ind1=7 and (subfield[@code='2']='doi' or subfield[@code='2']='DOI')]">
	<xsl:for-each select="datafield[@tag=024 and @ind1=7 and (subfield[@code='2']='doi' or subfield[@code='2']='DOI')]">
	  <dc:identifier><xsl:text>doi:</xsl:text><xsl:value-of select="subfield[@code='a']"/></dc:identifier>
	</xsl:for-each>
      </xsl:if>
      <!-- Language -->
        <xsl:for-each select="datafield[@tag=041]">
            <dc:language>
                <xsl:value-of select="subfield[@code='a']"/>
            </dc:language>
        </xsl:for-each>
	<!-- Author/Creator -->
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
	<!-- Corporate Author/Creator, if no main author/creator -->
	<xsl:if test="not (datafield[@tag=100 and subfield[@code='a']] or datafield[@tag=700 and subfield[@code='a']])">
	  <xsl:for-each select="datafield[@tag=110 and subfield[@code='a']]">
	    <dc:creator><xsl:value-of select="subfield[@code='a']"/></dc:creator>
	  </xsl:for-each>
	  <xsl:for-each select="datafield[@tag=710 and subfield[@code='a']]">
	    <dc:creator><xsl:value-of select="subfield[@code='a']"/></dc:creator>
	  </xsl:for-each>
	</xsl:if>
	<!-- Title -->
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
	<!-- Subject -->
        <xsl:for-each select="datafield[@tag=650 and @ind1=1 and @ind2=7]">
            <dc:subject>
                <xsl:value-of select="subfield[@code='a']"/>
            </dc:subject>
        </xsl:for-each>
	<!-- Main report number-->
	<xsl:for-each select="datafield[@tag=037]">
          <dc:identifier><xsl:value-of select="subfield[@code='a']"/></dc:identifier>
        </xsl:for-each>
	<!-- Additional report number-->
	<xsl:for-each select="datafield[@tag=088]">
          <dc:identifier><xsl:value-of select="subfield[@code='a']"/></dc:identifier>
        </xsl:for-each>
	<!-- Files -->
<!--        <xsl:for-each select="datafield[@tag=856 and @ind1=4]">
            <dc:identifier>
                <xsl:value-of select="subfield[@code='u']"/>
            </dc:identifier>
        </xsl:for-each>
-->
	<!-- Abstract -->
        <xsl:for-each select="datafield[@tag=520]">
            <dc:description>
                <xsl:value-of select="subfield[@code='a']"/>
            </dc:description>
        </xsl:for-each>
	<!-- Publisher -->
	<xsl:for-each select="datafield[@tag=260]">
	  <dc:publisher><xsl:value-of select="subfield[@code='b']"/></dc:publisher>
	</xsl:for-each>
	<!-- Date. Please keep ISO 8601 format -->
	<xsl:variable name="date" select="fn:eval_bibformat(controlfield[@tag='001'],'&lt;BFE_DATE date_format=&quot;%Y-%m-%d&quot; source_formats=&quot;%d %b %Y&quot; source_fields=&quot;269__c,260__c&quot;>')" />
	<xsl:choose>
	  <xsl:when test="$date">
	    <!-- Metadata date -->
	    <dc:date><xsl:value-of select="$date"/></dc:date>
	  </xsl:when>
	  <xsl:otherwise>
	    <!-- Record creation date-->
	    <dc:date><xsl:value-of select="fn:creation_date(controlfield[@tag=001])"/></dc:date>
	  </xsl:otherwise>
	</xsl:choose>
            <dc:source>
                <xsl:value-of select="fn:eval_bibformat(controlfield[@tag=001],'&lt;BFE_SERVER_INFO var=&quot;absoluterecurl&quot; >')" />
            </dc:source>
        <xsl:for-each select="datafield[@tag=024 and @ind1=7]">
            <xsl:if test="subfield[@code='2']">
                <dc:doi>
                    <xsl:value-of select="subfield[@code='a']"/>
                </dc:doi>
           </xsl:if>
        </xsl:for-each>
	<!-- Type -->
        <xsl:for-each select="datafield[@tag=650 and @ind1=2]">
            <xsl:if test="subfield[@code='a']">
                <dc:type>
                    <xsl:value-of select="subfield[@code='a']"/>
                </dc:type>
            </xsl:if>
        </xsl:for-each>
	<!-- Link to main record -->
	<dc:identifier><xsl:value-of select="fn:eval_bibformat(controlfield[@tag='001'],'&lt;BFE_SERVER_INFO var=&quot;recinternaldoiurl_or_recurl&quot;>')"/></dc:identifier>
	<!-- OAI Identifier -->
	<xsl:value-of disable-output-escaping="yes" select="fn:eval_bibformat(controlfield[@tag='001'],'&lt;BFE_OAI_IDENTIFIER instance_prefix=&quot;&lt;dc:identifier>&quot; separator=&quot;&quot; instance_suffix=&quot;&lt;/dc:identifier>&quot;>')"/>
	<xsl:if test="fn:eval_bibformat(controlfield[@tag=001],'&lt;BFE_SERVER_INFO var=&quot;CFG_SITE_NAME&quot; >')='CERN Document Server'">
	  <!-- Some CERN-specific tags for the CERN Global Network. TODO: investigate if this could go by default everywhere -->
	    <xsl:for-each select="datafield[@tag=111]">
		<xsl:if test="subfield[@code='c']">
		    <invenio:conference.place>
			<xsl:value-of select="subfield[@code='c']"/>
		    </invenio:conference.place>
		</xsl:if>
		<xsl:if test="subfield[@code='d']">
		    <invenio:conference.dates>
			<xsl:value-of select="subfield[@code='d']"/>
		    </invenio:conference.dates>
		</xsl:if>
	    </xsl:for-each>
	    <xsl:for-each select="datafield[@tag=270]">
		<xsl:if test="subfield[@code='a']">
		    <invenio:conference.contact-address>
			<xsl:value-of select="subfield[@code='a']"/>
		    </invenio:conference.contact-address>
		</xsl:if>
		<xsl:if test="subfield[@code='k']">
		    <invenio:conference.contact-phone>
			<xsl:value-of select="subfield[@code='k']"/>
		    </invenio:conference.contact-phone>
		</xsl:if>
		<xsl:if test="subfield[@code='l']">
		    <invenio:conference.contact-fax>
			<xsl:value-of select="subfield[@code='l']"/>
		    </invenio:conference.contact-fax>
		</xsl:if>
		<xsl:if test="subfield[@code='m']">
		    <invenio:conference.contact-email>
			<xsl:value-of select="subfield[@code='m']"/>
		    </invenio:conference.contact-email>
		</xsl:if>
	    </xsl:for-each>
	    <xsl:for-each select="datafield[@tag=500]">
		<xsl:if test="subfield[@code='a']">
		    <invenio:conference.notes>
			<xsl:value-of select="subfield[@code='a']"/>
		    </invenio:conference.notes>
		</xsl:if>
	    </xsl:for-each>
	</xsl:if>
    </xsl:template>
</xsl:stylesheet>
