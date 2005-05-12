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
//  File: AEvalLan.inc (flexElink core)
//  Classes: 	LAEvalLan
//  		AELInterpreter
//  		AELNode
//  		AELAtribs
//  		AEvalLan
//  		AELExecutor
//		
//  Requires: FormatRetriever, UDFRetriever, KBRetriever
//  Included: 	core/FormatRetriever.inc
//		core/UDFRetriever.inc
//		core/KBRetriever.inc
//		general.inc
//		
//		
//==========================================================================

  include_once(FORMAT_RETRIEVER);
  include_once(UDF_RETRIEVER);
  include_once(KB_RETRIEVER);

  include_once(FUNCTION_LIB);

//++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
//  Class: LAEvalLan
//  Purpose:
//  Attributes:
//  Methods:
//++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

  //Constants that define lexical categories
  define(LAEL_NONE, -1);
  define(LAEL_LITERAL, 0);
  define(LAEL_VAR, 2);
  define(LAEL_OPAR, 6);
  define(LAEL_CPAR, 7);
  define(LAEL_END, 8);
  define(LAEL_FORALL, 10);
  define(LAEL_FUNCTION, 13);
  define(LAEL_COMA, 14);
  define(LAEL_NOT, 15);
  define(LAEL_COP, 16);
  define(LAEL_LOP, 17);
  define(LAEL_OBRACE, 18);
  define(LAEL_CBRACE, 19);
  define(LAEL_IF, 20);
  define(LAEL_ELSE, 21);
  define(LAEL_DOT, 22);
  define(LAEL_FORMAT, 23);
  define(LAEL_LINK, 24);
  define(LAEL_KB, 25);
  define(LAEL_COUNT, 26);


  class LAEvalLan
  {
    var $text;
    var $pos;

    function LAEvalLan( $text )
    {
      $this->text=$text;
      $this->pos=0;
    }

    function nextItem($debug=0)
    {
      $cat=LAEL_NONE;
      $lex="";
      $state=0;

      while($state>=0)
      {
	if($this->pos>strlen($this->text))
	{
	  $cat=LAEL_END;
	  $lex="";
	  break;
	}
	$cchar=$this->text[$this->pos];
	switch($state)
	{
	  case 0:
	    if($cchar=='"')
	      $state=1;
            elseif($cchar=='$')
	      $state=5;
            elseif($cchar=='(')
	    {
	      $cat=LAEL_OPAR;
	      $state=-1;
	    }
	    elseif($cchar==')')
	    {
	      $cat=LAEL_CPAR;
	      $state=-1;
	    }
	    elseif($cchar==',')
	    {
	      $cat=LAEL_COMA;
	      $state=-1;
	    }
	    elseif($cchar=='{')
	    {
	      $cat=LAEL_OBRACE;
	      $state=-1;
	    }
	    elseif($cchar=='}')
	    {
	      $cat=LAEL_CBRACE;
	      $state=-1;
	    }
	    elseif($cchar=='.')
	    {
	      $cat=LAEL_DOT;
	      $state=-1;
	    }
	    elseif($cchar=='!')
	    {
	      $lex.=$cchar;
	      $state=7;
	    }
	    elseif((($cchar=='&')&&($this->text[$this->pos+1]=='&'))||
	           (($cchar=='|')&&($this->text[$this->pos+1]=='|')))
	    {
	      $lex=$cchar.$this->text[$this->pos+1];
	      $this->pos++;
	      $cat=LAEL_LOP;
	      $state=-1;
	    }
	    elseif($cchar=='=')
	    {
	      $cat=LAEL_COP;
              $lex=$cchar;
	      $state=-1;
	    }
	    elseif(($cchar=='>')||($cchar=='<'))
	    {
	      $cat=LAEL_COP;
              $lex=$cchar;
	      if($this->text[$this->pos+1]=="=")
	      {
		$lex.="=";
		$this->pos++;
	      }
	      $state=-1;
	    }
	    elseif((($cchar>='a')&&($cchar<='z'))||
		   (($cchar>='A')&&($cchar<='Z'))||
		   (($cchar>='0')&&($cchar<='9')))
            {
	      $lex.=$cchar;
	      $state=6;
	    }

            $this->pos++;
            break;

	  case 7:
	    if($cchar=='=')
	    {
	      $cat=LAEL_COP;
	      $lex.=$cchar;
              $state=-1;
	      $this->pos++;
            }
	    else
	    {
	      $cat=LAEL_NOT;
	      $state=-1;
	    }

	    break;
	  case 6:
	    if( (($cchar>='a')&&($cchar<='z'))||(($cchar>='A')&&($cchar<='Z'))||
		(($cchar>='0')&&($cchar<='9'))||($cchar=='_')||($cchar=='.') )
            {
	      $lex.=$cchar;
	      $this->pos++;
	    }
	    else
	    {
	      $lex=strtoupper($lex);
	      if($lex=="FORALL")
		$cat=LAEL_FORALL;
              elseif($lex=="IF")
		$cat=LAEL_IF;
              elseif($lex=="ELSE")
		$cat=LAEL_ELSE;
              elseif($lex=="FORMAT")
	        $cat=LAEL_FORMAT;
              elseif($lex=="LINK")
	        $cat=LAEL_LINK;
              elseif($lex=="KB")
	        $cat=LAEL_KB;
              elseif($lex=="COUNT")
	        $cat=LAEL_COUNT;
              else
	        $cat=LAEL_FUNCTION;
	      $state=-1;
	    }
	    break;
	  case 5:
	    if( (($cchar>='a')&&($cchar<='z'))||(($cchar>='A')&&($cchar<='Z'))||
		(($cchar>='0')&&($cchar<='9'))||($cchar=='_') )
            {
	      $lex.=$cchar;
	      $this->pos++;
	    }
	    else
	    {
	      $cat=LAEL_VAR;
	      $lex=strtoupper($lex);
	      $state=-1;
            }
	    break;
          
	  case 1:
	    if($cchar!='"')
	    {
	      if(($cchar=='\\')&&($this->text[$this->pos+1]=='"'))
	      {
		$lex.="\"";
		$this->pos++;
	      }
	      else
		$lex.=$cchar;
	    }
	    else
	    {
	      $cat=LAEL_LITERAL;
	      $state=-1;
	    }
	    $this->pos++;
	    break;
	  default:
	    break;
	}
      }
      return array($cat, $lex);
    }

  }//end class: LAEvalLan

//++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
//  Class: AELInterpreter
//  Purpose:
//  Attributes:
//  Methods:
//++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
  
  define(SCEL_VAR,0);
  define(SCEL_LITERAL,1);
  define(SCEL_FUNCTION, 2);
  define(SCEL_FORALL, 3);
  define(SCEL_IF, 4);
  define(SCEL_OR, 5);
  define(SCEL_AND, 6);
  define(SCEL_EQUAL, 7);
  define(SCEL_DIFFERENT, 8);
  define(SCEL_NOT, 9);
  define(SCEL_CONCAT, 11);
  define(SCEL_SUBFIELD, 12);
  define(SCEL_FORMAT, 13);
  define(SCEL_LINK, 14);
  define(SCEL_PARAMS, 15); //Not a Semantic cathegory, just a mark one
  define(SCEL_KB, 16);
  define(SCEL_COUNT, 17);

  class AELInterpreter
  {
    var $vars;
    var $format_ret;
    var $udf_ret;
    var $kb_ret;
    var $link_res;
    var $first;
    var $last;

    function AELInterpreter( $vars )
    {
      $this->vars=$vars;
      $this->format_ret=& FormatRetriever::getInstance();
      $this->udf_ret=& UDFRetriever::getInstance();
      $this->kb_ret=& KBRetriever::getInstance();
      $this->link_res=& LinkResolver::getInstance();
      $this->first=1;
      $this->last=0;
    }

    function interpret( & $node, $curr_var="" )
    {
      $str=""; //Will contain the son built string
      //----------------------
      // SCEL_LITERAL
      //----------------------
      if($node->cat==SCEL_LITERAL)
      {
        $str=$node->lex;
      }
      //----------------------
      // SCEL_VAR
      //----------------------
      elseif($node->cat==SCEL_VAR)
      {
	if($node->hasSons())
	{
	  //Only can have a SF son, so we should get its value from the
	  //  internal vars
	  $str=$this->vars->getSFValue($node->lex, $node->sons[0]->lex);
	}
        else
        {
	  $str=$this->vars->getValue($node->lex);
	}
      }
      //----------------------
      // SCEL_FUNCTION
      //----------------------
      elseif($node->cat==SCEL_FUNCTION)
      {
        $params=array();
        foreach($node->sons as $son)
	{
          $value=$this->interpret( $son, $curr_var );
	  array_push($params, $value);
	}
/*
	$last=1;
	$first=0;
	if($curr_var!="")
        {
          $last=$this->vars->varExist($curr_var)&&
		$this->vars->lastValue($curr_var);
          $first=$this->vars->varExist($curr_var)&&
		 $this->vars->firstValue($curr_var);
        }
*/
	$first=$this->first;
	$last=$this->last;
	list($ok, $str)=$this->udf_ret->execute( $node->lex, 
						 $params, 
						 $last, 
						 $first);
      }
      //----------------------
      // SCEL_CONCAT
      //----------------------
      elseif($node->cat==SCEL_CONCAT)
      {
        foreach($node->sons as $son)
	{
	  $str.=$this->interpret( $son, $curr_var );
        }
      }
      //----------------------
      // SCEL_EQUAL, SCEL_DIFERENT
      //----------------------
      elseif(($node->cat==SCEL_EQUAL)||($node->cat==SCEL_DIFFERENT))
      {
        $val1=$this->interpret( $node->sons[0], $curr_var );
	$val2=$this->interpret( $node->sons[1], $curr_var );
	$str="FALSE";
	if(($node->cat==SCEL_EQUAL)&&($val1==$val2))
	  $str="TRUE";
	elseif(($node->cat==SCEL_DIFFERENT)&&($val1!=$val2))
	  $str="TRUE";
      }
      //----------------------
      // SCEL_AND, SCEL_OR
      //----------------------
      elseif(($node->cat==SCEL_AND)||($node->cat==SCEL_OR))
      {
        $temp=$this->interpret( $node->sons[0], $curr_var );
        
        if(($node->cat==SCEL_AND)&&($temp=="FALSE"))
	{ 
	  $str="FALSE";
        }
	elseif(($node->cat==SCEL_OR) &&($temp=="TRUE"))
	{
	  $str="TRUE";
	}
	else
	{
	  $str=$this->interpret( $node->sons[1], $curr_var );
        }
      }
      //----------------------
      // SCEL_KB
      //----------------------
      elseif($node->cat==SCEL_KB)
      {
	$kb_name=$node->sons[0]->lex;
        $key=$this->interpret( $node->sons[1], $curr_var );
	
	//$str=getKBValue( $kb_name, $key );
	$str=$this->kb_ret->getValue( $kb_name, $key );
      }
      //----------------------
      // SCEL_IF
      //----------------------
      elseif($node->cat==SCEL_IF)
      {
        $temp=$this->interpret( $node->sons[0], $curr_var );
	if($temp=="TRUE")
	{
	  $str=$this->interpret( $node->sons[1], $curr_var );
	}
	else
	{
	  if($node->sons[2])
             $str=$this->interpret( $node->sons[2], $curr_var );
	}
      }
      //----------------------
      // SCEL_LINK
      //----------------------
      elseif($node->cat==SCEL_LINK)
      {
	//First, get the link type which is specified in the first son
	$linktype=$node->sons[0]->lex;
	//Then let's have the param values which are specified by a PARAMS node
	$params=array();
	$tparams=$node->sons[1]->sons;
	reset($tparams);
	while($temp=current($tparams))
	{
	  $pv=$this->interpret( $temp, $curr_var );
	  array_push($params, $pv);
	  next($tparams);
	}
	//Now call the linkresolver to solve the link
	list($ok, $link, $linkvar)=$this->link_res->solveLink( $linktype, 
	  						       $params );
	if($ok)
	{
	  $this->vars->add($linkvar);
	  $str=$this->interpret( $node->sons[2], $curr_var );
          $this->vars->remove("LINK");
        }
        else
	{
	  if($node->sons[3]!=null)
	  {
	    $str=$this->interpret( $node->sons[3], $curr_var );
	  }
        }
      }
      //----------------------
      // SCEL_FORALL
      //----------------------
      elseif($node->cat==SCEL_FORALL)
      {
        $varname=$node->lex;
	$sfname="";
	if($node->sons[0]!=null)
	{
	  $sfname=$node->sons[0]->lex;
        }
	$maxiter=-1;
	if($node->sons[1]!=null)
	{
	  $maxiter=$node->sons[1]->lex; 
	}
	if($this->vars->vreset($varname))
	{
	  if(!$this->vars->isEmpty($varname))
	  {
	    $numvalues=$this->vars->countValues($varname, $sfname);
	    $str="";
	    $morevalues=1;
	    if($sfname!="")
	      $morevalues=$this->vars->vfirstSFValue($varname, $sfname);
            $iter=0;
	    while($morevalues)
	    {
	      $iter++;
	      $this->first=0;
	      if($iter==1) $this->first=1;
	      $this->last=0;
	      if(($iter==$numvalues) ||
		 (($maxiter>=0) && ($iter>=$maxiter)))
		$this->last=1;
       	      $str.=$this->interpret( $node->sons[2], $varname );
	      if(($maxiter>=0)&&($iter>=$maxiter))
		break;
	      if($sfname!="")
	        $morevalues=$this->vars->vnextSFValue($varname, $sfname);
              else
	        $morevalues=$this->vars->vnextvalue($varname);
	    }
	    $this->vars->vreset($varname);
	  }
	}
      }
      //----------------------
      // SCEL_COUNT
      //----------------------
      elseif($node->cat==SCEL_COUNT)
      {
	$sf="";
	if($node->sons[0]!=null)
	{
	  $sf=$node->sons[0]->lex;
	}
	$str=$this->vars->countValues($node->lex, $sf);
      }
      //----------------------
      // SCEL_NOT
      //----------------------
      elseif($node->cat==SCEL_NOT)
      {
        $temp=$this->interpret( $node->sons[0], $curr_var );
	$str="TRUE";
	if($temp=="TRUE") 
	  $str="FALSE";
      }
      //----------------------
      // SCEL_FORMAT
      //----------------------
      elseif($node->cat==SCEL_FORMAT)
      {
        $fname=$this->interpret( $node->sons[0], $curr_var );
	//call to the format retriever in order to get the corresponding format
        list($ok, $ftree)=$this->format_ret->getParsedFormat( $fname );
	if($ok)
	{
	  $str=$this->interpret( $ftree, $curr_var );
	}
      }
      return $str;

    }

  }//end class: AELInterpreter

//++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
//  Class: AELNode
//  Purpose:
//  Attributes:
//  Methods:
//++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

  class AELNode
  {
    var $cat;
    var $lex;
    var $sons;

    function AELNode($cat, $lex="")
    {
      $this->cat=$cat;
      $this->lex=$lex;
      $this->sons=array();
    }

    function addSon( $son )
    {
      if($son)
        array_push( $this->sons, $son );
    }
    
    function addSonNoCheck( $son )
    {
      array_push( $this->sons, $son );
    }

    function hasSons()
    {
      return count($this->sons);
    }
    
    function debug($prefix="")
    {
      print "$prefix Node(Cat: <b>".$this->cat."</b>--Lex: <b>".$this->lex."</b>)<br>";
      foreach($this->sons as $son)
      {
	print $prefix.$this->cat."--".$this->lex." SON <br>";
	$son->debug($prefix."..");
      }
    }
  }//end clas: AELNode

//++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
//  Class: AELAtribs
//  Purpose:
//  Attributes:
//  Methods:
//++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

  class AELAtribs 
  {
    var $void;
    function AELAtribs()
    {
      $this->void="";
    }
  }//end class: AELAtribs

//++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
//  Class: AEvalLan
//  Purpose:
//  Attributes:
//  Methods:
//++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

  class AEvalLan
  {
    var $lexa;
    var $cat;
    var $text;
    var $code;
    var $debug;
    var $vars;
    var $tree;
    var $udf_ret;
    var $format_ret;
    
    var $text_error;
    var $notforall;
    var $vars_needed;

    var $formats_forbidden;

    function AEvalLan()
    {
      $this->tree=null;

      $this->udf_ret=& UDFRetriever::getInstance();
      $this->format_ret=& FormatRetriever::getInstance();

      $this->formats_forbidden = array();
    }

    function vars_needed( $text, $debug=false )
    {
      $this->debug=$debug;
      $this->code=$text;
      $this->notforall=0;
      $this->vars_needed=array();
      $this->lexa=new LAEvalLan( $this->code );
      list($this->cat, $this->text)=$this->lexa->nextItem();
      $ats=new AELAtribs();
      if($this->auxS( $ats ))
      {
	$this->tree=$ats->tree;
	return array(1, $this->vars_needed);
      }
      else
      {
	$this->tree=null;
	$this->text_error.="(at char ".$this->lexa->pos.")<br>";
	$cad=substr($this->code, 0, $this->lexa->pos-1);
	$this->text_error.="<font color=\"black\">".htmlspecialchars($cad)."</font>";
	return array(0, $this->text_error);
      }
    }

    function notAllowFormats( $ff )
    {
       if(!is_array($ff)) {
         $this->formats_forbidden = array( $ff );
       }
       else {
         $this->formats_forbidden = $ff;
       }
    }
    
    function parse( $text )
    {
      $this->debug=$debug;
      $this->code=$text;
      $this->notforall=0;
      $this->vars_needed=array();

      $this->lexa=new LAEvalLan( $this->code );
      list($this->cat, $this->text)=$this->lexa->nextItem();
      $ats=new AELAtribs();
      if($this->auxS( $ats ))
      {
	$this->tree=$ats->tree;
	return array(1, $this->tree);
      }
      else
      {
	$this->tree=null;
	$this->text_error.="(at char ".$this->lexa->pos.")<br>";
	$cad=substr($this->code, 0, $this->lexa->pos-1);
	$this->text_error.="<font color=\"black\">".text2HTML($cad)."</font>";
	return array(0, $this->text_error);
      }
    }
    
    function getParsedTree( $text )
    {
      list($ok, $msg)=$this->parse( $text );
      if($ok)
      {
	return array(1, $this->tree);
      }
      else
      {
	return array(0, $msg);
      }
    }

    function execute( $vars )//, & $format_ret, & $udf_ret, & $kb_ret )
    {
      if(!$this->tree)
      {
	return array(0, "There isn't a previous compilation");
      }

      $err="";
      $nulo=null;
      $int=new AELInterpreter( $vars );
      $str=$int->interpret( $this->tree );
      $this->kb_ret->print_acc();

      if($err!="")
	  return array(0, "Error interpreting: $err");
      else
	  return array(1, $str);
    }

    function newexecute( $text, $vars, $debug=false )
    {
      $this->code=$text;
      $this->notforall=0;
      $this->vars_needed=array();
      $this->lexa=new LAEvalLan( $this->code );
      list($this->cat, $this->text)=$this->lexa->nextItem();
      $ats=new AELAtribs();
      if($this->auxS( $ats ))
      {
	$this->tree=$ats->tree;
        $format_ret=new FormatRetriever();
	list($err, $str)=$ats->tree->getResult($vars, "", $format_ret);
	if($err!="")
	{
	  return array(0, "Error interpreting: $err");
	}
	else
	{
	  return array(1, $str);
        }
      }
      else
      {
	$this->text_error.="(at char ".$this->lexa->pos.")";
	return array(0, $this->text_error);
      }
    }

    function auxS( & $aS )
    {
      //<S>-><E>end
      if(in_array($this->cat, array(LAEL_NOT, LAEL_VAR, 
			LAEL_LITERAL, LAEL_FUNCTION, LAEL_OPAR, LAEL_FORALL,
			LAEL_IF, LAEL_FORMAT, LAEL_LINK, LAEL_KB, LAEL_COUNT)))
      {
        $aE=new AELAtribs();
	if($this->auxE( $aE ))
	{
	  if($this->cat==LAEL_END)
	  {
	    $aS->tree=$aE->tree;
	    $aS->type=$aE->type;
	    return 1;
	  }
	}
      }
      //<S>->end
      elseif($this->cat==LAEL_END)
      {
        $aS->tree=null;
	$aS->type="STRING";
	return 1;
      }
      return 0;
    }

    function auxE( & $aE )
    {
      //<E>-><T><Ep>
      if(in_array($this->cat, array(LAEL_NOT, LAEL_VAR, LAEL_LITERAL, 
			LAEL_FUNCTION, LAEL_OPAR, LAEL_FORALL, LAEL_IF, 
			LAEL_FORMAT, LAEL_LINK, LAEL_KB, LAEL_COUNT)))
      {
        $aT=new AELAtribs();
	if($this->auxT( $aT ))
	{
	  $aEp=new AELAtribs();
	  $aEp->h=$aT->tree;
          $aEp->th=$aT->type;
	  if($this->auxEp( $aEp ))
	  {
	    $aE->type=$aEp->ts;
	    $aE->tree=$aEp->s;
	    return 1;
          }
	}
      }
      else
      {
	$this->text_error="Expresion expected";
      }
      
      return 0;
    }

    
    function auxEp( & $aEp )
    {
      //<Ep>->lop<T><Ep>
      if($this->cat==LAEL_LOP)
      {
	if($this->text=="&&")
	  $tempcat=SCEL_AND;
        else
	  $tempcat=SCEL_OR;
        list($this->cat, $this->text)=$this->lexa->nextItem();
        $aT=new AELAtribs();
	if($this->auxT( $aT ))
	{
	  $temp=new AELNode( $tempcat );
	  $temp->addSon( $aEp->h );
	  $temp->addSon( $aT->tree );
	  $aEp1=new AELAtribs();
	  $aEp1->h=$temp;
	  if(($aEp->th!="BOOL")&&($aT->type!="BOOL"))
	  {
	    $this->text_error="Logical operations(&&,||) can only be applied over logical expressions";
	    return 0;
	  }
	  $aEp1->th="BOOL";

	  if($this->auxEp( $aEp1 ))
	  {
	    $aEp->s=$aEp1->s;
	    $aEp->ts=$aEp1->ts;
	    return 1;
	  }
	}
      }
      //<Ep>->lambda
      elseif(in_array($this->cat, array(LAEL_END, LAEL_CPAR, LAEL_COMA,
				LAEL_CBRACE)))
      {
        $aEp->s=$aEp->h;
	$aEp->ts=$aEp->th;
        return 1;
      }
      
      return 0;
    }

    function auxT( & $aT )
    {
      //<T>-><F><Tp>
      if(in_array($this->cat, array(LAEL_NOT, LAEL_VAR, LAEL_LITERAL, 
			LAEL_FUNCTION, LAEL_OPAR, LAEL_FORALL, LAEL_IF, 
			LAEL_FORMAT, LAEL_LINK, LAEL_KB, LAEL_COUNT)))
      {
        $aF=new AELAtribs();
        if($this->auxF( $aF ))
	{
	  $aTp=new AELAtribs();
	  $aTp->h=$aF->tree;
          $aTp->th=$aF->type;
	  if($this->auxTp( $aTp ))
	  {
	    $aT->tree=$aTp->s;
	    $aT->type=$aTp->ts;
	    return 1;
	  }
	}
      }

      return 0;
    }

    function auxTp( & $aTp )
    {
      //<Tp>->cop<F><Tp>
      if($this->cat==LAEL_COP)
      {
	if($this->text=="=")
	  $tempcat=SCEL_EQUAL;
        else
	  $tempcat=SCEL_DIFFERENT;
        list($this->cat, $this->text)=$this->lexa->nextItem();
        $aF=new AELAtribs();
	if($this->auxF( $aF ))
	{
	  if(($aTp->th!="STRING")&&($aF->type!="STRING"))
	  {
	    $this->text_error="Comparison operations(=,!=) can only be applied over STRING expressions";
	    return 0;
	  }
	  $temp=new AELNode( $tempcat );
	  $temp->addSon( $aTp->h );
	  $temp->addSon( $aF->tree );
	  $aTp1=new AELAtribs();
	  $aTp1->h=$temp;
	  $aTp1->th="BOOL";
	  if($this->auxTp( $aTp1 ))
	  {
	    $aTp->s=$aTp1->s;
	    $aTp->ts=$aTp1->ts;
	    return 1;
	  }
	}
      }
      //<Tp>-><F><Tp>
      elseif(in_array($this->cat, array(LAEL_NOT, LAEL_VAR, LAEL_LITERAL, 
			LAEL_FUNCTION, LAEL_OPAR, LAEL_FORALL, LAEL_IF, 
			LAEL_FORMAT, LAEL_LINK, LAEL_KB, LAEL_COUNT)))
      {
        $aF=new AELAtribs();
        if($this->auxF( $aF ))
	{
	  if(($aTp->th!="STRING")&&($aF->type!="STRING"))
	  {
	    $this->text_error="Can only concatenate STRING expressions";
	    return 0;
	  }
	  $temp=new AELNode( SCEL_CONCAT );
	  $temp->addSon( $aTp->h );
	  $temp->addSon( $aF->tree );
	  $aTp1=new AELAtribs();
	  $aTp1->h=$temp;
	  $aTp1->th="STRING";
	  if($this->auxTp( $aTp1 ))
	  {
	    $aTp->s=$aTp1->s;
	    $aTp->ts=$aTp1->ts;
	    return 1;
	  }
	}
      }
      //<Tp>->lambda
      elseif(in_array($this->cat, array(LAEL_LOP, LAEL_END, LAEL_CPAR, 
			LAEL_COMA, LAEL_CBRACE)))
      {
        $aTp->s=$aTp->h;
        $aTp->ts=$aTp->th;
        return 1;
      }
      
      return 0;
    }

    function auxF( & $aF )
    {
      //<F>->!<B>
      if($this->cat==LAEL_NOT)
      {
        list($this->cat, $this->text)=$this->lexa->nextItem();
	$aB=new AELAtribs();
	if($this->auxB( $aB ))
	{
	  if($aB->type!="BOOL")
	  {
	    $this->text_error="Cannot apply a NOT over a string expresion";
	    return 0;
          }
	  $aF->type="BOOL";
	  $temp=new AELNode( SCEL_NOT );
	  $temp->addSon( $aB->tree );
	  $aF->tree=$temp;
	  return 1;
	}
      }
      //<F>-><B>
      elseif(in_array($this->cat, array(LAEL_VAR, LAEL_LITERAL, LAEL_FUNCTION,
			LAEL_OPAR, LAEL_FORALL, LAEL_IF, LAEL_FORMAT, 
			LAEL_LINK, LAEL_KB, LAEL_COUNT)))
      {
	$aB=new AELAtribs();
	if ($this->auxB( $aB ))
	{
	  $aF->tree=$aB->tree;
	  $aF->type=$aB->type;
	  return 1;
	}
      }

      return 0;
    }

    function auxB( & $aB )
    {
      //<B>->var
      if($this->cat==LAEL_VAR)
      {
	$aB->tree=new AELNode( SCEL_VAR, $this->text );
        list($this->cat, $this->text)=$this->lexa->nextItem();
	$aSF=new AELAtribs();
        if($this->auxSF( $aSF ))
	{
	  $aB->tree->addSon( $aSF->tree );
	  $aB->type="STRING";
	  return 1;
	}
      }
      //<B>->literal
      elseif($this->cat==LAEL_LITERAL)
      {
	$aB->tree=new AELNode( SCEL_LITERAL, $this->text );
        list($this->cat, $this->text)=$this->lexa->nextItem();
	$aB->type="STRING";
        return 1;
      }
      //<B>->function(<LP>)
      elseif($this->cat==LAEL_FUNCTION)
      {
	$aB->tree=new AELNode( SCEL_FUNCTION, $this->text );
	$fname=$this->text;
        list($this->cat, $this->text)=$this->lexa->nextItem();
	if($this->cat==LAEL_OPAR)
	{
          list($this->cat, $this->text)=$this->lexa->nextItem();
	  if($this->auxLP( $aB ))
	  {
	    list($ok, $msg)=$this->udf_ret->validate( $fname, count($aB->tree->sons) );
	    if(!$ok)
	    {
	      $this->text_error=$msg;
	      return 0;
	    }
	    if($this->cat==LAEL_CPAR)
	    {
              list($this->cat, $this->text)=$this->lexa->nextItem();
	      //By the time, a function will allways return a STRING value.
	      //  If necessary we could distinguish between STRING or BOOL 
	      //  functions
	      $aB->type="STRING";
	      return 1;
	    }
	    else
	      $this->text_error="There is a ')' missing";
	  }
	}
	else
	  $this->text_error="Functions must be followed by '('";
      }
      //<B>->format( <E> )
      elseif($this->cat==LAEL_FORMAT)
      {
	    $aB->tree=new AELNode( SCEL_FORMAT );
        list($this->cat, $this->text)=$this->lexa->nextItem();
	    if($this->cat==LAEL_OPAR)
	    {
          list($this->cat, $this->text)=$this->lexa->nextItem();
	      $aE=new AELAtribs();
	      if($this->auxE( $aE ))
	      {
	        if($aE->type!="STRING")
	        {
	          $this->text_error="FORMAT type has to be a must be a STRING";
	          return 0;
	        }
            if($aE->tree->cat == SCEL_LITERAL)
            {
              if(in_array( strtoupper($aE->tree->lex), $this->formats_forbidden ))
              {
                $this->text_error="Recursive format call";
                return 0;
              }
            }

            
	        $aB->tree->addSon( $aE->tree );
	        if($this->cat==LAEL_CPAR)
	        {
              list($this->cat, $this->text)=$this->lexa->nextItem();
	          $aB->type="STRING";
	          return 1;
            }
	      }
        }
      }
      //<B>->link( literal, <LP> )
      elseif($this->cat==LAEL_LINK)
      {
	if($this->notlink)
	{
	  $this->text_error="LINK statements cannot be nested";
	  return 0;
	}
	$aB->tree=new AELNode( SCEL_LINK );
        list($this->cat, $this->text)=$this->lexa->nextItem();
	if($this->cat==LAEL_OPAR)
	{
          list($this->cat, $this->text)=$this->lexa->nextItem();
	  if($this->cat==LAEL_LITERAL)
	  {
	    //Check if the link type exists
	    //Add the literal as first son of the tree
	    $aB->tree->addSon(new AELNode( SCEL_LITERAL, $this->text ));
            list($this->cat, $this->text)=$this->lexa->nextItem();
	    if($this->cat==LAEL_COMA)
	    {
              list($this->cat, $this->text)=$this->lexa->nextItem();
	      $this->notlink=1;
	      $temp=new AELAtribs();
	      $temp->tree=new AELNode( SCEL_PARAMS );
	      if($this->auxLP( $temp ))
	      {
		$aB->tree->addSon( $temp->tree );
                if($this->cat==LAEL_CPAR)
		{
                  list($this->cat, $this->text)=$this->lexa->nextItem();
		  $aB->type="STRING";
		  if($this->cat==LAEL_OBRACE)
		  {
                    list($this->cat, $this->text)=$this->lexa->nextItem();
		    $aE=new AELAtribs();
		    if($this->auxE( $aE ))
		    {
		      if($aE->type!="STRING")
		      {
			$this->text_error="Actions inside a LINK statement must be STRING";
			return 0;
		      }
		      $aB->tree->addSon( $aE->tree );
		      if($this->cat==LAEL_CBRACE)
		      {
	                $this->notlink=0;
                        list($this->cat, $this->text)=$this->lexa->nextItem();
			$aEls=new AELAtribs();
			if($this->auxEls( $aEls ))
			{
			  $aB->tree->addSon( $aEls->tree );
		          return 1;
			}
			
                      }
		    }
		  }
		  else
		  {
	            $this->text_error="A '{' was expected";
	            return 0;
		  }
		}
	      }
	    }
	    else
	    {
	      $this->text_error="A ',' was expected";
	      return 0;
	      
	    }
	  }
	  else
	  {
	    $this->text_error="Link type has to be specified by a LITERAL in a LINK call";
	    return 0;
	  }
	}
	else
	{
	  $this->text_error="A '(' was expected after a LINK call";
	  return 0;
	}
      }
      //<B>->KB(literal, <E>)
      elseif($this->cat==LAEL_KB)
      {
	$aB->tree=new AELNode( SCEL_KB );
        list($this->cat, $this->text)=$this->lexa->nextItem();
	if($this->cat==LAEL_OPAR)
	{
          list($this->cat, $this->text)=$this->lexa->nextItem();
	  $aE=new AELAtribs();
	  if($this->auxE( $aE))
	  {
	    if($aE->type!="STRING")
	    {
	      $this->text_error="The key parameter has to be a STRING in a KB call";
	      return 0;
	    }
	    if($this->cat==LAEL_COMA)
	    {
              list($this->cat, $this->text)=$this->lexa->nextItem();
	      if($this->cat==LAEL_LITERAL)
	      {
		$aB->tree->addSon( new AELNode( SCEL_LITERAL, $this->text) );
		$aB->tree->addSon($aE->tree);
                list($this->cat, $this->text)=$this->lexa->nextItem();
		if($this->cat==LAEL_CPAR)
		{
                  list($this->cat, $this->text)=$this->lexa->nextItem();
		  $aB->type="STRING";
		  return 1;
		}
		else
		{
		  $this->text_error="A ')' was expected";
		  return 0;
		}
		
	      }
	      else
              {
		$this->text_error="KB name has to be specified by a LITERAL in a KB call";
		return 0;

	      }
	    }
	    else
	    {
	      $this->text_error="A ',' was expected after the key parameter in the KB call";
	      return 0;
	    }
	  }
	}
	else
	{
	  $this->text_error="A '(' was expected after a KB call";
	  return 0;
	}
      }
      //<B>->(<E>)
      elseif($this->cat==LAEL_OPAR)
      {
        list($this->cat, $this->text)=$this->lexa->nextItem();
	if($this->auxE( $aB ))
	{
	  if($this->cat==LAEL_CPAR)
	  {
            list($this->cat, $this->text)=$this->lexa->nextItem();
	    return 1;
	  }
	  else
	    $this->text_error="There is a ')' missing";
	}
      }
      //<B>->forall(var<SF>){<E>}
      elseif($this->cat==LAEL_FORALL)
      {
	if($this->notforall)
	{
	  $this->text_error="You cannot use forall into an evaluation zone";
	  return 0;
	}
        list($this->cat, $this->text)=$this->lexa->nextItem();
	if($this->cat==LAEL_OPAR)
	{
          list($this->cat, $this->text)=$this->lexa->nextItem();
	  if($this->cat==LAEL_VAR)
	  {
	    $aB->tree=new AELNode( SCEL_FORALL, $this->text );
            list($this->cat, $this->text)=$this->lexa->nextItem();
	    $aSF=new AELAtribs();
	    if($this->auxSF( $aSF ))
	    {
	      $aB->tree->addSonNoCheck( $aSF->tree );
	      $aNi=new AELAtribs();
	      if($this->auxNi( $aNi ))
	      {
	        $aB->tree->addSonNoCheck( $aNi->tree );
	        if($this->cat==LAEL_CPAR)
	        {
                  list($this->cat, $this->text)=$this->lexa->nextItem();
	          if($this->cat==LAEL_OBRACE)
	          {
                    list($this->cat, $this->text)=$this->lexa->nextItem();
		    $aE=new AELAtribs();
		    if($this->auxE( $aE ))
		    {
	              if($aE->type!="STRING")
	              {
	                $this->text_error="FORALL can only be applied over a STRING exression";
	                return 0;
	              }
		      if($this->cat==LAEL_CBRACE)
		      {
                        list($this->cat, $this->text)=$this->lexa->nextItem();
	                $aB->tree->addSon( $aE->tree );
		        $aB->type="STRING";
		        return 1;
		      }
	            }	
	          }
	        }
	      }
            } 
	  }
	  else
	  {
	    $this->text_error="A VARIABLE expected in the FORALL declaration";
	  }
	}
      }
      //<B>->if(<E>){<E>}<Els>
      elseif($this->cat==LAEL_IF)
      {
	$aB->tree=new AELNode( SCEL_IF );
        list($this->cat, $this->text)=$this->lexa->nextItem();
	if($this->cat==LAEL_OPAR)
	{
          list($this->cat, $this->text)=$this->lexa->nextItem();
	  $this->notforall++;
          $aE=new AELAtribs();
	  if($this->auxE( $aE ))
	  {
	    if($aE->type!="BOOL")
	    {
	      $this->text_error="IF condition must be a LOGIC expression";
	      return 0;
	    }
	    if($this->cat==LAEL_CPAR)
	    {
	      $aB->tree->addSon($aE->tree);
	      $this->notforall--;
              list($this->cat, $this->text)=$this->lexa->nextItem();
	      if($this->cat==LAEL_OBRACE)
	      {
                list($this->cat, $this->text)=$this->lexa->nextItem();
		$aE1=new AELAtribs();
		if($this->auxE( $aE1 ))
		{
	          if($aE1->type!="STRING")
	          {
	            $this->text_error="IF can only be applied over a STRING expression";
	            return 0;
	          }
		  if($this->cat==LAEL_CBRACE)
		  {
		    $aB->tree->addSon( $aE1->tree );
                    list($this->cat, $this->text)=$this->lexa->nextItem();
		    $aEls=new AELAtribs();
		    if($this->auxEls( $aEls ))
		    {
		      $aB->tree->addSon( $aEls->tree );
		      $aB->type="STRING";
		      return 1;
		    }
		  }
		}
	      }
	    }
	  }
	}
      }
      //<B>-> count( var <SF> )
      elseif($this->cat==LAEL_COUNT)
      {
        list($this->cat, $this->text)=$this->lexa->nextItem();
	if($this->cat==LAEL_OPAR)
        {
          list($this->cat, $this->text)=$this->lexa->nextItem();
	  if($this->cat==LAEL_VAR)
          {
	    $temp_var=$this->text;
            list($this->cat, $this->text)=$this->lexa->nextItem();
	    $aSF=new AELAtribs();
            if($this->auxSF( $aSF ))
	    {
	      if($this->cat==LAEL_CPAR)
	      {
                list($this->cat, $this->text)=$this->lexa->nextItem();
		$aB->tree=new AELNode(SCEL_COUNT, $temp_var);
	        $aB->tree->addSon( $aSF->tree );
	        $aB->type="STRING";
	        return 1;
	      }
	      else
	      {
	        $this->text_error="A ')' was expected after the COUNT call";
	      }
            }
          }
	  else
	  {
	    $this->text_error="A VARIABLE was expected inside the COUNT call";
	  }
	}
	else
	{
	  $this->text_error="A '(' expected after COUNT call";
	}
      }
      return 0;
    }

    function auxNi( & $aNi )
    {
      //<Ni>->,literal
      if($this->cat==LAEL_COMA)
      {
        list($this->cat, $this->text)=$this->lexa->nextItem();
        if($this->cat==LAEL_LITERAL)
	{
	  $aNi->tree=new AELNode( SCEL_LITERAL, $this->text );
          list($this->cat, $this->text)=$this->lexa->nextItem();
	  return 1;
	}
	else
	{
	  $this->text_error="A LITERAL was expected";
	}
      }
      //<Ni>->lambda
      elseif($this->cat==LAEL_CPAR)
      {
        $aNi->tree=null;
        return 1;
      }
      return 0;
    }

    function auxSF( & $aSF )
    {
      //<SF>->.function
      if($this->cat==LAEL_DOT)
      {
        list($this->cat, $this->text)=$this->lexa->nextItem();
	if($this->cat==LAEL_FUNCTION)
	{
          $aSF->tree=new AELNode( SCEL_SUBFIELD, $this->text );
          list($this->cat, $this->text)=$this->lexa->nextItem();
	  return 1; 
	}
	else
	{
	  $this->text_error="You have to specify the subfield";
	}
      }
      //<SF>->lambda
      elseif(in_array($this->cat, array( LAEL_COP, LAEL_NOT, LAEL_VAR, 
		LAEL_LITERAL, LAEL_FUNCTION, LAEL_OPAR, LAEL_FORALL, LAEL_IF,
		LAEL_LOP, LAEL_END, LAEL_CPAR, LAEL_CBRACE, LAEL_COMA, 
		LAEL_FORMAT, LAEL_LINK, LAEL_KB, LAEL_COUNT, LAEL_CPAR )))
      {
        $aSF->tree=null;
        return 1;
      }
    
      return 0;
    }

    function auxEls( & $aEls )
    {
      //<Els>->else{ <E> }
      if($this->cat==LAEL_ELSE)
      {
        list($this->cat, $this->text)=$this->lexa->nextItem();
        if($this->cat==LAEL_OBRACE)
	{
          list($this->cat, $this->text)=$this->lexa->nextItem();
	  $aE=new AELAtribs();
	  if($this->auxE( $aE ))
	  {
	    if($aE->type!="STRING")
	    {
	      $this->text_error="ELSE can only be applied over a STRING expression";
	       return 0;
	    }
	    $aEls->tree=$aE->tree;
	    if($this->cat==LAEL_CBRACE)
	    {
              list($this->cat, $this->text)=$this->lexa->nextItem();
	      return 1;
	    }
	  }
	}
      }
      //<Els>->lambda
      elseif(in_array($this->cat, array( LAEL_COP, LAEL_NOT, LAEL_VAR, 
		LAEL_LITERAL, LAEL_FUNCTION, LAEL_OPAR, LAEL_FORALL, LAEL_IF,
		LAEL_LOP, LAEL_END, LAEL_CPAR, LAEL_CBRACE, LAEL_COMA, 
		LAEL_FORMAT, LAEL_LINK, LAEL_KB, LAEL_COUNT )))
      {
        $aEls->tree=null;
	return 1;
      }
      return 0;
    }
    
    function auxLP( & $aLP )
    {
      //<LP>-><E><LPp>
      if(in_array($this->cat, array(LAEL_NOT, LAEL_VAR, LAEL_LITERAL, 
			LAEL_FUNCTION, LAEL_OPAR, LAEL_FORALL, LAEL_IF, 
			LAEL_FORMAT, LAEL_LINK, LAEL_KB, LAEL_COUNT)))
      {
        $aE=new AELAtribs();
	if($this->auxE( $aE ))
	{
	  $aLP->tree->addSon( $aE->tree );
	  $aLPp=new AELAtribs();
	  $aLPp->tree=$aLP->tree;
	  if($this->auxLPp( $aLPp ))
	  {
	    $aLP->tree=$aLPp->tree;
	    return 1;
	  }
	}
      }
      //<LP>->lambda
      elseif($this->cat==LAEL_CPAR)
      {
        return 1;
      }

      return 0;
    }

    function auxLPp( & $aLPp )
    {
      //<LPp>->,<LP>
      if($this->cat==LAEL_COMA)
      {
        list($this->cat, $this->text)=$this->lexa->nextItem();
	$aLP=new AELAtribs();
	$aLP->tree=$aLPp->tree;
	if($this->auxLP( $aLP ))
	{
	  $aLPp->tree=$aLP->tree;
	  return 1;
	}
      }
      //<LPp>->lambda
      elseif($this->cat==LAEL_CPAR)
      {
        return 1;
      }
    }
    
  }//end class: AEvalLan


//++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
//  Class: AELExecutor
//  Purpose:
//  Attributes:
//  Methods:
//++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

  class AELExecutor {
    var $link_res;

    function AELExecutor( $create_handlers=1 )
    { 
      $this->link_res=null;
    }

    function checkCode( $code )
    {
      $anz=new AEvalLan();
      list($ok, $msg)=$anz->parse( $code );
      unset($anz);
      return array($ok, $msg);
    }

    
    function execTree( $tree, $vars )
    {
      if($tree==null) return array(0, "Empty tree to interpret");
      $int=new AELInterpreter( $vars );
      $str=$int->interpret( $tree, $vars );
      unset($int);
      return array( 1, $str );
    }

    function execCode( $code, $vars )
    {
      $anz=new AEvalLan();
      $int=new AELInterpreter( $vars );
      list($ok, $tree)=$anz->parse( $code );
      unset($anz);
      if(!$ok)
	return array($ok, $tree);
      $str=$int->interpret( $tree, $vars );
      unset($int);
      return array( 1, $str );
    }

  }

?>
