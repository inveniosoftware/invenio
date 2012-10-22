<?xml version="1.0" encoding="UTF-8"?>
<!--
     This file is part of Invenio.
     Copyright (C) 2011 CERN.

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
<name>Podcast</name>
<description>Sample format suitable for multimedia feeds, such as podcasts</description>
-->

<!--

This stylesheet transforms a MARCXML input into a multimedia RSS.
It is different from the standard RSS output in the following ways:
- it includes the <enclosure> tag, which links to multimedia file
- it generate one <item> tag per multimedia elements (so it can generate
  more than one item per record)
- it includes additional tags

This stylesheet is provided only as an example of transformation.

Considers only records having subfield 8564_u ending with .mp4 or
.mp3, or 8567_u where $x is mp3128 or mp40600 or mp4podcast.

Note that due to how Podcast readers identify compatible files, it
might be that links to Invenio "subformats" might not be accepted. For
eg.  <http://mysite/record/1/files/video.mp4?subformat=low-res> might
not be accepted as the URL is not seen as ending with '.mp4'. Some
tricks might be used:
<http://mysite/record/1/files/video.mp4?subformat=low-res.mp4> or
<http://mysite/record/1/files/video.mp4?subformat=low-res&extension=.mp4>

TODO: Consider adding PDF files, for ebooks podcasts
TODO: Consider adding an image for each episode
-->
<xsl:stylesheet version="1.0"
xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
xmlns:marc="http://www.loc.gov/MARC21/slim"
xmlns:fn="http://cdsweb.cern.ch/bibformat/fn"
xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd"
xmlns:dc="http://purl.org/dc/elements/1.1/"
xmlns:media="http://search.yahoo.com/mrss/"
xmlns:jwplayer="http://developer.longtailvideo.com/trac/"
exclude-result-prefixes="marc fn">
<xsl:output method="xml"  indent="yes" encoding="UTF-8" omit-xml-declaration="yes"/>

<xsl:template match="/">

 <xsl:for-each select="//datafield[(@tag='856' and @ind1='4' and @ind2=' ' and (substring(subfield[@code='u'], string-length(subfield[@code='u']) - string-length('.mp4') + 1) = '.mp4') or (substring(subfield[@code='u'], string-length(subfield[@code='u']) - string-length('.mp3') + 1) = '.mp3')) or (@tag='856' and @ind1='7' and @ind2=' ' and (subfield[@code='x']='mp3128' or subfield[@code='x']='mp40600' or subfield[@code='x']='mp4podcast'))]/subfield[@code='u']">
        <item>
	  <!-- <xsl:value-of select="substring-after(., '.')" />-->
        <xsl:variable name="tirage" select="../subfield[@code='8']" />
        <title>
                <xsl:value-of select="../../datafield[@tag='245' and @ind1=' ' and @ind2=' ']/subfield[@code='a']" />
        </title>
        <link>
                <xsl:value-of select="fn:eval_bibformat(../../controlfield[@tag=001],'&lt;BFE_SERVER_INFO var=&quot;absoluterecurl&quot;>')" />
        </link>
        <description>
		<xsl:value-of select="fn:eval_bibformat(../../controlfield[@tag=001],'&lt;BFE_ABSTRACT print_lang=&quot;auto&quot;  separator_en=&quot; &quot;   separator_fr=&quot; &quot;  escape=&quot;4&quot; >')" />
        </description>

	<xsl:choose>
            <xsl:when test="contains(datafield[(@tag='100' or @tag='700') and @ind1=' ' and @ind2=' ']/subfield[@code='a'], '@')">
                <!-- Email address: we can use author -->
	         <author>
                    <xsl:value-of select="datafield[(@tag='100' or @tag='700') and @ind1=' ' and @ind2=' ']/subfield[@code='a']"/>
                </author>
            </xsl:when>
            <xsl:otherwise>
                <dc:creator>
                    <xsl:value-of select="datafield[(@tag='100' or @tag='700') and @ind1=' ' and @ind2=' ']/subfield[@code='a']"/>
                </dc:creator>
            </xsl:otherwise>
	</xsl:choose>

        <pubDate>
		<xsl:value-of select="fn:creation_date(../../controlfield[@tag=001], '%a, %d %b %Y %H:%M:%S GMT')"/>
        </pubDate>
        <guid>
                <xsl:value-of select="."/>
        </guid>

        <enclosure>
             <xsl:attribute name="url"><xsl:value-of select="."/></xsl:attribute>
             <xsl:attribute name="length">0</xsl:attribute>
             <xsl:choose>
                <xsl:when test="../subfield[@code='x']='mp3128' or (substring(., string-length(.) - string-length('.mp3') + 1) = '.mp3')">
                    <xsl:attribute name="type">audio/mpeg</xsl:attribute>
                </xsl:when>
		<xsl:when test="../subfield[@code='x']='mp40600' or (substring(., string-length(.) - string-length('.mp4') + 1) = '.mp4')">
                    <xsl:attribute name="type">video/mp4</xsl:attribute>
                </xsl:when>
             </xsl:choose>
        </enclosure>
	<!-- Some specific fields for the Longtail video player (in the context of MediaArchive, CERN) -->
	<xsl:if test="starts-with(., 'http://mediaarchive.cern.ch/MediaArchive/')">
	  <jwplayer:file><xsl:value-of select="substring(., 42)"/></jwplayer:file>
	  <jwplayer:provider>rtmp</jwplayer:provider>
	  <jwplayer:streamer>rtmp://wowza.cern.ch:1935/vod</jwplayer:streamer>
        </xsl:if>

        <media:content>
        <xsl:attribute name="url"><xsl:value-of select="."/></xsl:attribute>
        </media:content>

	<!-- Image preview -->
        <xsl:for-each select="../../datafield[@tag='856' and @ind1='4' and @ind2=' ' and (substring(subfield[@code='u'], string-length(subfield[@code='u']) - string-length('.jpg') + 1) = '.jpg')]/subfield[@code='u']">
          <itunes:image>
            <xsl:attribute name="url"><xsl:value-of select="."/></xsl:attribute>
          </itunes:image>
        </xsl:for-each>

	<!-- Image preview, in the context of MediaArchive (CERN) -->
        <xsl:for-each select="../../datafield[@tag='856' and @ind1='7' and @ind2=' ' and subfield[@code='x']='jpgIcon']">
            <xsl:if test="subfield[@code='8']=$tirage">
                <itunes:image>
                        <xsl:attribute name="url"><xsl:value-of select="subfield[@code='u']"/></xsl:attribute>
                </itunes:image>
            </xsl:if>
        </xsl:for-each>


        <itunes:author>
                <xsl:value-of select="../../datafield[(@tag='100' or @tag='700') and @ind1=' ' and @ind2=' ']/subfield[@code='a']"/>
        </itunes:author>

        <itunes:subtitle>
                <xsl:value-of select="../../datafield[@tag='245' and @ind1=' ' and @ind2=' ']/subfield[@code='b']" />
        </itunes:subtitle>

        <itunes:summary>
		<xsl:value-of select="fn:eval_bibformat(../../controlfield[@tag=001],'&lt;BFE_ABSTRACT print_lang=&quot;auto&quot;  separator_en=&quot; &quot;   separator_fr=&quot; &quot;  escape=&quot;4&quot; >')" />
        </itunes:summary>

        <itunes:keywords>
                <xsl:for-each select="../../datafield[@tag='653' and @ind1='1' and @ind2=' ']/subfield[@code='a']">
                        <xsl:value-of select="." /><xsl:text>, </xsl:text>
                </xsl:for-each>
        </itunes:keywords>

	<!-- Content duration. Assuming it is in a good format, in well defined field. See BFE for details -->
	<xsl:variable name="duration" select="fn:eval_bibformat(../../controlfield[@tag=001],'&lt;BFE_DURATION >')" />
	<xsl:if test="$duration !=''">
	    <itunes:duration xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd"><xsl:value-of select="$duration" /></itunes:duration>
        </xsl:if>
        </item>
    </xsl:for-each>

</xsl:template>

</xsl:stylesheet>
