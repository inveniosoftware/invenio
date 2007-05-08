<?xml version="1.0" encoding="ISO-8859-1"?>
<!-- $Id$

     This file is part of CDS Invenio.
     Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.

     CDS Invenio is free software; you can redistribute it and/or
     modify it under the terms of the GNU General Public License as
     published by the Free Software Foundation; either version 2 of the
     License, or (at your option) any later version.

     CDS Invenio is distributed in the hope that it will be useful, but
     WITHOUT ANY WARRANTY; without even the implied warranty of
     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
     General Public License for more details.

     You should have received a copy of the GNU General Public License
     along with CDS Invenio; if not, write to the Free Software Foundation, Inc.,
     59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
-->


<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:OAI-PMH="http://www.openarchives.org/OAI/2.0/"
                xmlns:arXiv="http://arxiv.org/OAI/arXiv/"
                exclude-result-prefixes="OAI-PMH arXiv"
                version="1.0">
<xsl:output method="xml" encoding="UTF-8"/>



<!-- ************ FUNCTIONS ************ -->

 <!-- FUNCTION  replace-string -->
 <xsl:template name="replace-string">
    <xsl:param name="text"/>
    <xsl:param name="from"/>
    <xsl:param name="to"/>
    <xsl:choose>
      <xsl:when test="contains($text, $from)">
        <xsl:variable name="before" select="substring-before($text, $from)"/>
        <xsl:variable name="after" select="substring-after($text, $from)"/>
        <xsl:variable name="prefix" select="concat($before, $to)"/>

        <xsl:value-of select="$before"/>
        <xsl:value-of select="$to"/>
        <xsl:call-template name="replace-string">
          <xsl:with-param name="text" select="$after"/>
          <xsl:with-param name="from" select="$from"/>
          <xsl:with-param name="to" select="$to"/>
        </xsl:call-template>
      </xsl:when>
      <xsl:otherwise>
        <xsl:value-of select="$text"/>
      </xsl:otherwise>
    </xsl:choose>
 </xsl:template>


<!-- FUNCTION   output-695a-subfields -->
<xsl:template name="output-695a-subfields">
      <xsl:param name="list" />
      <xsl:variable name="newlist" select="concat(normalize-space($list), ' ')" />
      <xsl:variable name="first" select="substring-before($newlist, ' ')" />
      <xsl:variable name="remaining" select="substring-after($newlist, ' ')" />
      <xsl:if test="not($first='')">
         <datafield tag="695" ind1=" " ind2=" ">
           <subfield code="a"><xsl:value-of select="$first" /></subfield>
           <subfield code="9">LANL EDS</subfield>
         </datafield>
      </xsl:if>
      <xsl:if test="$remaining">
          <xsl:call-template name="output-695a-subfields">
              <xsl:with-param name="list" select="$remaining" />
          </xsl:call-template>
      </xsl:if>
</xsl:template>


<!-- FUNCTION   output-65017a-subfields -->
<xsl:template name="output-65017a-subfields">
      <xsl:param name="list" />
      <xsl:variable name="newlist" select="concat(normalize-space($list), ' ')" />
      <xsl:variable name="first" select="substring-before($newlist, ' ')" />
      <xsl:variable name="remaining" select="substring-after($newlist, ' ')" />
      <xsl:if test="not($first='')">
         <datafield tag="650" ind1="1" ind2="7">
           <subfield code="a"><xsl:value-of select="$first" /></subfield>
           <subfield code="2">arXiv</subfield>
         </datafield>
      </xsl:if>
      <xsl:if test="$remaining">
          <xsl:call-template name="output-65027a-subfields">
              <xsl:with-param name="list" select="$remaining" />
          </xsl:call-template>
      </xsl:if>
</xsl:template>


<!-- FUNCTION   output-65027a-subfields -->
<xsl:template name="output-65027a-subfields">
      <xsl:param name="list" />
      <xsl:variable name="newlist" select="concat(normalize-space($list), ' ')" />
      <xsl:variable name="first" select="substring-before($newlist, ' ')" />
      <xsl:variable name="remaining" select="substring-after($newlist, ' ')" />
      <xsl:if test="not($first='')">
         <datafield tag="650" ind1="2" ind2="7">
           <subfield code="a"><xsl:value-of select="$first" /></subfield>
           <subfield code="2">arXiv</subfield>
         </datafield>
      </xsl:if>
      <xsl:if test="$remaining">
          <xsl:call-template name="output-65027a-subfields">
              <xsl:with-param name="list" select="$remaining" />
          </xsl:call-template>
      </xsl:if>
</xsl:template>



 <!-- FUNCTION  last-word : returns last word of a string of words separated by spaces -->
 <xsl:template name="last-word">
    <xsl:param name="text"/>
    <xsl:choose>
      <xsl:when test="contains(normalize-space($text), ' ')">
        <xsl:variable name="after" select="substring-after( normalize-space($text), ' ') "/>
        <xsl:call-template name="last-word">
          <xsl:with-param name="text" select="$after"/>
        </xsl:call-template>
      </xsl:when>
      <xsl:otherwise>
        <xsl:value-of select="$text"/>
      </xsl:otherwise>
    </xsl:choose>
 </xsl:template>


 <!-- FUNCTION  matchPR773p -->
 <xsl:template name="matchPR773p">
    <xsl:param name="detectPR"/>
    <xsl:param name="commentsf"/>
    <xsl:choose>
      <xsl:when test="contains(normalize-space($detectPR), '@')">
        <xsl:variable name="after" select="substring-after( normalize-space($detectPR), '@') "/>
        <xsl:variable name="todetect" select="substring-before( normalize-space($detectPR), '@') "/>
        <xsl:call-template name="matchPR773pSUB">
          <xsl:with-param name="todetect" select="$todetect"/>
	  <xsl:with-param name="commentsf" select="$commentsf"/>
        </xsl:call-template>
        <xsl:call-template name="matchPR773p">
          <xsl:with-param name="detectPR" select="$after"/>
          <xsl:with-param name="commentsf" select="$commentsf"/> 
        </xsl:call-template>
      </xsl:when>
    </xsl:choose>
 </xsl:template>

<!--
      <xsl:otherwise>
        <xsl:variable name="todetect" select="substring-before( normalize-space($detectPR), '@') "/>
        <xsl:call-template name="matchPR773pSUB">
	  <xsl:with-param name="commentsf" select="$commentsf"/>
          <xsl:with-param name="todetect" select="$todetect"/>
        </xsl:call-template>
      </xsl:otherwise>
    </xsl:choose>
 </xsl:template>

-->


 <!-- FUNCTION  matchPR773pSUB called by mathPR773p  -->
 <xsl:template name="matchPR773pSUB">
    <xsl:param name="todetect"/>
    <xsl:param name="commentsf"/>
    <xsl:if test="contains($commentsf, $todetect)">
       <datafield tag="773" ind1=" " ind2=" ">
          <subfield code="p"><xsl:value-of select="normalize-space(substring-after($commentsf, $todetect))"/></subfield>
       </datafield>
    </xsl:if>
 </xsl:template>


 <!-- FUNCTION  rn-extract : returns a subfield for each reportnumber in a string (comma separted)  -->
 <xsl:template name="rn-extract">
    <xsl:param name="text"/>
    <xsl:choose>
      <xsl:when test="contains(normalize-space($text), ',')">
        <xsl:variable name="after" select="substring-after( normalize-space($text), ',')"/>
        <datafield tag="088" ind1=" " ind2=" ">
           <subfield code="a"><xsl:value-of select="substring-before( normalize-space($text), ',')"/></subfield>
        </datafield>
        <xsl:call-template name="rn-extract">
          <xsl:with-param name="text" select="$after"/>
        </xsl:call-template>
      </xsl:when>
      <xsl:otherwise>
        <datafield tag="088" ind1=" " ind2=" ">
          <subfield code="a"><xsl:value-of select="$text"/></subfield>
        </datafield>
      </xsl:otherwise>
    </xsl:choose>
 </xsl:template>


 <!-- FUNCTION cern-detect : returns the appropriatate 690C subfield if it is a CERN parper and nothing otherwise -->
 <xsl:template name="cern-detect">
    <xsl:param name="reportnumber"/>
    <xsl:choose>
      <xsl:when test="contains($reportnumber, 'CERN')">
         <datafield tag="690" ind1="C" ind2=" ">
           <subfield code="a">CERN</subfield>
         </datafield>
     </xsl:when>
      <xsl:otherwise><xsl:call-template name="cern-detect-aff"/></xsl:otherwise>
    </xsl:choose>
 </xsl:template>

 <!-- FUNCTION Print sets values separated by ;  -->
 <xsl:template name="print-sets">
    <xsl:for-each select="./OAI-PMH:header/OAI-PMH:setSpec"><xsl:value-of select="."/>;</xsl:for-each>
 </xsl:template>


 <!-- FUNCTION cern-detect-aff : used by cern-detect : detects if the srting  CERN is present in affiaitons  -->
 <xsl:template name="cern-detect-aff">
 <xsl:for-each select="./OAI-PMH:metadata/arXiv:arXiv/arXiv:authors/arXiv:author">
   <!-- <xsl:if test="./arXiv:affiliation"/> -->
      <xsl:if test="contains(./arXiv:affiliation, 'CERN') or contains(./arXiv:affiliation, 'cern') ">
         <datafield tag="690" ind1="C" ind2=" ">
          <subfield code="a">CERN</subfield>
         </datafield>
      </xsl:if>
    <!-- </xsl:if>  -->
 </xsl:for-each>
 </xsl:template>


 <!-- FUNCTION cern-detect9 : returns the appropriatate 690C subfield if it is a CERN parper and nothing otherwise -->
 <xsl:template name="cern-detect9">
    <xsl:param name="reportnumber"/>
    <xsl:choose>
      <xsl:when test="contains($reportnumber, 'CERN')">
         <datafield tag="980" ind1=" " ind2=" ">
           <subfield code="a">CERN</subfield>
         </datafield>
     </xsl:when>
      <xsl:otherwise><xsl:call-template name="cern-detect-aff9"/></xsl:otherwise>
    </xsl:choose>
 </xsl:template>


 <!-- FUNCTION cern-detect-aff9 : used by cern-detect : detects if the srting  CERN is present in affiaitons  -->
 <xsl:template name="cern-detect-aff9">
 <xsl:for-each select="./OAI-PMH:metadata/arXiv:arXiv/arXiv:authors/arXiv:author">
   <!-- <xsl:if test="./arXiv:affiliation"/> -->
      <xsl:if test="contains(./arXiv:affiliation, 'CERN') or contains(./arXiv:affiliation, 'cern') ">
         <datafield tag="980" ind1=" " ind2=" ">
          <subfield code="a">CERN</subfield>
         </datafield>
      </xsl:if>
    <!-- </xsl:if>  -->
 </xsl:for-each>
 </xsl:template>



 <!-- FUNCTION  reformat-date : from 3 params (YYYY,MM,DD)  to "DD Mmm YYYY" -->
 <xsl:template name="reformat-date">
    <xsl:param name="year"/>
    <xsl:param name="month"/>
    <xsl:param name="day"/>
    <xsl:choose>
      <xsl:when test="$month='01'">
         <xsl:value-of select="concat($day,' Jan ',$year)"/>
      </xsl:when>
      <xsl:when test="$month='02'">
         <xsl:value-of select="concat($day,' Feb ',$year)"/>
      </xsl:when>
      <xsl:when test="$month='03'">
         <xsl:value-of select="concat($day,' Mar ',$year)"/>
      </xsl:when>
      <xsl:when test="$month='04'">
         <xsl:value-of select="concat($day,' Apr ',$year)"/>
      </xsl:when>
      <xsl:when test="$month='05'">
         <xsl:value-of select="concat($day,' May ',$year)"/>
      </xsl:when>
      <xsl:when test="$month='06'">
         <xsl:value-of select="concat($day,' Jun ',$year)"/>
      </xsl:when>
      <xsl:when test="$month='07'">
         <xsl:value-of select="concat($day,' Jul ',$year)"/>
      </xsl:when>
      <xsl:when test="$month='08'">
         <xsl:value-of select="concat($day,' Aug ',$year)"/>
      </xsl:when>
      <xsl:when test="$month='09'">
         <xsl:value-of select="concat($day,' Sep ',$year)"/>
      </xsl:when>
      <xsl:when test="$month='10'">
         <xsl:value-of select="concat($day,' Oct ',$year)"/>
      </xsl:when>
      <xsl:when test="$month='11'">
         <xsl:value-of select="concat($day,' Nov ',$year)"/>
      </xsl:when>
      <xsl:when test="$month='12'">
         <xsl:value-of select="concat($day,' Dec ',$year)"/>
      </xsl:when>
    </xsl:choose>
 </xsl:template>



<!-- ************ MAIN CODE ************ -->

<xsl:template match="/">




  <collection>
  <xsl:for-each select="//OAI-PMH:record">


  <!-- *** GLOBAL RECORD VARS *** -->

  <!-- Preparing base determination : getting cathegory -->
  <xsl:variable name="setspec2">
    <xsl:value-of select="substring-after(./OAI-PMH:header/OAI-PMH:setSpec,':')"/>
  </xsl:variable>

  <!-- Preparing data : is this a thesis ? (we can find this in the abstract)-->
  <xsl:variable name="lcletters">abcdefghijklmnopqrstuvwxyz</xsl:variable>
  <xsl:variable name="ucletters">ABCDEFGHIJKLMNOPQRSTUVWXYZ</xsl:variable>
  <xsl:variable name="abstractlow">
    <xsl:value-of select="translate(./OAI-PMH:metadata/arXiv:arXiv/arXiv:abstract,$ucletters,$lcletters)"/>
  </xsl:variable>
 
  <xsl:variable name="detectPR">accepted@appear@press@publ@review@submitted"></xsl:variable>

  <!-- *** END GLOBAL RECIRD VARS *** -->



    <!-- KEEPING ONLY RECORDS THAT ARE USEFULL FOR CERN -->
    <xsl:variable name="setspec">
      <xsl:value-of select="substring-after(./OAI-PMH:header/OAI-PMH:setSpec,':')"/>
    </xsl:variable>


    <xsl:variable name="allsets">
      <xsl:call-template name="print-sets" />
    </xsl:variable>

   <!--  <xsl:if test=" contains($allsets,'solv-int') or contains($allsets,'quant-ph') or contains($allsets,'q-alg') or contains($allsets,'plasm-ph') or contains($allsets,'physics') or contains($allsets,'patt-sol') or contains($allsets,'nucl-th') or contains($allsets,'nucl-ex') or contains($allsets,'nlin') or contains($allsets,'neuro-sci') or contains($allsets,'neuro-dev') or contains($allsets,'neuro-cel') or contains($allsets,'mtrl-th') or contains($allsets,'math') or contains($allsets,'math-ph') or contains($allsets,'lc-om') or contains($allsets,'hep-th') or contains($allsets,'hep-ph') or contains($allsets,'hep-lat') or contains($allsets,'hep-ex') or contains($allsets,'gr-qc') or contains($allsets,'funct-an') or contains($allsets,'dg-ga') or contains($allsets,'cs') or contains($allsets,'cond-mat') or contains($allsets,'comp-gas') or contains($allsets,'cmp-lg') or contains($allsets,'chem-ph') or contains($allsets,'chao-dyn') or contains($allsets,'cd-hg') or contains($allsets,'bayes-an') or contains($allsets,'auto-fms') or contains($allsets,'atom-ph') or contains($allsets,'astro-ph') or contains($allsets,'ao-sci') or contains($allsets,'alg-geom') or contains($allsets,'adap-org') or contains($allsets,'acc-phys')  "> -->

     <xsl:if test=" contains($allsets, 'quant-ph') or contains($allsets,'q-alg') or contains($allsets,'plasm-ph') or contains($allsets,'physics') or contains($allsets,'nucl-th') or contains($allsets,'nucl-ex') or contains($allsets,'math') or contains($allsets,'math-ph') or contains($allsets,'hep-th') or contains($allsets,'hep-ph') or contains($allsets,'hep-lat') or contains($allsets,'hep-ex') or contains($allsets,'gr-qc') or contains($allsets,'cs') or contains($allsets,'astro-ph') or contains($allsets,'acc-phys')  ">

    <xsl:choose>
       <!-- HANDLING DELETED RECORDS -->
       <xsl:when test="OAI-PMH:header[@status='deleted']">
         <record>
         <xsl:if test="./OAI-PMH:header/OAI-PMH:identifier | ./OAI-PMH:header/OAI-PMH:setSpec">
           <datafield tag="909" ind1="C" ind2="O">
             <subfield code="o"><xsl:value-of select="./OAI-PMH:header/OAI-PMH:identifier"/></subfield>
             <subfield code="p"><xsl:value-of select="./OAI-PMH:header/OAI-PMH:setSpec"/></subfield>
           </datafield>
         </xsl:if>
           <datafield tag="980" ind1="" ind2="">
             <subfield code="c">DELETED</subfield>
             </datafield>
         </record>
       </xsl:when>



       <!-- HANDLING NON-DELETED RECORDS -->
       <xsl:otherwise>
         <record>

           <!-- Field FFT :  url for future bibupload fultext importation : FIXME: add other sets
           <xsl:if test=" ($setspec ='quant-ph') or ($setspec ='physics') or ($setspec ='q-alg') or ($setspec ='nucl-th') or ($setspec ='nucl-ex') or ($setspec ='hep-th') or ($setspec ='hep-ph') or ($setspec ='hep-lat') or ($setspec ='hep-ex')  or ($setspec ='chao-dyn') or ($setspec ='gr-qc')  or ($setspec ='astro-ph') ">

           <xsl:if test="./OAI-PMH:metadata/arXiv:arXiv/arXiv:id">
             <datafield tag="FFT" ind1=" " ind2=" "><subfield code="a">http://export.arxiv.org/pdf/<xsl:value-of select="./OAI-PMH:metadata/arXiv:arXiv/arXiv:id"/>.pdf</subfield></datafield>
           </xsl:if>
           </xsl:if>  -->



           <!-- MARC FIELD 003  -->
             <controlfield tag="003">SzGeCERN</controlfield>


           <!-- MARC FIELD 034_$$9,a  = metadata/header/identifier  -->
           <xsl:if test="./OAI-PMH:header/OAI-PMH:identifier">
             <datafield tag="035" ind1=" " ind2=" ">
                <subfield code="9">arXiv</subfield>
                <subfield code="a"><xsl:value-of select="./OAI-PMH:header/OAI-PMH:identifier"/></subfield>
             </datafield>
           </xsl:if>


           <!-- MARC FIELD 037$$a = metadata/arXiv/id
           <xsl:if test="./OAI-PMH:metadata/arXiv:arXiv/arXiv:id">
             <datafield tag="037" ind1=" " ind2=" ">
                <subfield code="a"><xsl:value-of select="./OAI-PMH:metadata/arXiv:arXiv/arXiv:id"/></subfield>
             </datafield>
           </xsl:if> -->


           <!-- MARC FIELD 037_$$a = metadata/header/identifier  -->
           <xsl:if test="./OAI-PMH:header/OAI-PMH:identifier">
             <datafield tag="037" ind1=" " ind2=" ">
                <subfield code="a">
                  <xsl:call-template name="replace-string">
                    <xsl:with-param name="text" select="substring-after(./OAI-PMH:header/OAI-PMH:identifier, ':')"/>
                    <xsl:with-param name="from" select="'arXiv.org'"/>
                    <xsl:with-param name="to" select="'arXiv'"/>
                  </xsl:call-template>
                </subfield>
             </datafield>
           </xsl:if>


           <!-- MARC FIELD 041$$a = default value: eng for english  -->
           <datafield tag="041" ind1=" " ind2=" ">
                <subfield code="a">eng</subfield>
           </datafield>




           <!-- MARC FIELD 088$$a = metadata/arXiv/report-no   -->
           <xsl:if test="./OAI-PMH:metadata/arXiv:arXiv/arXiv:report-no">
             <xsl:variable name="RN0">
               <xsl:value-of select="translate(./OAI-PMH:metadata/arXiv:arXiv/arXiv:report-no, $lcletters, $ucletters)"/>
             </xsl:variable>
             <xsl:variable name="RN1">
               <xsl:call-template name="replace-string"><xsl:with-param name="text" select="$RN0"/><xsl:with-param name="from" select="'/'"/><xsl:with-param name="to" select="'-'"/></xsl:call-template>
             </xsl:variable>
             <xsl:variable name="RN2">
               <xsl:call-template name="replace-string"><xsl:with-param name="text" select="$RN1"/><xsl:with-param name="from" select="';'"/><xsl:with-param name="to" select="','"/></xsl:call-template>
             </xsl:variable>
             <xsl:variable name="RN3">
               <xsl:call-template name="replace-string"><xsl:with-param name="text" select="$RN2"/><xsl:with-param name="from" select="', '"/><xsl:with-param name="to" select="','"/></xsl:call-template>
             </xsl:variable>
               <xsl:call-template name="rn-extract"><xsl:with-param name="text" select="$RN3"/></xsl:call-template>
           </xsl:if>




           <!-- MARC FIELDS [1,7]00$$a,u and 710  = metadata/arXiv/[author,affiliation]
                N.B.: $$v not used, all affiliations are repeated in $$u   -->
           <xsl:if test="./OAI-PMH:metadata/arXiv:arXiv/arXiv:authors/arXiv:author">

             <!-- Filling 710$$g   substring(chaîne,position,longueur)  -->
                <xsl:for-each select="./OAI-PMH:metadata/arXiv:arXiv/arXiv:authors/arXiv:author[1]/arXiv:affiliation">
                  <xsl:if test="contains( translate(., $lcletters, $ucletters), 'collaboration')">
                      <datafield tag="710" ind1=" " ind2=" ">
                       <subfield code="g"><xsl:value-of select="."/></subfield>
                     </datafield>
                  </xsl:if>
                </xsl:for-each>


             <!-- Filling 100$$a,u   substring(chaîne,position,longueur)  -->
             <datafield tag="100" ind1=" " ind2=" ">
                <subfield code="a">
                  <xsl:variable name="fnames">
                    <xsl:value-of select="normalize-space(./OAI-PMH:metadata/arXiv:arXiv/arXiv:authors/arXiv:author/arXiv:forenames)"/>
                  </xsl:variable>
                  <xsl:value-of select="./OAI-PMH:metadata/arXiv:arXiv/arXiv:authors/arXiv:author/arXiv:keyname"/>, <xsl:call-template name="replace-string"><xsl:with-param name="text" select="$fnames"/><xsl:with-param name="from" select="'.'"/><xsl:with-param name="to" select="''"/></xsl:call-template>
                </subfield>
                <xsl:for-each select="./OAI-PMH:metadata/arXiv:arXiv/arXiv:authors/arXiv:author[1]/arXiv:affiliation">
                  <subfield code="u"><xsl:value-of select="."/></subfield>
                </xsl:for-each>
             </datafield>



             <!-- Filling 700$$a,u -->
             <xsl:for-each select="./OAI-PMH:metadata/arXiv:arXiv/arXiv:authors/arXiv:author[position()>1]">
               <datafield tag="700" ind1=" " ind2=" ">
                <!-- Old way without reformating to initials
                <subfield code="a">
                  <xsl:value-of select="./arXiv:keyname"/>, <xsl:value-of select="./arXiv:forenames"/>
                </subfield>
                -->
                <subfield code="a">
                  <xsl:variable name="fnames">
                    <xsl:value-of select="normalize-space(./arXiv:forenames)"/>
                  </xsl:variable>
                  <xsl:value-of select="./arXiv:keyname"/>, <xsl:call-template name="replace-string"><xsl:with-param name="text" select="$fnames"/><xsl:with-param name="from" select="'.'"/><xsl:with-param name="to" select="''"/></xsl:call-template>
                </subfield>
                <xsl:for-each select="./arXiv:affiliation">
                  <subfield code="u"><xsl:value-of select="."/></subfield>
                </xsl:for-each>
               </datafield>
             </xsl:for-each>


             <!-- Filling 710$$g - collaboration detection in affiliation field  -->
             <xsl:variable name="knlow"><xsl:value-of select="normalize-space(translate(./OAI-PMH:metadata/arXiv:arXiv/arXiv:authors/arXiv:author[1]/arXiv:affiliation, $ucletters, $lcletters))"/></xsl:variable>
             <xsl:if test="contains($knlow,'collab') or contains($knlow,'team') or contains($knlow,'group') ">
               <datafield tag="710" ind1=" " ind2=" ">
                 <subfield code="g"><xsl:value-of select="concat(translate(./OAI-PMH:metadata/arXiv:arXiv/arXiv:authors/arXiv:author[1]/arXiv:forenames, $lcletters, $ucletters), ' ', ./OAI-PMH:metadata/arXiv:arXiv/arXiv:authors/arXiv:author[1]/arXiv:affiliation)"/> </subfield>
               </datafield>
             </xsl:if>
             </xsl:if>


           <!-- MARC FIELD 8564   <subfield code="y">Access to fulltext document</subfield> -->
           <xsl:if test="./OAI-PMH:metadata/arXiv:arXiv/arXiv:id">
             <datafield tag="856" ind1="4" ind2=" ">
                  <subfield code="u">http://arxiv.org/pdf/<xsl:value-of select="substring-after(./OAI-PMH:header/OAI-PMH:identifier, '.org:')"/>.pdf</subfield>
             </datafield>
           </xsl:if>


             <!-- Filling 962$$b  LKR$$b - conference detection in comments field  -->
             <xsl:if test="./OAI-PMH:metadata/arXiv:arXiv/arXiv:comments">
             <xsl:variable name="lkrmatch"><xsl:value-of select="normalize-space(translate(./OAI-PMH:metadata/arXiv:arXiv/arXiv:comments, $ucletters, $lcletters))"/></xsl:variable>
             <xsl:if test="contains($lkrmatch,'conf') or contains($lkrmatch,'talk') or contains($lkrmatch,'seminar') or contains($lkrmatch,'lecture')  or contains($lkrmatch,'contrib')  or contains($lkrmatch,'forum')  or contains($lkrmatch,'seminar') or contains($lkrmatch,'meeting') or contains($lkrmatch,'symp')or contains($lkrmatch,'rencontre') or contains($lkrmatch,'proc') or contains($lkrmatch,'workshop')   ">
               <datafield tag="962" ind1=" " ind2=" ">
                 <subfield code="b"><xsl:value-of select="normalize-space(./OAI-PMH:metadata/arXiv:arXiv/arXiv:comments)"/> </subfield>
               </datafield>
             </xsl:if>
             </xsl:if>


             <!-- Filling 773$$p  - publication detection in comments field -->
             <xsl:if test="./OAI-PMH:metadata/arXiv:arXiv/arXiv:comments">
	       <xsl:variable name="commentsf">
	         <xsl:value-of select="translate(./OAI-PMH:metadata/arXiv:arXiv/arXiv:comments,$ucletters,$lcletters)"/>
	       </xsl:variable>
             <xsl:call-template name="matchPR773p"><xsl:with-param name="detectPR" select="$detectPR"/><xsl:with-param name="commentsf" select="$commentsf"/></xsl:call-template>
             </xsl:if>


           <!-- MARC FIELD 245$$a  -->
           <xsl:if test="./OAI-PMH:metadata/arXiv:arXiv/arXiv:title">
             <datafield tag="245" ind1=" " ind2=" ">
               <subfield code="a"><xsl:value-of select="normalize-space(./OAI-PMH:metadata/arXiv:arXiv/arXiv:title)"/></subfield>
             </datafield>
           </xsl:if>


           <!-- MARC FIELD  269$$c / date  -->
           <!-- RE-MARC FIELD Same treatement for all bases, subfileds a and b addeb by babbage.py later  -->
           <xsl:if test="./OAI-PMH:header/OAI-PMH:datestamp">
             <xsl:variable name="datebase" select="./OAI-PMH:header/OAI-PMH:datestamp"/>
             <xsl:variable name="year" select="substring-before($datebase,'-')"/>
             <xsl:variable name="month" select="substring-before(substring-after($datebase,'-'),'-')"/>
             <xsl:variable name="day" select="substring-after(substring-after($datebase,'-'),'-')"/>

             <datafield tag="269" ind1=" " ind2=" ">
                <subfield code="c">
                  <xsl:call-template name="reformat-date"><xsl:with-param name="year" select="$year"/><xsl:with-param name="month" select="$month"/><xsl:with-param name="day" select="$day"/></xsl:call-template>
                </subfield>
             </datafield>
           </xsl:if>


           <!-- MARC FIELD 300$$a / pagination -->
               <xsl:if test="./OAI-PMH:metadata/arXiv:arXiv/arXiv:comments">
               <xsl:choose>
               <xsl:when test="contains(./OAI-PMH:metadata/arXiv:arXiv/arXiv:comments, 'pages')">
                 <xsl:variable name="beforepages">
                   <xsl:value-of select="normalize-space(substring-before(./OAI-PMH:metadata/arXiv:arXiv/arXiv:comments,'pages'))"/>
                 </xsl:variable>
                 <datafield tag="300" ind1=" " ind2=" ">
                   <subfield code="a"><xsl:call-template name="last-word"><xsl:with-param name="text" select="$beforepages"/></xsl:call-template> p</subfield>
                 </datafield>
               </xsl:when>
               <xsl:otherwise>
                 <datafield tag="300" ind1=" " ind2=" ">
                   <subfield code="a">mult. p</subfield>
                 </datafield>
               </xsl:otherwise>
               </xsl:choose>
               </xsl:if>


           <!-- MARC FIELD 520$$a  -->
           <xsl:if test="./OAI-PMH:metadata/arXiv:arXiv/arXiv:abstract">
             <datafield tag="520" ind1=" " ind2=" ">
                <subfield code="a">
                   <xsl:value-of select="normalize-space(./OAI-PMH:metadata/arXiv:arXiv/arXiv:abstract)"/>
                </subfield>
             </datafield>
           </xsl:if>


           <!-- MARC FIELD 500$$a -->
           <xsl:if test="./OAI-PMH:metadata/arXiv:arXiv/arXiv:comments">
              <datafield tag="500" ind1=" " ind2=" ">
                <subfield code="a">Comments: <xsl:value-of select="normalize-space(./OAI-PMH:metadata/arXiv:arXiv/arXiv:comments)"/></subfield>
              </datafield>
           </xsl:if>


           <!-- MARC FIELD 65017$$ab -->
           <xsl:if test="./OAI-PMH:metadata/arXiv:arXiv/arXiv:categories">
                <xsl:call-template name="output-65017a-subfields">
                    <xsl:with-param name="list"><xsl:value-of select="./OAI-PMH:metadata/arXiv:arXiv/arXiv:categories"/></xsl:with-param>
                </xsl:call-template>
           </xsl:if>


           <!-- MARC FIELD 695$$a -->
           <xsl:if test="./OAI-PMH:metadata/arXiv:arXiv/arXiv:categories">
                <xsl:call-template name="output-695a-subfields">
                    <xsl:with-param name="list"><xsl:value-of select="./OAI-PMH:metadata/arXiv:arXiv/arXiv:categories"/></xsl:with-param>
                </xsl:call-template>
           </xsl:if>


           <!-- MARC FIELD 773 -->
           <xsl:if test="./OAI-PMH:metadata/arXiv:arXiv/arXiv:journal-ref">

             <!-- typically something like: A)  Phys. Rev. B 58, 10648 (1998)
                                        or:  B)  Astron.J. 133 (2007) 1236-1242-->

             <xsl:variable name="jref">
               <xsl:value-of select="./OAI-PMH:metadata/arXiv:arXiv/arXiv:journal-ref"/>
             </xsl:variable>

             <xsl:choose>
               <xsl:when test="contains($jref,',')"> <!-- case A -->

               <xsl:variable name="jref-beforecoma">
                 <xsl:value-of select="normalize-space(substring-before($jref,','))"/>
               </xsl:variable>

               <xsl:variable name="jref-volume">
                 <xsl:call-template name="last-word"><xsl:with-param name="text" select="$jref-beforecoma"/></xsl:call-template>
               </xsl:variable>

               <xsl:variable name="jref-title">
                 <xsl:value-of select="normalize-space(substring-before($jref-beforecoma,$jref-volume))"/>
               </xsl:variable>

               <xsl:variable name="jref-title2">
                  <xsl:call-template name="replace-string"><xsl:with-param name="text" select="$jref-title"/><xsl:with-param name="from" select="'.'"/><xsl:with-param name="to" select="'. '"/></xsl:call-template>
               </xsl:variable>

               <xsl:variable name="jref-aftercoma">
                 <xsl:value-of select="normalize-space(substring-after($jref,','))"/>
               </xsl:variable>

               <xsl:variable name="jref-year">
                 <xsl:value-of select="normalize-space(substring-before(substring-after($jref,'('),')'))"/>
               </xsl:variable>

               <xsl:variable name="jref-pages-base">
                 <xsl:value-of select="normalize-space(substring-before($jref-aftercoma,'('))"/>
               </xsl:variable>

                   <xsl:variable name="jref-pages">
                     <xsl:value-of select="normalize-space($jref-pages-base)"/>
                   </xsl:variable>


               <datafield tag="773" ind1=" " ind2=" ">
                  <subfield code="p"><xsl:value-of select="normalize-space($jref-title2)"/></subfield>
                  <subfield code="v"><xsl:value-of select="$jref-volume"/></subfield>
                  <subfield code="y"><xsl:value-of select="$jref-year"/></subfield>
                  <subfield code="c"><xsl:value-of select="$jref-pages-base"/></subfield>
               </datafield>

               <datafield tag="260" ind1=" " ind2=" ">
                   <subfield code="c"><xsl:value-of select="$jref-year"/></subfield>
                </datafield>


             </xsl:when>
             <xsl:otherwise> <!-- case B -->
               <xsl:variable name="jref-beforedate">
                 <xsl:value-of select="normalize-space(substring-before($jref,'('))"/>
               </xsl:variable>

               <xsl:variable name="jref-volume-pre">
                 <xsl:call-template name="last-word"><xsl:with-param name="text" select="$jref-beforedate"/></xsl:call-template>
               </xsl:variable>


               <xsl:choose>
                 <xsl:when test="string(number($jref-beforedate)) = 'NaN'">
                  <xsl:variable name="jref-volume">
                    <xsl:value-of select="substring($jref-volume-pre, 2)"/>
                  </xsl:variable>
                 </xsl:when>
                 <xsl:otherwise>
                  <xsl:variable name="jref-volume">
                    <xsl:value-of select="$jref-volume-pre"/>
                  </xsl:variable>
                 </xsl:otherwise>
               </xsl:choose>



               <xsl:variable name="jref-volume">
                 <xsl:value-of select="substring($jref-volume-pre, 2)"/>
               </xsl:variable>


               <xsl:variable name="jref-title">
                 <xsl:value-of select="normalize-space(substring-before($jref-beforedate,$jref-volume))"/>
               </xsl:variable>

               <xsl:variable name="jref-title2">
                  <xsl:call-template name="replace-string"><xsl:with-param name="text" select="$jref-title"/><xsl:with-param name="from" select="'.'"/><xsl:with-param name="to" select="'. '"/></xsl:call-template>
               </xsl:variable>

               <xsl:variable name="jref-pages">
                 <xsl:value-of select="normalize-space(substring-after($jref,')'))"/>
               </xsl:variable>

               <xsl:variable name="jref-year">
                 <xsl:value-of select="substring-after( substring-before($jref,')') , '(' )"/>
               </xsl:variable>

               <datafield tag="773" ind1=" " ind2=" ">
                  <subfield code="p"><xsl:value-of select="normalize-space($jref-title2)"/></subfield>
                  <subfield code="v"><xsl:value-of select="$jref-volume"/></subfield>
                  <subfield code="y"><xsl:value-of select="$jref-year"/></subfield>
                  <subfield code="c"><xsl:value-of select="$jref-pages"/></subfield>
               </datafield>

               <datafield tag="260" ind1=" " ind2=" ">
                   <subfield code="c"><xsl:value-of select="$jref-year"/></subfield>
                </datafield>

             </xsl:otherwise>
           </xsl:choose>


           </xsl:if>



           <!-- MARC FIELDS which are treated differently according to the base  -->
           <!-- MARC FIELDS 269$$[b,a,c], 300$$a , V 500$$a,  502$$[a,b,c] , V 595$$a, V 690$$c, V 960$$a, V 980$$a -->
           <!-- RE-MARC :-) FIELD 962 (LKR) is genrated via FFT tag by bibupload  -->
           <!-- Base: 10=hep related topics , 11=hep topics , 13=published articles, 14=theses  -->



           <!-- Now determinig base -->
           <xsl:choose>


             <!-- Base 13 specific treatment -->
             <xsl:when test="./OAI-PMH:metadata/arXiv:arXiv/arXiv:journal-ref">

                   <!-- MARC FIELDS 690C$$a and 980$$a NB: 980$$a enables searching  -->
                   <datafield tag="690" ind1="C" ind2=" ">
                     <subfield code="a">ARTICLE</subfield>
                   </datafield>

                   <xsl:call-template name="cern-detect"><xsl:with-param name="reportnumber" select="./OAI-PMH:metadata/arXiv:arXiv/arXiv:report-no"/></xsl:call-template>

                   <datafield tag="980" ind1=" " ind2=" ">
                     <subfield code="a">ARTICLE</subfield>
                   </datafield>
                   <xsl:call-template name="cern-detect9"><xsl:with-param name="reportnumber" select="./OAI-PMH:metadata/arXiv:arXiv/arXiv:report-no"/></xsl:call-template>
                   <!-- MARC FIELD 960$$a the base field  -->
                   <datafield tag="960" ind1=" " ind2=" ">
                       <subfield code="a">13</subfield>
                   </datafield>

             </xsl:when>

             <!-- Base 14 specific treatment -->
             <xsl:when test="contains($abstractlow,' thesis ') or contains($abstractlow,' dipl') or contains($abstractlow,' licence') or contains($abstractlow,' bachelor ' or contains($abstractlow,' phd '))">

                   <xsl:if test="./OAI-PMH:header/OAI-PMH:datestamp">
                     <xsl:variable name="datebase" select="./OAI-PMH:header/OAI-PMH:datestamp"/>
                     <xsl:variable name="year" select="substring-before($datebase,'-')"/>
                     <xsl:variable name="month" select="substring-before(substring-after($datebase,'-'),'-')"/>
                     <xsl:variable name="day" select="substring-after(substring-after($datebase,'-'),'-')"/>

                     <datafield tag="260" ind1=" " ind2=" ">
                       <subfield code="c"><xsl:value-of select="$year"/></subfield>
                     </datafield>
                   </xsl:if>

                   <!-- MARC FIELDS 502$$a  -->
                   <datafield tag="502" ind1=" " ind2=" ">
                     <subfield code="a">Thesis</subfield>
                   </datafield>

                   <!-- MARC FIELDS 690C$$a and 980$$a NB: 980$$a enables searching  -->
                   <datafield tag="690" ind1="C" ind2=" ">
                     <subfield code="a">THESIS</subfield>
                   </datafield>
                   <xsl:call-template name="cern-detect"><xsl:with-param name="reportnumber" select="./OAI-PMH:metadata/arXiv:arXiv/arXiv:report-no"/></xsl:call-template>

                   <datafield tag="980" ind1=" " ind2=" ">
                     <subfield code="a">THESIS</subfield>
                   </datafield>
                   <xsl:call-template name="cern-detect9"><xsl:with-param name="reportnumber" select="./OAI-PMH:metadata/arXiv:arXiv/arXiv:report-no"/></xsl:call-template>

                   <!-- MARC FIELD 960$$a the base field  -->
                   <datafield tag="960" ind1=" " ind2=" ">
                       <subfield code="a">14</subfield>
                   </datafield>

             </xsl:when>

             <!-- Otherwise we have to decide between bases 11 and 10 -->
             <xsl:otherwise>
               <xsl:choose>


                 <!-- Base 11 specific treatement -->
                 <xsl:when test=" ($setspec2 ='solv-int') or ($setspec2 ='quant-ph') or ($setspec2 ='q-alg') or ($setspec2 ='plasm-ph') or ($setspec2 ='physics') or ($setspec2 ='patt-sol') or ($setspec2 ='nucl-th') or ($setspec2 ='nucl-ex') or ($setspec2 ='hep-th') or ($setspec2 ='hep-ph') or ($setspec2 ='hep-lat') or ($setspec2 ='hep-ex') or ($setspec2 ='gr-qc') ">

                   <xsl:if test="./OAI-PMH:header/OAI-PMH:datestamp">
                     <xsl:variable name="datebase" select="./OAI-PMH:header/OAI-PMH:datestamp"/>
                     <xsl:variable name="year" select="substring-before($datebase,'-')"/>
                     <xsl:variable name="month" select="substring-before(substring-after($datebase,'-'),'-')"/>
                     <xsl:variable name="day" select="substring-after(substring-after($datebase,'-'),'-')"/>

                     <datafield tag="260" ind1=" " ind2=" ">
                       <subfield code="c"><xsl:value-of select="$year"/></subfield>
                     </datafield>
                   </xsl:if>

                   <!-- MARC FIELDS 690C$$a and 980$$a NB: 980$$a enables searching  -->
                   <datafield tag="690" ind1="C" ind2=" ">
                     <subfield code="a">PREPRINT</subfield>
                   </datafield>
                   <xsl:call-template name="cern-detect"><xsl:with-param name="reportnumber" select="translate(./OAI-PMH:metadata/arXiv:arXiv/arXiv:report-no, lcletters, ucletters)"/></xsl:call-template>

                   <datafield tag="980" ind1=" " ind2=" ">
                     <subfield code="a">PREPRINT</subfield>
                   </datafield>
                   <xsl:call-template name="cern-detect9"><xsl:with-param name="reportnumber" select="translate(./OAI-PMH:metadata/arXiv:arXiv/arXiv:report-no, lcletters, ucletters)"/></xsl:call-template>

                   <!-- MARC FIELD 960$$a the base field  -->
                   <datafield tag="960" ind1=" " ind2=" ">
                       <subfield code="a">11</subfield>
                   </datafield>

                 </xsl:when>

                 <!-- Base 10 specific treatement -->
                 <xsl:otherwise>

                   <xsl:if test="./OAI-PMH:header/OAI-PMH:datestamp">
                     <xsl:variable name="datebase" select="./OAI-PMH:header/OAI-PMH:datestamp"/>
                     <xsl:variable name="year" select="substring-before($datebase,'-')"/>
                     <xsl:variable name="month" select="substring-before(substring-after($datebase,'-'),'-')"/>
                     <xsl:variable name="day" select="substring-after(substring-after($datebase,'-'),'-')"/>

                     <datafield tag="260" ind1=" " ind2=" ">
                       <subfield code="c"><xsl:value-of select="$year"/></subfield>
                     </datafield>
                   </xsl:if>

                      <!-- MARC FIELDS 690C$$a and 980$$a NB: 980$$a enables searching  -->
                      <datafield tag="690" ind1="C" ind2=" ">
                        <subfield code="a">PREPRINT</subfield>
                      </datafield>
                      <xsl:call-template name="cern-detect"><xsl:with-param name="reportnumber" select="translate(./OAI-PMH:metadata/arXiv:arXiv/arXiv:report-no, lcletters, ucletters)"/></xsl:call-template>

                      <datafield tag="980" ind1=" " ind2=" ">
                        <subfield code="a">PREPRINT</subfield>
                      </datafield>
                      <xsl:call-template name="cern-detect9"><xsl:with-param name="reportnumber" select="translate(./OAI-PMH:metadata/arXiv:arXiv/arXiv:report-no, lcletters, ucletters)"/></xsl:call-template>

                      <!-- MARC FIELD 960$$a the base field  -->
                      <datafield tag="960" ind1=" " ind2=" ">
                         <subfield code="a">10</subfield>
                      </datafield>


                 </xsl:otherwise>


               </xsl:choose>
             </xsl:otherwise>

           </xsl:choose>



         </record>
       </xsl:otherwise>


    </xsl:choose>
   </xsl:if>
  </xsl:for-each>
  </collection>
</xsl:template>

</xsl:stylesheet>
