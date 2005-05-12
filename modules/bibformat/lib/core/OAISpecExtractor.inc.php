<?
## $Id$

## This file is part of the CERN Document Server Software (CDSware).
## Copyright (C) 2002, 2003, 2004, 2005 CERN.
##
## The CDSware is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## The CDSware is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.  
##
## You should have received a copy of the GNU General Public License
## along with CDSware; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

//==========================================================================
//  File: OAISpecExtractor.inc (flexElink core)
//  Classes:    OAIVarExtractor
//  Requires: Vars
//  Included:   core/IntVars.inc, DB
//==========================================================================

  include_once(INTVARS);

//++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
//  Class: OAIVarExtractor
//  Purpose:
//  Attributes:
//  Methods:
//++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

  class OAIVarExtractor {
    var $xml_parser;
    var $doc;
    var $db;
    var $type;
    var $errortext;
    var $intvars;
    var $CFcache;
    var $MFcache;
    var $SFcache;
    
    function OAIVarExtractor()
    {
      include( DB );

      $this->db=$db=mysql_pconnect( $DB_HOST, $DB_USER, $DB_PASSWD );
      if($this->db)
	mysql_selectdb( $DB_DB, $this->db );
      $this->errortext="";
      $this->CFcache=array();
      $this->MFcache=array();
      $this->SFcache=array();
    }

    function destroy()
    {
    }

    function getError()
    {
      return $this->errortext;
    }
    
    function inCFcache( $tag )
    {
      return $this->CFcache["$tag"];
    }

    function addCFcache($tag, $vars)
    {
      $this->CFcache["$tag"]=$vars;
    }

    function inMFcache($id, $i1, $i2)
    {
      return $this->MFcache["$id::$i1::$i2"];
    }
    
    function addMFcache($id, $i1, $i2, $vars)
    {
      $this->MFcache["$id::$i1::$i2"]=$vars;
    }
    
    function inSFcache($varname, $label)
    {
      return $this->SFcache["$varname::$label"];
    }
    
    function addSFcache($varname, $label, $vars)
    {
      $this->SFcache["$varname::$label"]=$vars;
    }

    function getVarfromCF( $tag )
    {
      $vars=$this->inCFcache( $tag );
      if($vars!=null)
        return $vars;
      $tag=addslashes($tag);
      $qry="select varname, mvalues from flxXMLMARCEXTRULES where type='".
            addslashes($this->type)."' and att_id='$tag'
            and ftype='CONTROLFIELD'";
      $res=mysql_query($qry, $this->db);
      $vars=array();
      while($row=mysql_fetch_array($res))
      {
        array_push( $vars, array($row["varname"], $row["mvalues"]) );
      }
      $this->addCFcache( $tag, $vars );
      return $vars;
    }

    function getVarfromMF( $id, $i1, $i2 )
    {
      $vars=$this->inMFcache( $id, $i1, $i2 );
      if($vars!=null)
	return $vars;
      $id=addslashes($id);
      $i1=addslashes($i1);
      $i2=addslashes($i2);
      $qry="select varname, mvalues from flxXMLMARCEXTRULES where type='".
	 addslashes($this->type)."' and att_id='".addslashes($id).
         "' and att_i1='".addslashes($i1)."' and att_i2='".addslashes($i2)."'";
      $res=mysql_query($qry, $this->db);
      $vars=array();
      while($row=mysql_fetch_array($res))
      {
	array_push( $vars, array($row["varname"], $row["mvalues"]) );
      }
      $this->addMFcache( $id, $i1, $i2, $vars );
      return $vars;
    }

    function getVarfromSF( $varname, $label )
    {
      $vars=$this->inSFcache( $varname, $label );
      if($vars!=null)
	return $vars;
      $varname=addslashes($varname);
      $label=addslashes($label);
      $qry="select sfname from flxXMLMARCEXTRULESUBFIELDS where type='".
	 addslashes($this->type)."' and varname='".addslashes($varname).
         "' and att_label='".addslashes($label)."'";
      $res=mysql_query($qry, $this->db);
      $vars=array();
      while($row=mysql_fetch_array($res))
      {
	array_push( $vars, $row["sfname"] );
      }
      $this->addSFcache( $varname, $label, $vars );
      return $vars;
    }

    function getVars( $type, $doc )
    {
      $this->type=strtoupper(trim($type));
      if(!$this->db)
      {
	$this->errortext="Invalid database resource";
	return null;
      }
      $this->intvars=new Vars();
      $this->insideCF=0;
      $this->insideMF=0;
      $this->insideSF=0;
      $this->ignore=0;
      $this->doc=$doc;
      $this->xml_parser=xml_parser_create();
      xml_set_object($this->xml_parser, &$this);
      xml_parser_set_option($this->xml_parser, XML_OPTION_CASE_FOLDING, 1);
      xml_set_element_handler($this->xml_parser, "startElement", "endElement");
      xml_set_character_data_handler($this->xml_parser, "characterData");
      if(!xml_parse($this->xml_parser, $doc, 1))
      {
        $this->errortext=sprintf("XML error: %s at line %d",
		xml_error_string(xml_get_error_code($this->xml_parser)),
		xml_get_current_line_number($this->xml_parser));
        xml_parser_free($this->xml_parser);
        return null;
      }
      xml_parser_free($this->xml_parser);
      return $this->intvars;
    }

    function startElement($parser, $name, $attrs)
    {
      if($this->ignore>0)
      {
	$this->ignore++;
	return;
      }
      if($name=="CONTROLFIELD")
      {
        if($this->insideCF)
        {
          $this->ignore--;
          return;
        }
        $this->insideCF=1;
        $this->tempCF="";
        $this->varsCF=$this->getVarfromCF( $attrs["TAG"] );
      }
      elseif($name=="DATAFIELD")
      {
	//If we are already processing a VARFIELD element and we find another
	//	one inside, it's a wrong XML, so we just ignore until the wrong
	//	element and all it contains is finished
	if( ($this->insideMF) || ($this->insideCF) )
	{
	  $this->ignore++;
	  return;
	}
	$this->insideMF=1;
	$this->tempMF="";
	$this->varsMF=$this->getVarfromMF(
		$attrs["TAG"], $attrs["IND1"], $attrs["IND2"]);
      }
      elseif($name=="SUBFIELD")
      {
	//When we find a SUBFIELD element, we need to check that it's contained
	//  by a VARFIELD one. It's also a wrong XML if we find another SUBFIELD
	//  tag inside it
	if((!$this->insideMF)||($this->insideSF))
	{
	  $this->ignore++;
	  return;
	}
	$this->insideSF=1;
	$this->tempSF="";
	$this->labelSF=$attrs["CODE"];
      }
      //For other types of TAGs we don't care, because is supposed that the
      //  input will be OK
      else
      {
	if($name!="RECORD")
	  $this->ignore++;
      }

    }

    function endElement($parser, $name)
    {
      if($this->ignore>0)
      {
	$this->ignore--;
	return;
      }
      if($name=="CONTROLFIELD")
      {
        $this->insideCF=0;
        if(($this->varsCF!=null)&&(count($this->varsCF)>0))
        {
          foreach($this->varsCF as $var)
          {
            list($varname, $mvalues)=$var;
            $this->intvars->addValue( $varname, $this->tempCF );
            if($mvalues=="S")
              $this->intvars->inextValue( $varname );
          }
        }
      }
      //As the XML parser will check the validness of the XML, there is no
      //  possibility to find a closing DATAFIELD before a closing SUBFIELD, so
      //  we don't need to check it
      elseif($name=="DATAFIELD")
      {
	$this->insideMF=0;
        if(($this->varsMF!=null)&&(count($this->varsMF)>0))
	{
	  foreach($this->varsMF as $var)
	  {
            list($varname, $mvalues)=$var;
	    $this->intvars->addValue( $varname, $this->tempMF );
            if($mvalues=="S")
	      $this->intvars->inextValue( $varname );
          }
	}

      }
      elseif($name=="SUBFIELD")
      {
	$this->insideSF=0;
        if(($this->varsMF!=null)&&(count($this->varsMF)>0))
	{
	  foreach($this->varsMF as $var)
	  {
            list($varname, $mvalues)=$var;
	    $this->intvars->addVar($varname);
            $ow=true;
            if($mvalues!="S") $ow=false;
	    $sfs=$this->getVarfromSF( $varname, $this->labelSF );
	    if(($sfs!=null)&&(count($sfs)>0))
	    {
	      foreach($sfs as $sfname)
	      {
	        $this->intvars->addSFValue( $varname, $sfname, $this->tempSF, $ow );
	      }
	    }
	  }
	}
      }
    }

    function characterData($parser, $data)
    {
      if($this->ignore>0)
	return;
      if($this->insideCF)
      {
        $this->tempCF.=$data;
      }
      elseif($this->insideMF)
      {
	if($this->insideSF)
	  $this->tempSF.=$data;
        else
	  $this->tempMF.=$data;
      }
    }

  }
?>
