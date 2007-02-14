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

//==========================================================================
//  File: KBRetriever.inc (flexElink core)
//  Classes:    KBRetriever
//  Requires: 
//  Includes: DB
//==========================================================================


//++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
//  Class: KBRetriever
//  Purpose: Encapsulates the retrieving of KB values defined in the FlexElink
//	consiguration DB. It implements an internal cache in order to minimize
//	database accesses and optimize performace. It follows the Singleton 
//	pattern for ensuring the existence of a single instance of this class
//  Attributes:
//	db -----------> Persistent MySQL connection
//	cache_tables -> Array for keeping in memory kb name-kb table
//		correspondence retrieved from the DB
//	cache_values -> Array for keeping in memory key-value correspondence 
//		for a certain KB and that have been already etrieved from the DB
//  Methods:
//	getInstance (static) --> returns an instance of this class assuring that
//		is unique
//	getValue --------------> returns the string value mapped for a given
//		key value in a given KB configured inseide the flexElink DB. In
//		case the key or KB don't exist, an empty string is retruned
//++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

  class KBRetriever
  {
    var $db;
    var $cache_tables;
    var $cache_values;

    function KBRetriever()
    {
      srand((float)microtime()*10000000);
      $this->cache_tables=array();
      $this->cache_values=array();

      include( DB );
      $this->db=mysql_pconnect( $DB_HOST, $DB_USER, $DB_PASSWD );
      mysql_selectdb( $DB_DB, $this->db );
      $qry="select kb_name, kb_table
            from flxKBS";
      $qh=mysql_query($qry, $this->db);
      while($row=mysql_fetch_array($qh))
      {
	list($kb_name, $kb_value)=$row;
	$this->cache_tables["$kb_name"]="$kb_value";
      }
    }

/*---------------------------------------------------------------------
  Method: getInstance
  Description: 
  Parameters:
  Return value: (KBRetriever)
---------------------------------------------------------------------*/
    function & getInstance()
    {
      static $instance;
      if(!isset($instance))
      {
	$instance=new KBRetriever();
      }
      return $instance;
    }
    
/*---------------------------------------------------------------------
  Method: getValue
  Description: 
  Parameters:
  	kb_name (String) --> KB identifier in flexElink database from which the 
		value is going to be extracted
	key (String) ------> Key value to search for inside the KB
  Return value: (String) Mapped value corresponding to the KB and key values
  	given
---------------------------------------------------------------------*/
    function getValue( $kb_name, $key )
    {
      if(!$this->db)
	return "";
      $kb_name=strtoupper(trim($kb_name));
      $kb_table=$this->cache_tables[$kb_name];
      if(!$kb_table)
      {
	return "";
      }
      $value=$this->cache_values["$kb_table##$key"];
      if($value=="")
      {
        $key=addslashes($key);
        $qry="select value from $kb_table where vkey='$key'";  
        $qh=mysql_query($qry, $this->db);  
        if(mysql_num_rows($qh)<1)  
          return "";  
        list($value)=mysql_fetch_array($qh);  
	if(count($this->cache_values)>100)
	{
	  $k=array_rand($this->cache_values);
	  unset($this->cache_values["$k"]);
	}
	$this->cache_values["$kb_table##$key"]=$value;
      }
      return $value;
    }
  }
?>
