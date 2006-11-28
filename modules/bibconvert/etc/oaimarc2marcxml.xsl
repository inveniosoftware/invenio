<?xml version="1.0" encoding="ISO-8859-1"?>
<!-- This transformation keeps the same source file, with the following exceptions:
     - Records marked with status='deleted' are returned as deleted for Invenio
     - subfield 980 $a is removed
-->
<xsl:stylesheet version="1.0"
xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
xmlns:OAI-PMH="http://www.openarchives.org/OAI/2.0/"
exclude-result-prefixes="OAI-PMH">
<xsl:template match="/">
        <collection>
            <xsl:for-each select="//OAI-PMH:record">    
            <xsl:choose>
                <xsl:when test="OAI-PMH:header[@status='deleted']">
                    <record>
                        <xsl:if test='./OAI-PMH:header/OAI-PMH:identifier | ./OAI-PMH:header/OAI-PMH:setSpec'>
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
                <xsl:otherwise>
                    <record>
                        <xsl:for-each select="./OAI-PMH:metadata/OAI-PMH:record/OAI-PMH:datafield">
                            <xsl:if test="not(@tag='980' and @ind1='' and @ind2='' and ./OAI-PMH:subfield[@code='a'])"> 
                                <xsl:copy-of select="." />
                            </xsl:if>
                         </xsl:for-each> 
                        
		        <xsl:if test='./OAI-PMH:header/OAI-PMH:identifier'>
                        <!-- CUSTOMIZE ME: Modify the datafield below with tag and indicators used 
                                 in your Invenio installation for the OAI identifier -->
                            <datafield tag="909" ind1="C" ind2="O">
                                <subfield code="u"><xsl:value-of select="./OAI-PMH:header/OAI-PMH:identifier"/></subfield>
                            </datafield>
		        </xsl:if>
                    </record>
                </xsl:otherwise>        
            </xsl:choose>
        </xsl:for-each> 
        </collection>

</xsl:template>

</xsl:stylesheet>