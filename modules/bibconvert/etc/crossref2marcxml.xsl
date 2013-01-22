<?xml version="1.0" encoding="ISO-8859-1"?>
<xsl:stylesheet version="1.0"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:crossref="http://www.crossref.org/qrschema/2.0"
                xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                exclude-result-prefixes="crossref xsi">
  <xsl:output method="xml" indent="yes" encoding="UTF-8"/>
  <!-- ************ VARIABLES ************ -->
  <xsl:variable name="upper"
              select="'ABCDEFGHIJKLMNOPQRSTUVWXYZ'"/>
  <!-- ************ FUNCTIONS ************ -->
  <!-- FUNCTION doi-element: processes the DOI element -->
  <xsl:template name="doi-element">
    <xsl:param name="doi"/>
    <datafield tag="024" ind1="7" ind2=" ">
      <subfield code="a"><xsl:value-of select="$doi"/></subfield>
      <subfield code="2"><xsl:text>DOI</xsl:text></subfield>
    </datafield>
    <xsl:choose>
      <!-- checking different types of documents -->
      <xsl:when test="$doi[@type='journal_article']">
        <datafield tag="980" ind1=" " ind2=" ">
          <subfield code="a"><xsl:text>Published</xsl:text></subfield>
        </datafield>
        <datafield tag="980" ind1=" " ind2=" ">
          <subfield code="a"><xsl:text>citeable</xsl:text></subfield>
        </datafield>
      </xsl:when>
      <xsl:when test="$doi[@type='conference_paper']">
        <datafield tag="980" ind1=" " ind2=" ">
          <subfield code="a"><xsl:text>ConferencePaper</xsl:text></subfield>
        </datafield>
      </xsl:when>
    </xsl:choose>
  </xsl:template>
  <!-- FUNCTION contributors-element: processes the contributors element -->
  <xsl:template name="contributors-element">
    <xsl:param name="contributors"/>
    <xsl:for-each select="$contributors/crossref:contributor">
      <xsl:if test="@sequence='first'">
        <datafield tag="100" ind1=" " ind2=" ">
          <xsl:call-template name="print-a-authorname">
            <xsl:with-param name="given_name" select="./crossref:given_name"/>
            <xsl:with-param name="surname" select="./crossref:surname"/>
            <xsl:with-param name="role" select="@contributor_role"/>
          </xsl:call-template>
        </datafield>
      </xsl:if>
      <xsl:if test="@sequence='additional'">
        <datafield tag="700" ind1=" " ind2=" ">
          <xsl:call-template name="print-a-authorname">
            <xsl:with-param name="given_name" select="./crossref:given_name"/>
            <xsl:with-param name="surname" select="./crossref:surname"/>
            <xsl:with-param name="role" select="@contributor_role"/>
          </xsl:call-template>
        </datafield>
      </xsl:if>
    </xsl:for-each>
  </xsl:template>
  <!-- FUNCTION print-a-authorname: prints the authorname inside xxx__a subfield -->
  <xsl:template name="print-a-authorname">
    <xsl:param name="given_name"/>
    <xsl:param name="surname"/>
    <xsl:param name="role"/>
    <subfield code="a">
      <xsl:value-of select="normalize-space($surname)"/>
      <xsl:if test="normalize-space($given_name) != ''">
        <xsl:text>, </xsl:text>
        <xsl:value-of select="normalize-space($given_name)"/>
      </xsl:if>
    </subfield>
    <xsl:if test="$role='editor'">
      <subfield code="e"><xsl:text>ed.</xsl:text></subfield>
    </xsl:if>
  </xsl:template>
  <!-- FUNCTION process_title: process the journal title and put the volume letter in beginning of 773__v -->
  <xsl:template name="process_title">
    <xsl:param name="title_param"/>
    <xsl:param name="query"/>
    <xsl:variable name="last_two" select="substring($title_param, string-length($title_param)-1)" />
    <xsl:variable name="prefix">
    <xsl:choose>
      <xsl:when test="substring($last_two,1,1) = ' ' and not(translate(substring($last_two,2,1),$upper,''))">
          <xsl:value-of select="substring($last_two,2,1)"/>
      </xsl:when>
    </xsl:choose>
    </xsl:variable>
    <xsl:variable name="value">
    <xsl:choose>
      <xsl:when test="$prefix != ''">
        <subfield code="p"><xsl:value-of select="substring($title_param, 1, string-length($title_param)-2)"/></subfield>
      </xsl:when>
      <xsl:otherwise>
        <subfield code="p"><xsl:value-of select="$title_param"/></subfield>
      </xsl:otherwise>
    </xsl:choose>
    </xsl:variable>
    <xsl:copy-of select="$value" />
      <xsl:if test="normalize-space($query/crossref:volume) != ''">
        <xsl:call-template name="volume_field">
          <xsl:with-param name="prefix" select="$prefix"/>
          <xsl:with-param name="query" select="$query"/>
        </xsl:call-template>
      </xsl:if>
  </xsl:template>
  <!-- FUNCTION field-773: processes the elements that go to the 773 field -->
  <xsl:template name="field-773">
    <xsl:param name="query"/>
    <datafield tag="773" ind1=" " ind2=" ">
      <!-- Processing the title -->
      <xsl:choose>
        <xsl:when test="normalize-space($query/crossref:journal_title) != ''">
          <xsl:call-template name="process_title">
            <xsl:with-param name="title_param" select="$query/crossref:journal_title"/>
            <xsl:with-param name="query" select="$query"/>
          </xsl:call-template>
        </xsl:when>
        <xsl:when test="normalize-space($query/crossref:series_title) != ''">
          <xsl:call-template name="process_title">
            <xsl:with-param name="title_param" select="$query/crossref:series_title"/>
            <xsl:with-param name="query" select="$query"/>
          </xsl:call-template>
        </xsl:when>
        <xsl:otherwise>
          <xsl:if test="normalize-space($query/crossref:volume) != ''">
            <xsl:call-template name="volume_field">
              <xsl:with-param name="prefix" select="''"/>
              <xsl:with-param name="query" select="$query"/>
            </xsl:call-template>
          </xsl:if>
        </xsl:otherwise>
      </xsl:choose>
      <xsl:if test="normalize-space($query/crossref:issue) != ''">
        <subfield code="n"><xsl:value-of select="$query/crossref:issue"/></subfield>
      </xsl:if>
      <xsl:if test="normalize-space($query/crossref:first_page) != '' or normalize-space($query/crossref:last_page) != ''">
        <subfield code="c">
          <xsl:value-of select="$query/crossref:first_page"/>
          <!-- If no "last page" we don't put the dash -->
          <xsl:if test="normalize-space($query/crossref:last_page) != ''">
            <xsl:text>-</xsl:text>
            <xsl:value-of select="$query/crossref:last_page"/>
          </xsl:if>
        </subfield>
      </xsl:if>
      <!-- Year -->
      <xsl:if test="normalize-space($query/crossref:year) != ''">
        <xsl:variable name="media_print">
          <xsl:for-each select="$query/crossref:year[@media_type='print']">
            <subfield code="y"><xsl:value-of select="."/></subfield>
          </xsl:for-each>
        </xsl:variable>
        <xsl:choose>
          <xsl:when test="$media_print != ''">
            <xsl:copy-of select="$media_print"/>
          </xsl:when>
          <xsl:otherwise>
            <subfield code="y"><xsl:value-of select="$query/crossref:year"/></subfield>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:if>
    </datafield>
  </xsl:template>
  <!-- FUNCTION article_title: prints the article title -->
  <xsl:template name="article_title">
    <xsl:param name="title"/>
    <datafield tag="245" ind1=" " ind2=" ">
      <subfield code="a"><xsl:value-of select="normalize-space($title)"/></subfield>
    </datafield>
  </xsl:template>
  <!-- FUNCTION volume_field: prints the volume -->
  <xsl:template name="volume_field">
    <xsl:param name="query"/>
    <xsl:param name="prefix"/>
    <subfield code="v"><xsl:value-of select="$prefix"/><xsl:value-of select="normalize-space($query/crossref:volume)"/></subfield>
  </xsl:template>
  <!-- ************ MAIN CODE ************ -->
  <xsl:template match="/">
    <record>
      <xsl:apply-templates select="//crossref:body"/>
    </record>
  </xsl:template>

  <xsl:template match="//crossref:body">
    <xsl:if test="./crossref:query/crossref:doi">
      <xsl:call-template name="doi-element">
        <xsl:with-param name="doi" select="./crossref:query/crossref:doi"/>
      </xsl:call-template>
    </xsl:if>
    <xsl:if test="./crossref:query/crossref:journal_title
      or ./crossref:query/crossref:series_title
      or ./crossref:query/crossref:volume
      or ./crossref:query/crossref:issue
      or ./crossref:query/crossref:first_page
      or ./crossref:query/crossref:last_page
      or ./crossref:query/crossref:year">
      <xsl:call-template name="field-773">
        <xsl:with-param name="query" select="./crossref:query"/>
      </xsl:call-template>
    </xsl:if>
    <xsl:if test="./crossref:query/crossref:contributors">
      <xsl:call-template name="contributors-element">
        <xsl:with-param name="contributors" select="./crossref:query/crossref:contributors"/>
      </xsl:call-template>
    </xsl:if>
    <xsl:if test="./crossref:query/crossref:article_title">
      <xsl:call-template name="article_title">
        <xsl:with-param name="title" select="./crossref:query/crossref:article_title"/>
      </xsl:call-template>
    </xsl:if>
    <!-- Adding 980__$aHEP field to every record -->
    <datafield tag="980" ind1=" " ind2=" ">
      <subfield code="a"><xsl:text>HEP</xsl:text></subfield>
    </datafield>
  </xsl:template>
</xsl:stylesheet>