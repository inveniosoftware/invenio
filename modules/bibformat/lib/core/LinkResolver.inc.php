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
//  File: LinkResolver.inc (flexElink core)
//  Classes:    LinkResolver
//  Requires: AELExecutor, Vars, IntVar
//  Included:  EXECUTOR, INTVARS, DB 
//==========================================================================

  include_once(EXECUTOR);
  include_once(INTVARS);


//++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
//  Class: Link
//  Purpose:
//  Attributes:
//  Methods:
//++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class Link {

  var $type;
  var $params;
  var $conditions;

  function Link( $type )
  {

    include( DB );

    $db=mysql_connect( $DB_HOST, $DB_USER, $DB_PASSWD );
    mysql_selectdb( $DB_DB, $db );

    $this->params=array();
    $qry="select pname
	  from flxLINKTYPEPARAMS
	  where linktype='".addslashes($type)."'
	  order by ord";
    $qh=mysql_query($qry, $db);
    while($row=mysql_fetch_array($qh))
    {
      array_push($this->params, $row[0]);
    }
    
    $this->conditions=array();
    $qry="select eval_order, el_condition, solvingtype, base_file, base_url
	  from flxLINKTYPECONDITIONS
	  where linktype='".$type."'
	  order by eval_order";
    $qh=mysql_query($qry);
    while($row=mysql_fetch_array($qh))
    {
      list($eorder, $ccode, $stype, $file, $url)=$row;
      $d=new LinkConditionData();
      $d->linktype=$type;
      $d->eorder=$eorder;
      $d->code=$ccode;
      if($stype=="INT")
      {
        $d->file=$file;
        $d->url=$url;
	$c=new LinkConditionINT( $d );
      }
      else
      {
	$c=new LinkConditionEXT( $d );
      }
      if($c!=null)
        array_push($this->conditions, $c);
    }
    //mysql_close($db);
  }

  function check( $par_values )
  {
    return (count($par_values)==count($this->params));
  }

  function solve( $par_values )
  {
    if(count($par_values)!=count($this->params))
    {
      return array(0, "Incorrect number of parameters");
    }
    $vars=new Vars();
    for($i=0;$i<=count($this->params);$i++)
    {
      $vars->addValue($this->params[$i], $par_values[$i]);
    }
    foreach($this->conditions as $cond)
    {
      list($errcode, $link)=$cond->evaluate($vars);
      if($errcode<0) return array(0, "$link");
      if($errcode==0) continue;
      return array(1, $link);
    }
    return array(0, "NOT SOLVED");
  }

}

//++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
//  Class: LinkConditionData (non-visible)
//  Purpose:
//  Attributes:
//  Methods:
//++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class LinkConditionData{
  var $linktype;
  var $eorder;
  var $code;
  var $file;
  var $url;

  function LinkConditionData(){}
}

//++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
//  Class: LinkConditionINT (implements LinkCondition)
//  Purpose:
//  Attributes:
//  Methods:
//++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class LinkConditionINT {

  var $condition;
  var $actions;
  var $formats;
  var $exec;
  var $file_path;
  var $url_path;

  function LinkConditionINT( $data )
  {
    if($data==null) return null;
    $this->exec=new AELExecutor();
    list($ok, $msg)=$this->exec->checkCode( $data->code );
    if(!$ok) return null;
    $this->condition=$msg;
    $this->file_path=$data->file;
    $this->url_path=$data->url;
    $this->actions=array();
    $this->formats=array();

    include( DB );

    $db=mysql_connect( $DB_HOST, $DB_USER, $DB_PASSWD );
    mysql_selectdb( $DB_DB, $db );
    $qry="select f.name, f.text, f.extensions
	  from flxFILEFORMATS f, flxLINKTYPECONDITIONSFILEFORMATS cf
	  where cf.linktype='".$data->linktype."'
	  and cf.eval_order='".$data->eorder."'
	  and f.name=cf.fname";
    $qh=mysql_query($qry, $db);
    while($row=mysql_fetch_array($qh))
    {
      $d=new LinkFileFormatData();
      list($d->name, $d->description, $ext)=$row;
      $d->extensions=array();
      if(trim($ext)!="")
	$d->extensions=explode("|", $ext);
      $format=new LinkFileFormat( $d );
      if($format==null) continue;
      array_push($this->formats, $format);
    }


    $qry="select el_code
          from flxLINKTYPECONDITIONSACTIONS
	  where linktype='".$data->linktype."'
          and eval_order=".$data->eorder."
          order by apply_order";
    $qh=mysql_query($qry, $db);
    while($row=mysql_fetch_array($qh))
    {
      $d=new LinkActionData();
      list($d->code)=$row;
      $action=new LinkAction($d);
      if(!$action) continue;
      array_push($this->actions, $action);
    }
    mysql_close($db);
  }

  function evaluate( $vars )
  {
    list($ok, $res)=$this->exec->execTree( $this->condition, $vars );
    if(!$ok) return array(-1, "Error evaluating condtion: $res");
    if($res=="FALSE") return array(0, "FALSE");
    if(count($this->actions)==0) return array(0, "NO ACTIONS");
    $v=new IntVar("LINK");
    $generated=false;
    foreach($this->actions as $action)
    {
      list($ok, $res)=$action->getResult( $vars );
      if(!$ok) return array(-1, "Error evaluating action: $res");
      $file=$this->file_path.$res;
      $url=$this->url_path.$res;
      if(count($this->formats)>0)
      {
	foreach($this->formats as $format)
	{
	  foreach($format->composeFilePaths( $file, $url ) as $i)
	  {
	    list($full_file, $full_url)=$i;
            $testfh=@ fopen($full_file, "r");
            if($testfh)
            {
	      $generated=true;
	      fclose($testfh);
	      $v->addValue($full_url);
              $v->addSFValue("url", $full_url);
              $v->addSFValue("file", $full_file);
              $v->addSFValue("format_id", $format->getName());
              $v->addSFValue("format_desc", $format->getDesc());
	      $v->inextValue();
            }
	  }
	}
      }
      if($generated===true) break;
      $testfh=@ fopen($file, "r");
      if($testfh)
      {
	$generated=true;
        fclose($testfh);
        $v->addValue($url);
        $v->addSFValue("url", $url);
        $v->addSFValue("file", $url);
	break;
      }
    }
    if($generated)
      return array(1, $v);
    return array(0, "NO LINK");

  }
}


//++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
//  Class: LinkFileFormatData (non-visible)
//  Purpose:
//  Attributes:
//  Methods:
//++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class LinkFileFormatData {

  var $name;
  var $description;
  var $extensions;

  function LinkFileFormatData(){}
}


//++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
//  Class: LinkFileFormat
//  Purpose:
//  Attributes:
//  Methods:
//++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class LinkFileFormat {

  var $description;
  var $name;
  var $extensions;
  
  function LinkFileFormat( $data )
  {
    if($data==null) return null;
    $this->name=$data->name;
    $this->description=$data->description;
    $this->extensions=$data->extensions;
  }

  function getName()
  {
    return $this->name;
  }

  function getDesc()
  {
    return $this->description;
  }

  function composeFilePaths( $base_path, $base_url )
  {
    $res=array();
    foreach($this->extensions as $ext)
    {
      $ext=trim($ext);
      if($ext=="") continue;
      array_push( $res, array($base_path.".".$ext, $base_url.".".$ext) );
    }
    return $res;
  }
}


//++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
//  Class: LinkConditionEXT (implements LinkCondition)
//  Purpose:
//  Attributes:
//  Methods:
//++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class LinkConditionEXT {
  
  var $condition;
  var $action;
  var $exec;

  function LinkConditionEXT( $data )
  {
    if($data==null) return null;
    $this->exec=new AELExecutor();
    list($ok, $msg)=$this->exec->checkCode( $data->code );
    if(!$ok) return null;
    $this->condition=$msg;
    
    include( DB );

    $db=mysql_connect( $DB_HOST, $DB_USER, $DB_PASSWD );
    mysql_selectdb( $DB_DB, $db );
    $qry="select el_code
	  from flxLINKTYPECONDITIONSACTIONS
	  where linktype='".$data->linktype."'
	  and eval_order=".$data->eorder."
	  order by apply_order";
    $qh=mysql_query($qry, $db);
    $d=new LinkActionData();
    list($d->code)=mysql_fetch_array($qh);
    mysql_close($db);
    if(!$d->code) return null;
    if(!($this->action=new LinkAction($d))) return null;
  }

  function evaluate( $vars )
  {
    list($ok, $res)=$this->exec->execTree( $this->condition, $vars );
    if(!$ok) return array(-1, "Error evaluating condtion: $res");
    if($res=="FALSE") return array(0, "FALSE");
    list($ok, $res)=$this->action->getResult( $vars );
    if(!$ok) return array(-1, "Error evaluating action: $res");
    $v=new IntVar("LINK");
    $v->addValue($res);
    $v->addSFValue("url", "$res");
    $v->inextValue();
    return array(1, $v);
  }

}

//++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
//  Class: LinkActionData (non-visible)
//  Purpose:
//  Attributes:
//  Methods:
//++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class LinkActionData {
  var $code;

  function LinkActionData(){}
}

//++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
//  Class: LinkAction
//  Purpose:
//  Attributes:
//  Methods:
//++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class LinkAction {
  
  var $action;
  var $exec;

  function LinkAction($data)
  {
    if($data==null) return null;
    $this->exec=new AELExecutor();
    list($ok, $msg)=$this->exec->checkCode( $data->code );
    if(!$ok) return null;
    $this->action=$msg;
  }

  function getResult($vars)
  {
    return $this->exec->execTree( $this->action, $vars );
  }

}

//++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
//  Class: LinkResolver
//  Purpose:
//  Attributes:
//  Methods:
//++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class LinkResolver {

  var $db;
  var $a;

  var $links;

  function LinkResolver() {
    $this->links=array();
  }

  function & getInstance()
  {
    static $instance;
    if(!isset($instance))
    {
      $instance=new LinkResolver();
    }
    return $instance;
  }

  function getLink($type)
  {
    $type=strtoupper(trim($type));
    if(isset($this->links[$type]))
    {
      return $this->links[$type];
    }
    else
    {
      include( DB );

      $db=mysql_connect( $DB_HOST, $DB_USER, $DB_PASSWD );
      mysql_selectdb( $DB_DB, $db );
      $qry="select linktype
	    from flxLINKTYPES
	    where linktype='$type'";
      $qh=mysql_query($qry);
      if(mysql_num_rows($qh)!="1") return null;
      mysql_close($db);
      $link=new Link($type);
      if($link==null) return null;
      $this->links[$type]=$link;
      return $link;
    }
  }

  function destroy()
  {
    //mysql_close( $this->db );
  }

  function checkLink( $linktype, $params ) { 
    $l=$this->getLink( $linktype );
    if($l==null) return 0;
    return $l->check($params);
  }

  function solveLink( $linktype, $params ) {
    $l=$this->getLink($linktype);
    if($l==null) return array(0, "Incorrect link");
    list($ok, $res)=$l->solve($params);
    if(!$ok) return array(0, $res);
    return array(1, $link_url, $res);
  }

}//end class

?>
