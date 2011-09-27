<?xml version="1.0" encoding="ISO-8859-1"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:pbcore="http://www.pbcore.org/PBCore/PBCoreNamespace.html" xmlns:xsi="http://www.w3.org/2001/XMLSchema-pbcore:instance"  version="1.0" exclude-result-prefixes="pbcore xsi">
<xsl:output method="xml" indent="yes" encoding="UTF-8" omit-xml-declaration="no"/>

	<xsl:template match="/*">
		<collection>
			<record>
				<xsl:if test="pbcore:pbcoreIdentifier">
					<controlfield tag="001">
						<xsl:value-of select="pbcore:pbcoreIdentifier"/>
					</controlfield>
				</xsl:if>
				<xsl:apply-templates select="pbcore:pbcoreInstantiation"/>
			</record>
		</collection>
	</xsl:template>

	<xsl:template match="pbcore:pbcoreInstantiation">
		<datafield tag="950">
			<xsl:if test="pbcore:instantiationIdentifier">
				<subfield code="a"><xsl:value-of select="pbcore:instantiationIdentifier"/></subfield>
			</xsl:if>
			<xsl:if test="pbcore:instantiationStandard">
				<subfield code="b"><xsl:value-of select="pbcore:instantiationStandard"/>/></subfield>
			</xsl:if>
			<xsl:if test="pbcore:instantiationTimeStart">
				<subfield code="c"><xsl:value-of select="pbcore:instantiationTimeStart"/></subfield>
			</xsl:if>
			<xsl:if test="pbcore:instantiationDuration">
				<subfield code="d"><xsl:value-of select="pbcore:instantiationDuration"/></subfield>
			</xsl:if>
			<xsl:if test="pbcore:instantiationDataRate">
				<subfield code="e"><xsl:value-of select="pbcore:instantiationDataRate"/></subfield>
			</xsl:if>
			<xsl:if test="pbcore:instantiationLanguage">
				<subfield code="f"><xsl:value-of select="pbcore:instantiationLanguage"/></subfield>
			</xsl:if>
			<xsl:if test="pbcore:instantiationExtension">
				<subfield code="j"><xsl:value-of select="pbcore:instantiationExtension"/></subfield>
			</xsl:if>
			<xsl:if test="pbcore:instantiationPart">
				<subfield code="k"><xsl:value-of select="pbcore:instantiationPart"/></subfield>
			</xsl:if>
			<xsl:if test="pbcore:instantiationAnnotation">
				<subfield code="l"><xsl:value-of select="pbcore:instantiationAnnotation"/></subfield>
			</xsl:if>
			<xsl:if test="pbcore:instantiationRights">
				<subfield code="m"><xsl:value-of select="pbcore:instantiationRights"/></subfield>
			</xsl:if>
			<xsl:if test="pbcore:instantiationRelation">
				<subfield code="n"><xsl:value-of select="pbcore:instantiationRelation"/></subfield>
			</xsl:if>
			<xsl:if test="pbcore:instantiationDate">
				<subfield code="o"><xsl:value-of select="pbcore:instantiationDate"/></subfield>
			</xsl:if>
			<xsl:if test="pbcore:instantiationDimensions">
				<subfield code="p"><xsl:value-of select="pbcore:instantiationDimensions"/></subfield>
			</xsl:if>
			<xsl:if test="pbcore:instantiationPhysical">
				<subfield code="q"><xsl:value-of select="pbcore:instantiationPhysical"/></subfield>
			</xsl:if>
			<xsl:if test="pbcore:instantiationDigital">
				<subfield code="r"><xsl:value-of select="pbcore:instantiationDigital"/></subfield>
			</xsl:if>
			<xsl:if test="pbcore:instantiationLocation">
				<subfield code="s"><xsl:value-of select="pbcore:instantiationLocation"/></subfield>
			</xsl:if>
			<xsl:if test="pbcore:instantiationMediaType">
				<subfield code="t"><xsl:value-of select="pbcore:instantiationMediaType"/></subfield>
			</xsl:if>
			<xsl:if test="pbcore:instantiationGenerations">
				<subfield code="u"><xsl:value-of select="pbcore:instantiationGenerations"/></subfield>
			</xsl:if>
			<xsl:if test="pbcore:instantiationFileSize">
				<subfield code="v"><xsl:value-of select="pbcore:instantiationFileSize"/></subfield>
			</xsl:if>
			<xsl:if test="pbcore:instantiationColors">
				<subfield code="w"><xsl:value-of select="pbcore:instantiationColors"/></subfield>
			</xsl:if>
			<xsl:if test="pbcore:instantiationTracks">
				<subfield code="x"><xsl:value-of select="pbcore:instantiationTracks"/></subfield>
			</xsl:if>
			<xsl:if test="pbcore:instantiationChannelConfiguration">
				<subfield code="y"><xsl:value-of select="pbcore:instantiationChannelConfiguration"/></subfield>
			</xsl:if>
			<xsl:if test="pbcore:instantiationAlternativeModes">
				<subfield code="z"><xsl:value-of select="pbcore:instantiationAlternativeModes"/></subfield>
			</xsl:if>
			</datafield>
			<xsl:apply-templates select="pbcore:instantiationEssenceTrack"/>
	</xsl:template>
	
	<xsl:template match="pbcore:instantiationEssenceTrack">
		<datafield tag="951">
			<xsl:if test="pbcore:essenceTrackIdentifier">
				<subfield code="a"><xsl:value-of select="pbcore:essenceTrackIdentifier"/></subfield>
			</xsl:if>
			<xsl:if test="pbcore:essenceTrackStandard">
				<subfield code="b"><xsl:value-of select="pbcore:essenceTrackStandard"/></subfield>
			</xsl:if>
			<xsl:if test="pbcore:essenceTrackTimeStart">
				<subfield code="c"><xsl:value-of select="pbcore:essenceTrackTimeStart"/></subfield>
			</xsl:if>
			<xsl:if test="pbcore:essenceTrackDuration">
				<subfield code="d"><xsl:value-of select="pbcore:essenceTrackDuration"/></subfield>
			</xsl:if>
			<xsl:if test="pbcore:essenceTrackDataRate">
				<subfield code="e"><xsl:value-of select="pbcore:essenceTrackDataRate"/></subfield>
			</xsl:if>
			<xsl:if test="pbcore:essenceTrackLanguage">
				<subfield code="f"><xsl:value-of select="pbcore:essenceTrackLanguage"/></subfield>
			</xsl:if>
			<xsl:if test="pbcore:essenceTrackType">
				<subfield code="q"><xsl:value-of select="pbcore:essenceTrackType"/></subfield>
			</xsl:if>
			<xsl:if test="pbcore:essenceTrackEncoding">
				<subfield code="r"><xsl:value-of select="pbcore:essenceTrackEncoding"/></subfield>
			</xsl:if>
			<xsl:if test="pbcore:essenceTrackFrameRate">
				<subfield code="s"><xsl:value-of select="pbcore:essenceTrackFrameRate"/></subfield>
			</xsl:if>
			<xsl:if test="pbcore:essenceTrackPlaybackSpeed">
				<subfield code="t"><xsl:value-of select="pbcore:essenceTrackPlaybackSpeed"/></subfield>
			</xsl:if>
			<xsl:if test="pbcore:essenceTrackSamplingRate">
				<subfield code="u"><xsl:value-of select="pbcore:essenceTrackSamplingRate"/></subfield>
			</xsl:if>
			<xsl:if test="pbcore:essenceTrackBitDepth">
				<subfield code="v"><xsl:value-of select="pbcore:essenceTrackBitDepth"/></subfield>
			</xsl:if>
			<xsl:if test="pbcore:essenceTrackFrameSize">
				<subfield code="w"><xsl:value-of select="pbcore:essenceTrackFrameSize"/></subfield>
			</xsl:if>
			<xsl:if test="pbcore:essenceTrackAspectRatio">
				<subfield code="x"><xsl:value-of select="pbcore:essenceTrackAspectRatio"/></subfield>
			</xsl:if>
			<xsl:if test="pbcore:essenceTrackAnnotation">
				<subfield code="y"><xsl:value-of select="pbcore:essenceTrackAnnotation"/></subfield>
			</xsl:if>
			<xsl:if test="pbcore:essenceTrackExtension">
				<subfield code="z"><xsl:value-of select="pbcore:essenceTrackExtension"/></subfield>
			</xsl:if>
		</datafield>
	</xsl:template>
	

</xsl:stylesheet>