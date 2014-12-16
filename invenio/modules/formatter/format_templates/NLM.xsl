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
<name>NLM</name>
<description>NLM</description>
TODO: - Implement THESIS output (if needed?)
      - Add 'day' and 'month' tags
      - Add 'nlm-citation' tag
-->

<xsl:stylesheet version="1.0"
xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
xmlns:xlink="http://www.w3.org/1999/xlink/"
xmlns:marc="http://www.loc.gov/MARC21/slim"
xmlns:fn="http://cdsweb.cern.ch/bibformat/fn"
exclude-result-prefixes="marc fn">
<!-- <xsl:output method="xml" doctype-system="nlm_lib/2.3/journalpublishing.dtd"
     doctype-public="-//NLM//DTD Journal Publishing DTD v2.3 20070202//EN" indent="yes" encoding="UTF-8"/> -->
<xsl:output method="xml"  indent="yes" encoding="UTF-8" omit-xml-declaration="yes"/>
  <xsl:template match='/' >
      <xsl:for-each select="//record">
        <xsl:choose>
            <xsl:when test="datafield[@tag='980' and @ind1=' ' and @ind2=' ']/subfield[@code='c'] = 'DELETED'" >
                <xsl:apply-templates select="." mode="NLM_DELETED"/>
            </xsl:when>
            <xsl:when test="datafield[@tag='980' and @ind1=' ' and @ind2=' ']/subfield[@code='a'] = 'ARTICLE'" >
                <xsl:apply-templates select="." mode="NLM_ARTICLE"/>
            </xsl:when>
            <xsl:when test="datafield[@tag='980' and @ind1=' ' and  @ind2=' ']/subfield[@code='a'] = 'REPORT'" >
                <xsl:apply-templates select="." mode="NLM_REPORT"/>
            </xsl:when>
            <xsl:when test="datafield[@tag='980' and @ind1=' ' and  @ind2=' ']/subfield[@code='a'] = 'THESIS'" >
                <xsl:apply-templates select="." mode="NLM_REPORT"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:apply-templates select="." mode="NLM_DEFAULT"/>
            </xsl:otherwise>
        </xsl:choose>
      </xsl:for-each>
  </xsl:template>

  <xsl:template match="record" mode="NLM_ARTICLE">
    <article>
      <front>
        <journal-meta>
          <journal-title><!--<bx:field name="journal_name_long"/>-->
                <xsl:value-of select="datafield[@tag='222' and @ind1=' ' and @ind2=' ']/subfield[@code='a']" />
                <xsl:value-of select="datafield[@tag='210' and @ind1=' ' and @ind2=' ']/subfield[@code='a']" />
                <xsl:value-of select="datafield[@tag='773' and @ind1=' ' and @ind2=' ']/subfield[@code='p']" />
                <xsl:value-of select="datafield[@tag='909' and @ind1='C' and @ind2='4']/subfield[@code='p']" />
          </journal-title>
          <abbrev-journal-title>
                <xsl:value-of select="datafield[@tag='210' and @ind1=' ' and @ind2=' ']/subfield[@code='a']" />
                <xsl:value-of select="datafield[@tag='773' and @ind1=' ' and @ind2=' ']/subfield[@code='p']" />
                <xsl:value-of select="datafield[@tag='909' and @ind1='C' and @ind2='4']/subfield[@code='p']" />
          </abbrev-journal-title>

          <issn>
                <xsl:value-of select="fn:eval_bibformat(controlfield[@tag=001],'&lt;BFE_ISSN>')" />
                <xsl:value-of select="datafield[@tag='022' and @ind1=' ' and @ind2=' ']/subfield[@code='a']" />
          </issn>
          <xsl:if test="datafield[@tag='260' and @ind1=' ' and @ind2=' ']/subfield[@code='v']">
             <publisher>
               <publisher-name>
                 <xsl:value-of select="datafield[@tag='260' and @ind1=' ' and @ind2=' ']/subfield[@code='b']" />
               </publisher-name>
             </publisher>
          </xsl:if>
        </journal-meta>
        <article-meta>
          <title-group>
            <article-title>
                <xsl:for-each select="datafield[@tag='245' and @ind1=' ' and @ind2=' ']/subfield[@code='a']">
                    <xsl:value-of select="." />
                </xsl:for-each>
            </article-title>
          </title-group>
          <xsl:if test="datafield[@tag='773' and @ind1=' ' and @ind2=' ']/subfield[@code='a']">
              <article-id pub-id-type="doi">
                <xsl:value-of select="datafield[@tag='773' and @ind1=' ' and @ind2=' ']/subfield[@code='a']" />
              </article-id>
          </xsl:if>
          <contrib-group>
            <xsl:for-each select="datafield[(@tag='100' or @tag='700') and @ind1=' ' and @ind2=' ']">
              <contrib contrib-type="author">
               <name>
                <surname>
                    <xsl:value-of select="normalize-space(substring-before(subfield[@code='a'], ','))" />
                </surname>
                <given-names>
                    <xsl:value-of select="normalize-space(substring-after(subfield[@code='a'], ','))" />
                </given-names>
               </name>
               <xsl:for-each select="subfield[@code='u']">
                  <aff>
                      <institution>
                          <xsl:value-of select="." />
                      </institution>
                  </aff>
               </xsl:for-each>
              </contrib>
          </xsl:for-each>
          </contrib-group>
          <pub-date pub-type="pub">
        <!--
            <xsl:if test="fn:eval_bibformat(controlfield[@tag=001],'&lt;BFE_YEAR date_format=&quot;%d&quot;>')">
              <day>
                <xsl:value-of select="fn:eval_bibformat(controlfield[@tag=001],'&lt;BFE_YEAR date_format=&quot;%d&quot;>')" />
              </day>
            </xsl:if>
            <xsl:if test="fn:eval_bibformat(controlfield[@tag=001],'&lt;BFE_YEAR date_format=&quot;%m&quot;>')">
              <month>
                <xsl:value-of select="fn:eval_bibformat(controlfield[@tag=001],'&lt;BFE_YEAR date_format=&quot;%m&quot;>')" />
              </month>
            </xsl:if>
        -->
            <year>
                <xsl:value-of select="fn:eval_bibformat(controlfield[@tag=001],'&lt;BFE_YEAR date_format=&quot;%Y&quot;>')" />
           </year>
          </pub-date>
          <volume>
                <xsl:value-of select="datafield[@tag='773' and @ind1=' ' and @ind2=' ']/subfield[@code='v']" />
                <xsl:value-of select="datafield[@tag='909' and @ind1='C' and @ind2='4']/subfield[@code='v']" />
          </volume>
          <xsl:if test="/datafield[@tag='773' and @ind1=' ' and @ind2=' ']/subfield[@code='n']">
            <issue>
                <xsl:value-of select="datafield[@tag='773' and @ind1=' ' and @ind2=' ']/subfield[@code='n']" />
            </issue>
          </xsl:if>
          <fpage>
                <xsl:value-of select="normalize-space(substring-before(datafield[@tag='773' and @ind1=' ' and @ind2=' ']/subfield[@code='c'], '-'))" />
                <xsl:value-of select="normalize-space(substring-before(datafield[@tag='909' and @ind1='C' and @ind2='4']/subfield[@code='c'], '-'))" />
          </fpage>
          <lpage>
                <xsl:value-of select="normalize-space(substring-after(datafield[@tag='773' and @ind1=' ' and @ind2=' ']/subfield[@code='c'], '-'))" />
                <xsl:value-of select="normalize-space(substring-after(datafield[@tag='909' and @ind1='C' and @ind2='4']/subfield[@code='c'], '-'))" />
          </lpage>
          <self-uri xmlns:xlink="http://www.w3.org/1999/xlink/" >
                <xsl:attribute name="xlink:href">
                <xsl:value-of select="fn:eval_bibformat(controlfield[@tag=001],'&lt;BFE_SERVER_INFO var=&quot;absoluterecurl&quot;>')" />
                </xsl:attribute>
          </self-uri>
          <xsl:for-each select="datafield[@tag='856' and @ind1='4' and @ind2=' ']/subfield[@code='u' or @code='q']">
              <self-uri xmlns:xlink="http://www.w3.org/1999/xlink/" >
                <xsl:attribute name="xlink:href"><xsl:value-of select="."/></xsl:attribute>
              </self-uri>
          </xsl:for-each>
        </article-meta>
        <abstract>
            <xsl:value-of select="datafield[@tag='520' and @ind1=' ' and @ind2=' ']/subfield[@code='a']" />
        </abstract>
      </front>
      <article-type>research-article</article-type>
      <ref>
<!--        <xsl:for-each object="reference">
          <nlm-citation>
            <comment><bx:field name="reference"/></comment>
          </nlm-citation>
        </xsl:for-each>
-->
      </ref>
    </article>
  </xsl:template>

  <xsl:template match="record" mode="NLM_REPORT">
    <article>
      <front>
        <publisher>
            <publisher-name>
                 <xsl:value-of select="datafield[@tag='260' and @ind1=' ' and @ind2=' ']/subfield[@code='b']" />
            </publisher-name>
            <publisher-loc>
                 <xsl:value-of select="datafield[@tag='260' and @ind1=' ' and @ind2=' ']/subfield[@code='a']" />
            </publisher-loc>
        </publisher>
        <article-meta>
          <title-group>
            <article-title>
                <xsl:for-each select="datafield[@tag='245' and @ind1=' ' and @ind2=' ']/subfield[@code='a']">
                    <xsl:value-of select="." />
                </xsl:for-each>
           </article-title>
          </title-group>
          <article-id pub-id-type="publisher-id">
          </article-id>
          <contrib-group>
            <xsl:for-each select="datafield[(@tag='100' or @tag='700') and @ind1=' ' and @ind2=' ']">
              <contrib contrib-type="author">
               <name>
                <surname>
                    <xsl:value-of select="normalize-space(substring-before(subfield[@code='a'], ','))" />
                </surname>
                <given-names>
                    <xsl:value-of select="normalize-space(substring-after(subfield[@code='a'], ','))" />
                </given-names>
               </name>
               <xsl:for-each select="subfield[@code='u']">
                  <aff>
                      <institution>
                          <xsl:value-of select="." />
                      </institution>
                  </aff>
               </xsl:for-each>
              </contrib>
          </xsl:for-each>
          </contrib-group>
          <pub-date pub-type="pub">
        <!--
            <xsl:if test="fn:eval_bibformat(controlfield[@tag=001],'&lt;BFE_YEAR date_format=&quot;%d&quot;>')">
              <day>
                <xsl:value-of select="fn:eval_bibformat(controlfield[@tag=001],'&lt;BFE_YEAR date_format=&quot;%d&quot;>')" />
              </day>
            </xsl:if>
            <xsl:if test="fn:eval_bibformat(controlfield[@tag=001],'&lt;BFE_YEAR date_format=&quot;%m&quot;>')">
              <month>
                <xsl:value-of select="fn:eval_bibformat(controlfield[@tag=001],'&lt;BFE_YEAR date_format=&quot;%m&quot;>')" />
              </month>
            </xsl:if>
        -->
            <year>
                <xsl:value-of select="fn:eval_bibformat(controlfield[@tag=001],'&lt;BFE_YEAR date_format=&quot;%Y&quot;>')" />
           </year>
          </pub-date>
          <self-uri xmlns:xlink="http://www.w3.org/1999/xlink/" >
                <xsl:attribute name="xlink:href">
                <xsl:value-of select="fn:eval_bibformat(controlfield[@tag=001],'&lt;BFE_SERVER_INFO var=&quot;absoluterecurl&quot;>')" />
                </xsl:attribute>
          </self-uri>
          <xsl:for-each select="datafield[@tag='856' and @ind1='4' and @ind2=' ']/subfield[@code='u' or @code='q']">
              <self-uri xmlns:xlink="http://www.w3.org/1999/xlink/" >
                <xsl:attribute name="xlink:href"><xsl:value-of select="."/></xsl:attribute>
              </self-uri>
          </xsl:for-each>
        </article-meta>
        <abstract>
            <xsl:value-of select="datafield[@tag='520' and @ind1=' ' and @ind2=' ']/subfield[@code='a']" />
        </abstract>
      </front>
      <article-type>technical-report</article-type>
    </article>
  </xsl:template>

  <xsl:template match="record" mode="NLM_DEFAULT">
    <article>
      <front>
        <article-meta>
          <title-group>
            <article-title>
                <xsl:for-each select="datafield[@tag='245' and @ind1=' ' and @ind2=' ']/subfield[@code='a']">
                    <xsl:value-of select="." />
                </xsl:for-each>
            </article-title>
          </title-group>
          <contrib-group>
            <xsl:for-each select="datafield[(@tag='100' or @tag='700') and @ind1=' ' and @ind2=' ']">
               <contrib contrib-type="author">
                  <name>
                      <surname>
                          <xsl:value-of select="normalize-space(substring-before(subfield[@code='a'], ','))" />
                      </surname>
                      <given-names>
                          <xsl:value-of select="normalize-space(substring-after(subfield[@code='a'], ','))" />
                      </given-names>
                  </name>
                  <xsl:for-each select="subfield[@code='u']">
                      <aff>
                          <institution>
                            <xsl:value-of select="." />
                          </institution>
                      </aff>
                  </xsl:for-each>
                </contrib>
            </xsl:for-each>
          </contrib-group>
          <pub-date pub-type="pub">
              <year>
                 <xsl:value-of select="fn:eval_bibformat(controlfield[@tag=001],'&lt;BFE_YEAR date_format=&quot;%Y&quot;>')" />
              </year>
          </pub-date>

          <self-uri xmlns:xlink="http://www.w3.org/1999/xlink/" >
                <xsl:attribute name="xlink:href">
                    <xsl:value-of select="fn:eval_bibformat(controlfield[@tag=001],'&lt;BFE_SERVER_INFO var=&quot;absoluterecurl&quot;>')" />
                </xsl:attribute>
          </self-uri>
          <xsl:for-each select="datafield[@tag='856' and @ind1='4' and @ind2=' ']/subfield[@code='u' or @code='q']">
            <self-uri xmlns:xlink="http://www.w3.org/1999/xlink/" >
                <xsl:attribute name="xlink:href"><xsl:value-of select="."/></xsl:attribute>
            </self-uri>
          </xsl:for-each>
        </article-meta>
        <abstract>
            <xsl:value-of select="datafield[@tag='520' and @ind1=' ' and @ind2=' ']/subfield[@code='a']" />
        </abstract>
      </front>
      <article-type>
        <xsl:value-of select="datafield[@tag='980' and @ind1=' ' and @ind2=' ']/subfield[@code='a']" />
      </article-type>
    </article>
  </xsl:template>

</xsl:stylesheet>
