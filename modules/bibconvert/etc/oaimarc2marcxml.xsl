<?xml version="1.0" encoding="ISO-8859-1"?>
<!-- This transformation keeps the same source file, with the following exceptions:
     - Records marked with status='deleted' are returned as deleted for Invenio
     - subfield 980 $w is removed

     It is provided only as an example of transformation.
     Please look for 'CUSTOMIZEME' labels in this stylesheet in order to find
     key parts that you should customize to fit your installation needs.

     Also note that this stylesheet expect source file to correctly refers to
        http://www.loc.gov/MARC21/slim and 
        http://www.openarchives.org/OAI/2.0/ namespaces
-->
<xsl:stylesheet version="1.0"
xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
xmlns:OAI-PMH="http://www.openarchives.org/OAI/2.0/"
xmlns:marc="http://www.loc.gov/MARC21/slim"
exclude-result-prefixes="OAI-PMH marc">
<xsl:template match="/">
        <collection>
            <xsl:for-each select="//OAI-PMH:record">
            <xsl:choose>
                <xsl:when test="./OAI-PMH:header[@status='deleted']">
                    <record>
                        <xsl:if test="./OAI-PMH:header/OAI-PMH:identifier | ./OAI-PMH:header/OAI-PMH:setSpec">
        		            <datafield tag="909" ind1="C" ind2="O">
                                <subfield code="o"><xsl:value-of select="./OAI-PMH:header/OAI-PMH:identifier"/></subfield>
                                <subfield code="p"><xsl:value-of select="./OAI-PMH:header/OAI-PMH:setSpec"/></subfield>
                             </datafield>
                        </xsl:if>
                        <datafield tag="980" ind1=" " ind2=" ">
                            <subfield code="c">DELETED</subfield>
                        </datafield>
                     </record>
                </xsl:when>
                <xsl:otherwise>
                    <record>
                        <xsl:for-each select="./OAI-PMH:metadata/marc:record/marc:datafield">
                           <!-- CUSTOMIZEME: Modify below in order to choose which 
                                             datafield/subfield will be kept
                                             and which will be dropped  
                                                
                                             Sample below: -keep if tag is not 980__ and has subfields
                                                           -if tag is 980__ , keep datafield only if some
                                                            subfield with code != 'w' exist. Remove
                                                            subfield 980__w.
                                                -->   
                            <xsl:choose>  
                               <xsl:when test="not(@tag='980' and (@ind1='' or @ind1=' ') and (@ind2='' or @ind2=' ') and ./marc:subfield)">
                                 <xsl:element name="{local-name(.)}">
                                    <xsl:copy-of select="@*"/>
                                    <xsl:for-each select="./marc:subfield">
                                         <xsl:element name="{local-name(.)}">
                                             <xsl:copy-of select="@*"/>
                                             <xsl:value-of select="."/>
                                         </xsl:element>
                                    </xsl:for-each>
                                 </xsl:element> 
                               </xsl:when>
                               <xsl:otherwise>
                                 <xsl:if test="./marc:subfield[@code!='w']">
                                 <xsl:element name="{local-name(.)}">
                                    <xsl:copy-of select="@*"/>
                                    <xsl:for-each select="./marc:subfield[@code!='w']">
                                         <xsl:element name="{local-name(.)}">
                                             <xsl:copy-of select="@*"/>
                                             <xsl:value-of select="."/>
                                         </xsl:element>
                                    </xsl:for-each>
                                 </xsl:element> 
                                 </xsl:if>
                               </xsl:otherwise>
                            </xsl:choose>
                         </xsl:for-each> 
                        
		        <xsl:if test="./OAI-PMH:header/OAI-PMH:identifier">
                        <!-- CUSTOMIZEME: Modify the datafield below with tag and indicators used 
                                 in your Invenio installation for the OAI identifier -->
                            <datafield tag="909" ind1="C" ind2="O">
                                <subfield code="o"><xsl:value-of select="./OAI-PMH:header/OAI-PMH:identifier"/></subfield>
                            </datafield>
		        </xsl:if>
                    </record>
                </xsl:otherwise>        
            </xsl:choose>
        </xsl:for-each> 
        </collection>

</xsl:template>

</xsl:stylesheet>