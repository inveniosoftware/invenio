<?xml version="1.0" encoding="ISO-8859-1"?>

<xsl:stylesheet version="1.0"
xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
xmlns:OAI-PMH="http://www.openarchives.org/OAI/2.0/"
xmlns:oaidc="http://www.openarchives.org/OAI/2.0/oai_dc/"
xmlns:dc="http://purl.org/dc/elements/1.1/"
exclude-result-prefixes="OAI-PMH oaidc dc">
<xsl:template match="/">
        <collection>
            <xsl:for-each select="//OAI-PMH:record">    
            <xsl:choose>
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
                <xsl:otherwise>
                    <record>
                    	<xsl:if test="./OAI-PMH:metadata/oaidc:dc/dc:language">
                            <datafield tag="041" ind1="" ind2="">
                                <subfield code="a"><xsl:value-of select="./OAI-PMH:metadata/oaidc:dc/dc:language"/></subfield>
                            </datafield>
                
	        	</xsl:if>
		        <xsl:if test="./OAI-PMH:metadata/oaidc:dc/dc:creator[1]">
                            <datafield tag="100" ind1="" ind2="">
                                <subfield code="a"><xsl:value-of select="./OAI-PMH:metadata/oaidc:dc/dc:creator[1]"/></subfield>
                            </datafield>
                        </xsl:if>
		<xsl:if test="./OAI-PMH:metadata/oaidc:dc/dc:title">
                
		    <datafield tag="245" ind1="" ind2="">
                        <subfield code="a"><xsl:value-of select="./OAI-PMH:metadata/oaidc:dc/dc:title"/></subfield>
                    </datafield>
                
		</xsl:if>
		<xsl:if test="./OAI-PMH:metadata/oaidc:dc/dc:title | ./OAI-PMH:metadata/oaidc:dc/dc:date">
                
                    <datafield tag="260" ind1="" ind2="">
		        <xsl:if test="./OAI-PMH:metadata/oaidc:dc/dc:publisher">
                        
		            <subfield code="b"><xsl:value-of select="./OAI-PMH:metadata/oaidc:dc/dc:publisher"/></subfield>
                        
                        </xsl:if>
			<xsl:if test="./OAI-PMH:metadata/oaidc:dc/dc:date">
                        
			    <subfield code="c"><xsl:value-of select="./OAI-PMH:metadata/oaidc:dc/dc:date"/></subfield>
			
                        </xsl:if>
                    </datafield>
                
		</xsl:if>
		<xsl:if test="./OAI-PMH:metadata/oaidc:dc/dc:coverage">
                
	    	    <datafield tag="500" ind1="" ind2="">
                        <subfield code="a"><xsl:value-of select="./OAI-PMH:metadata/oaidc:dc/dc:coverage"/></subfield>
                    </datafield>
                
		</xsl:if>
		<xsl:if test="./OAI-PMH:metadata/oaidc:dc/dc:description">
                
                    <datafield tag="520" ind1="" ind2="">
                        <subfield code="a"><xsl:value-of select="./OAI-PMH:metadata/oaidc:dc/dc:description"/></subfield>
                    </datafield>
                
		</xsl:if>
		<xsl:if test="./OAI-PMH:metadata/oaidc:dc/dc:rights">
                
		    <datafield tag="540" ind1="" ind2="">
                        <subfield code="a"><xsl:value-of select="./OAI-PMH:metadata/oaidc:dc/dc:rights"/></subfield>
                    </datafield>
                
		</xsl:if>
		<xsl:if test="./OAI-PMH:metadata/oaidc:dc/dc:subject">
                
                    <datafield tag="650" ind1="1" ind2="7">
                        <subfield code="a"><xsl:value-of select="./OAI-PMH:metadata/oaidc:dc/dc:subject"/></subfield>  
                    </datafield>
                
		</xsl:if>
		<xsl:if test="./OAI-PMH:metadata/oaidc:dc/dc:type">
                
		    <datafield tag="655" ind1="7" ind2="">
                        <subfield code="a"><xsl:value-of select="./OAI-PMH:metadata/oaidc:dc/dc:type"/></subfield>  
                    </datafield>
                
		</xsl:if>
		<xsl:for-each select="./OAI-PMH:metadata/oaidc:dc/dc:creator[position()>1]">
                    <datafield tag="700" ind1="" ind2="">
                    	<subfield code="a"><xsl:value-of select="."/></subfield>
                    </datafield>
		</xsl:for-each>
		<xsl:if test="./OAI-PMH:metadata/oaidc:dc/dc:contributor">
                
		    <datafield tag="720" ind1="" ind2="">
                        <subfield code="a"><xsl:value-of select="./OAI-PMH:metadata/oaidc:dc/dc:contributor"/></subfield>
                    </datafield>
                
		</xsl:if>
		<xsl:if test="./OAI-PMH:metadata/oaidc:dc/dc:source">
                
		    <datafield tag="786" ind1="0" ind2="">
                        <subfield code="n"><xsl:value-of select="./OAI-PMH:metadata/oaidc:dc/dc:source"/></subfield>
                    </datafield>
                
		</xsl:if>
		<xsl:if test="./OAI-PMH:metadata/oaidc:dc/dc:relation">
                
		    <datafield tag="786" ind1="0" ind2="">
                        <subfield code="n"><xsl:value-of select="./OAI-PMH:metadata/oaidc:dc/dc:relation"/></subfield>
                    </datafield>
                
		</xsl:if>
		<xsl:if test="./OAI-PMH:metadata/oaidc:dc/dc:format">
                
                    <datafield tag="856" ind1="" ind2="">
                        <subfield code="q"><xsl:value-of select="./OAI-PMH:metadata/oaidc:dc/dc:format"/></subfield>
                    </datafield>
                
		</xsl:if>
		<xsl:if test="./OAI-PMH:header/OAI-PMH:identifier">
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