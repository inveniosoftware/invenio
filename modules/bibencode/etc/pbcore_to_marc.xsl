<?xml version="1.0" encoding="ISO-8859-1"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:marc="http://www.loc.gov/MARC21/slim" xmlns:pbcore="http://www.pbcore.org/PBCore/PBCoreNamespace.html" xmlns:xsi="http://www.w3.org/2001/XMLSchema-pbcore:instance"  version="1.0" exclude-result-prefixes="marc">
<xsl:output method="xml" indent="yes" encoding="UTF-8" omit-xml-declaration="no"/>

	<xsl:template match="/*">
		<marc:collection>
			<marc:record>
				<xsl:if test="pbcore:pbcoreIdentifier">
					<marc:controlfield tag="001">
						<xsl:value-of select="pbcore:pbcoreIdentifier"/>
					</marc:controlfield>
				</xsl:if>
				<xsl:apply-templates select="pbcore:pbcoreInstantiation"/>
			</marc:record>
		</marc:collection>
	</xsl:template>

	<xsl:template match="pbcore:pbcoreInstantiation">
		<marc:datafield tag="950">
			<xsl:if test="pbcore:instantiationIdentifier">
				<marc:subfield code="a"><xsl:value-of select="pbcore:instantiationIdentifier"/></marc:subfield>
			</xsl:if>
			<xsl:if test="pbcore:instantiationStandard">
				<marc:subfield code="b"><xsl:value-of select="pbcore:instantiationStandard"/>/></marc:subfield>
			</xsl:if>
			<xsl:if test="pbcore:instantiationTimeStart">
				<marc:subfield code="c"><xsl:value-of select="pbcore:instantiationTimeStart"/></marc:subfield>
			</xsl:if>
			<xsl:if test="pbcore:instantiationDuration">
				<marc:subfield code="d"><xsl:value-of select="pbcore:instantiationDuration"/></marc:subfield>
			</xsl:if>
			<xsl:if test="pbcore:instantiationDataRate">
				<marc:subfield code="e"><xsl:value-of select="pbcore:instantiationDataRate"/></marc:subfield>
			</xsl:if>
			<xsl:if test="pbcore:instantiationLanguage">
				<marc:subfield code="f"><xsl:value-of select="pbcore:instantiationLanguage"/></marc:subfield>
			</xsl:if>
			<xsl:if test="pbcore:instantiationExtension">
				<marc:subfield code="j"><xsl:value-of select="pbcore:instantiationExtension"/></marc:subfield>
			</xsl:if>
			<xsl:if test="pbcore:instantiationPart">
				<marc:subfield code="k"><xsl:value-of select="pbcore:instantiationPart"/></marc:subfield>
			</xsl:if>
			<xsl:if test="pbcore:instantiationAnnotation">
				<marc:subfield code="l"><xsl:value-of select="pbcore:instantiationAnnotation"/></marc:subfield>
			</xsl:if>
			<xsl:if test="pbcore:instantiationRights">
				<marc:subfield code="m"><xsl:value-of select="pbcore:instantiationRights"/></marc:subfield>
			</xsl:if>
			<xsl:if test="pbcore:instantiationRelation">
				<marc:subfield code="n"><xsl:value-of select="pbcore:instantiationRelation"/></marc:subfield>
			</xsl:if>
			<xsl:if test="pbcore:instantiationDate">
				<marc:subfield code="o"><xsl:value-of select="pbcore:instantiationDate"/></marc:subfield>
			</xsl:if>
			<xsl:if test="pbcore:instantiationDimensions">
				<marc:subfield code="p"><xsl:value-of select="pbcore:instantiationDimensions"/></marc:subfield>
			</xsl:if>
			<xsl:if test="pbcore:instantiationPhysical">
				<marc:subfield code="q"><xsl:value-of select="pbcore:instantiationPhysical"/></marc:subfield>
			</xsl:if>
			<xsl:if test="pbcore:instantiationDigital">
				<marc:subfield code="r"><xsl:value-of select="pbcore:instantiationDigital"/></marc:subfield>
			</xsl:if>
			<xsl:if test="pbcore:instantiationLocation">
				<marc:subfield code="s"><xsl:value-of select="pbcore:instantiationLocation"/></marc:subfield>
			</xsl:if>
			<xsl:if test="pbcore:instantiationMediaType">
				<marc:subfield code="t"><xsl:value-of select="pbcore:instantiationMediaType"/></marc:subfield>
			</xsl:if>
			<xsl:if test="pbcore:instantiationGenerations">
				<marc:subfield code="u"><xsl:value-of select="pbcore:instantiationGenerations"/></marc:subfield>
			</xsl:if>
			<xsl:if test="pbcore:instantiationFileSize">
				<marc:subfield code="v"><xsl:value-of select="pbcore:instantiationFileSize"/></marc:subfield>
			</xsl:if>
			<xsl:if test="pbcore:instantiationColors">
				<marc:subfield code="w"><xsl:value-of select="pbcore:instantiationColors"/></marc:subfield>
			</xsl:if>
			<xsl:if test="pbcore:instantiationTracks">
				<marc:subfield code="x"><xsl:value-of select="pbcore:instantiationTracks"/></marc:subfield>
			</xsl:if>
			<xsl:if test="pbcore:instantiationChannelConfiguration">
				<marc:subfield code="y"><xsl:value-of select="pbcore:instantiationChannelConfiguration"/></marc:subfield>
			</xsl:if>
			<xsl:if test="pbcore:instantiationAlternativeModes">
				<marc:subfield code="z"><xsl:value-of select="pbcore:instantiationAlternativeModes"/></marc:subfield>
			</xsl:if>
			</marc:datafield>
			<xsl:apply-templates select="pbcore:instantiationEssenceTrack"/>
	</xsl:template>
	
	<xsl:template match="pbcore:instantiationEssenceTrack">
		<marc:datafield tag="951">
			<xsl:if test="pbcore:essenceTrackIdentifier">
				<marc:subfield code="a"><xsl:value-of select="pbcore:essenceTrackIdentifier"/></marc:subfield>
			</xsl:if>
			<xsl:if test="pbcore:essenceTrackStandard">
				<marc:subfield code="b"><xsl:value-of select="pbcore:essenceTrackStandard"/></marc:subfield>
			</xsl:if>
			<xsl:if test="pbcore:essenceTrackTimeStart">
				<marc:subfield code="c"><xsl:value-of select="pbcore:essenceTrackTimeStart"/></marc:subfield>
			</xsl:if>
			<xsl:if test="pbcore:essenceTrackDuration">
				<marc:subfield code="d"><xsl:value-of select="pbcore:essenceTrackDuration"/></marc:subfield>
			</xsl:if>
			<xsl:if test="pbcore:essenceTrackDataRate">
				<marc:subfield code="e"><xsl:value-of select="pbcore:essenceTrackDataRate"/></marc:subfield>
			</xsl:if>
			<xsl:if test="pbcore:essenceTrackLanguage">
				<marc:subfield code="f"><xsl:value-of select="pbcore:essenceTrackLanguage"/></marc:subfield>
			</xsl:if>
			<xsl:if test="pbcore:essenceTrackType">
				<marc:subfield code="q"><xsl:value-of select="pbcore:essenceTrackType"/></marc:subfield>
			</xsl:if>
			<xsl:if test="pbcore:essenceTrackEncoding">
				<marc:subfield code="r"><xsl:value-of select="pbcore:essenceTrackEncoding"/></marc:subfield>
			</xsl:if>
			<xsl:if test="pbcore:essenceTrackFrameRate">
				<marc:subfield code="s"><xsl:value-of select="pbcore:essenceTrackFrameRate"/></marc:subfield>
			</xsl:if>
			<xsl:if test="pbcore:essenceTrackPlaybackSpeed">
				<marc:subfield code="t"><xsl:value-of select="pbcore:essenceTrackPlaybackSpeed"/></marc:subfield>
			</xsl:if>
			<xsl:if test="pbcore:essenceTrackSamplingRate">
				<marc:subfield code="u"><xsl:value-of select="pbcore:essenceTrackSamplingRate"/></marc:subfield>
			</xsl:if>
			<xsl:if test="pbcore:essenceTrackBitDepth">
				<marc:subfield code="v"><xsl:value-of select="pbcore:essenceTrackBitDepth"/></marc:subfield>
			</xsl:if>
			<xsl:if test="pbcore:essenceTrackFrameSize">
				<marc:subfield code="w"><xsl:value-of select="pbcore:essenceTrackFrameSize"/></marc:subfield>
			</xsl:if>
			<xsl:if test="pbcore:essenceTrackAspectRatio">
				<marc:subfield code="x"><xsl:value-of select="pbcore:essenceTrackAspectRatio"/></marc:subfield>
			</xsl:if>
			<xsl:if test="pbcore:essenceTrackAnnotation">
				<marc:subfield code="y"><xsl:value-of select="pbcore:essenceTrackAnnotation"/></marc:subfield>
			</xsl:if>
			<xsl:if test="pbcore:essenceTrackExtension">
				<marc:subfield code="z"><xsl:value-of select="pbcore:essenceTrackExtension"/></marc:subfield>
			</xsl:if>
		</marc:datafield>
	</xsl:template>
	

</xsl:stylesheet>