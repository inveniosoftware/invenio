<?
## $Id$

## This file is part of the CERN Document Server Software (CDSware).
## Copyright (C) 2002, 2003, 2004, 2005, 2006 CERN.
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
//  File: Processor.inc (flexelink core)
//  Classes: Processor
//  Requires: AELExecutor, LinkResolver, Node, AVarSpec
//  Included: 	core/AEvalLan.inc
//		core/LinkResolver.inc
//		core/TreeNode.inc
//		core/ASpec.inc	
//		dbparams.inc
//==========================================================================

  include_once( EXECUTOR );
  include_once( LINK_RESOLVER );

//+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class BehaviorData {
  var $name;

  function BehaviorData(){}
}  

class NBehavior {

  var $conditions;

  function NBehavior( $data )
  {
    include(DB);

    $db=mysql_connect( $DB_HOST, $DB_USER, $DB_PASSWD );
    mysql_selectdb( $DB_DB, $db );
    $qry="select eval_order, el_condition
	  from flxBEHAVIORCONDITIONS
	  where otype='".$data->name."'
	  order by eval_order";
    $qh=mysql_query($qry, $db);
    $this->conditions=array();
    while($row=mysql_fetch_array($qh))
    {
      list($eorder, $ccond)=$row;
      $d=new BehCondData();
      $d->behname=$data->name;
      $d->eorder=$eorder;
      $d->code=$ccond;
      $bc=new BehCondition( $d );
      if($bc!=null)
      {
	array_push($this->conditions, $bc);
      }
    }
    //mysql_close($db);
  }

  function getResult( $vars, $record="" )
  {
    foreach($this->conditions as $condition)
    {
      if($condition==null) continue;
      list($errcode, $str)=$condition->evaluate( $vars );
      if($errcode<0) return array(0, $str);
      if($errcode==1) return array(1, $str);
    }
    return array(1, "");
  }
  
}

class IBehavior {
  
  var $conditions;

  function IBehavior( $data )
  {
    include(DB);

    $db=mysql_connect( $DB_HOST, $DB_USER, $DB_PASSWD );
    mysql_selectdb( $DB_DB, $db );
    $qry="select eval_order, el_condition
	  from flxBEHAVIORCONDITIONS
	  where otype='".$data->name."'
	  order by eval_order";
    $qh=mysql_query($qry, $db);
    $this->conditions=array();
    while($row=mysql_fetch_array($qh))
    {
      list($eorder, $ccond)=$row;
      $d=new BehCondData();
      $d->behname=$data->name;
      $d->eorder=$eorder;
      $d->code=$ccond;
      $bc=new BehCondition( $d );
      if($bc!=null)
	array_push($this->conditions, $bc);
    }
    //mysql_close($db);
  }
  
  function getResult( $vars, $record="" )
  {
    $str="";
    foreach($this->conditions as $condition)
    {
      if($condition==null) continue;
      list($errcode, $str)=$condition->evaluate( $vars );
      if($errcode<0) return array(0, $str);
      if($errcode==1) break;
    }
    $record=trim($record);
    $end_tag="</record>";
    $result=substr($record, 0, strlen($record)-strlen($end_tag)).$str.$end_tag;
    return array(1, $result);
  }

}

class BehCondData {
  var $behname;
  var $eorder;
  var $code;

  function BehCondData(){}
}

class BehCondition {

  var $exec;
  var $condition;
  var $actions;

  function BehCondition( $data )
  {
    $this->exec=new AELExecutor();
    $this->condition=null;
    $this->actions=array();
    list($ok, $msg)=$this->exec->checkCode( $data->code );
    if(!$ok) return null;
    $this->condition=$msg;

    include( DB );

    $db=mysql_connect( $DB_HOST, $DB_USER, $DB_PASSWD );
    mysql_selectdb( $DB_DB, $db );
    $qry="select el_code
	  from flxBEHAVIORCONDITIONSACTIONS
	  where otype='".$data->behname."'
	  and eval_order=".$data->eorder."
	  order by apply_order";
    $qh=mysql_query($qry, $db);
    while($row=mysql_fetch_array($qh))
    {
      list($ok, $msg)=$this->exec->checkCode($row[0]);
      if($ok)
      {
	array_push($this->actions, $msg);
      }
    }
    mysql_close($db);
  }

  function evaluate( $vars )
  {
    list($ok, $res)=$this->exec->execTree( $this->condition, $vars );
    if(!$ok) return array(-1, "Error executing action: $res");
    if($res!="TRUE") return array(0, "FALSE");
    $str="";
    foreach($this->actions as $action)
    {
      list($ok, $res)=$this->exec->execTree( $action, $vars);
      if(!$ok) continue;
      $str.=$res;
    }
    return array(1, $str);
  }

}

//+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
//  Class: Processor
//  Purpose: This is a wrapper class for the FlexElink formatting process.
//	It allows to apply a certaint pre-configured (in the Fxk config DB)
//	behavior with a set of internal variables from a single record, and 
//	gives back resulting string. There is a (private) method for each 
//	different type of behavior that the processor has to interpret: NORMAL,
//	IENRICH. It's able to apply corresponding method for each behavior type 
//  (Visible) Atributes: all private
//  (Visible) Methods: 
//	         constructor --> initializes processor 
//		 getOutput(intvars, otype, xml_doc*) ----> applies "otype"
//			pre-configured behavior from the configuration DB 
//			with the internal vars "intvars" for obtaining the
//			resulting string.  
//+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
  
  class Processor {
    var $behaviors;

//---------------------------------------------------------------------------
//  Method: CONSTRUCTOR Processor (public)
//  Description: Initializes class atributes needed to function. Creates the
//	link to the config DB; the instance of the code executor and link 
//	resolver; sets the link resolver for the code executor(in order to
//	enable link resolution on the executor)
//  Params:
//---------------------------------------------------------------------------
    function Processor()
    {
      $this->behaviors=array();
    }

//---------------------------------------------------------------------------
//  Method: DESTRUCTOR destroy (public)
//  Description:
//  Params:
//---------------------------------------------------------------------------
    function destroy() 
    {
    }

    function getBehavior( $behname )
    {
      $behname=strtoupper(trim($behname));
      if(trim($behname)=="") return null;
      if(isset($this->behaviors[$behname]))
      {
	return $this->behaviors[$behname];
      }
      else
      {
	include( DB );

	$db=mysql_connect( $DB_HOST, $DB_USER, $DB_PASSWD );
	mysql_selectdb( $DB_DB, $db );
	$qry="select type
	      from flxBEHAVIORS
	      where name='$behname'";
        $qh=mysql_query($qry, $db);
	if(mysql_num_rows($qh)!=1)
	  $res=null;
        else
	{
	  list($type)=mysql_fetch_array($qh);
	  $d=new BehaviorData();
	  $d->name=$behname;
	  if($type=="NORMAL")
	  {
	    $res=new NBehavior( $d );
	  }
	  elseif($type=="IENRICH")
	  {
	    $res=new IBehavior( $d );
	  }

	  if($res!=null)
	  {
	    $this->behaviors[$behname]=$res;
          }
        }
//	mysql_close($db);
	return $res;

      }
    }

    
//---------------------------------------------------------------------------
//  Method: getOutput (public)
//  Description: This method takes a behavior identifier as parameter, 
//	retrieves it from the config DB, checks the type of behavior, applies 
//	in each case corresponding private method, and gives the result or 
//	an error if something didn't go well.
//  Params: 
//	intvars -> (Vars) reference to the internal vars collection extracted
//		from the record over which the behavior has to be applied
//	otype ---> (string) Output type or behavior identifier to apply and 
//		that has to be pre-configure in the config DB
//	xml_doc -> (string) It's optional. In case of specified, it contains the
//		XML document of the record being processed (mandatory for
//		enriching behavior types)
//  Return value: (array) As result a two-element array is given; first value
//	is an error code an is 1 when the behavior was correctly applied; in
//	this case the second value contains the resulting string. First array
//	value can be also 0 when some error occured while applying behavior; 
//	in this case, the second value will contain a string with the error
//	description
//---------------------------------------------------------------------------
    function getOutput( $intvars, $otype, $xml_doc="" )
    {
      $b=$this->getBehavior( $otype );
      if($b==null) return array(0, "Undefined output type $otype");
      list($ok, $msg)=$b->getResult($intvars, $xml_doc);
      if(!$ok) return array(0, "Errors evaluating output type $otype: $msg");
      return array(1, $msg);
    }
}
?>
