<?
## $Id$

## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
##
## CDS Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.  
##
## You should have received a copy of the GNU General Public License
## along with CDS Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

//Main class

  include(RECORD_SEP);
  include(VARIABLE_EXT);
  include(PROCESSOR);

class CreateOAIMARCXMLFactory {

  function CreateOAIMARCXMLFactory() 
  { 
    $this->error="";
  }

  function error()
  {
    return $this->error;
  }

  function & createSeparator( $ifile="" ) 
  {
    $sep=new XMLSimpleRecSeparator();
    $error=$sep->setIFile( $ifile );
    if($error)
    {
      $this->error=$error;
      return "";
    }
    $sep->setTag("record");
    return $sep;
  }


  function & createExtractor() 
  {
    $ext=new OAIVarExtractor();
    return $ext;
  }
}

class FlexElink {

  function FlexElink()
  {
  }

  function initialise( $itype, $ifile="" )
  {
    $this->itype=trim(strtoupper($itype));


    if($itype=="OAIMARC")
      $this->factory=new CreateOAIMARCXMLFactory();
    else
      return "Not suported input type: $itype";

    $this->separator=& $this->factory->createSeparator( $ifile );
    if(!$this->separator)
      return "Error while creating the Record Separator: ".$this->factory->error();
    $this->extractor=& $this->factory->createExtractor();
    if(!$this->extractor)
      return "Error while creating the Variable Extractor: ".$this->factory->error();
    $this->processor=new Processor();
    return "";
  }

  function getRecordResult($otypes, $debug=0)
  {
    $record=$this->clean($this->separator->getRecord());
    //No more records
    if($record=="")
      return array(-1, "");
    //More records
    set_time_limit(TIMELIMIT);
    $vars=$this->extractor->getVars("DEFAULT", $record);
    if($vars==null)
      return array(0, $this->extractor->getError());
    if($debug)
      $vars->debug();
    $result="";
    foreach($otypes as $otype)
    {
      if(trim($otype)=="")
        continue;
      list($ok, $msg)=$this->processor->getOutput( $vars, $otype, $record );
      if($ok) 
        $result.=$msg;
      else
        return array(0, "Error processing record with otype '$otype':".$msg);
    }
    return array(1, $result);
  }

  function getResult( $otype, $itype, $ifile="" )
  {
  }
  function clean($text)
  {
    $text = str_replace("\016","",$text);
    $text = str_replace("\017","",$text);
    $text = str_replace("\018","",$text);
    $text = str_replace("\019","",$text);
    $text = str_replace("\020","",$text);
    $text = str_replace("\021","",$text);
    $text = str_replace("\022","",$text);
    $text = str_replace("\023","",$text);
    $text = str_replace("\024","",$text);
    $text = str_replace("\025","",$text);
    $text = str_replace("\026","",$text);
    $text = str_replace("\027","",$text);
    $text = str_replace("\028","",$text);
    $text = str_replace("\029","",$text);
    $text = str_replace("\030","",$text);
    $text = str_replace("\031","",$text);
    $text = str_replace("\032","",$text);
    $text = str_replace("\033","",$text);
    $text = str_replace("\034","",$text);
    $text = str_replace("\035","",$text);
    $text = str_replace("\036","",$text);
    $text = str_replace("\037","",$text);
    return $text;
  }
}

?>
