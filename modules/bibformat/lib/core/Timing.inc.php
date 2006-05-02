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

  class Timing {
    var $timing_list;

    function Timing()
    {
      $this->timing_list=array();
    }

    function start( $tname )
    {
      $tname=strtoupper(trim($tname));
      list($sec, $usec)=explode(" ", microtime());
      $this->timing_list[$tname]=(float)$sec+(float)$usec;
      return $this->timing_list[$tname];
    }

    function end( $tname )
    {
      $tname=strtoupper(trim($tname));
      if(in_array($tname, array_keys($this->timing_list)))
      {
        list($sec, $usec)=explode(" ", microtime());
        $endts=(float)$sec+(float)$usec;
        $this->timing_list[$tname]= $endts-$this->timing_list[$tname];
      }
      else
      {
        $this->timing_list[$tname]=-1;
      }
      return $this->timing_list[$tname];
    }

    function debug()
    {
      print "<font size=\"2\" color=\"red\"><u>Timing</u></font><br>";
      foreach($this->timing_list as $tsname=>$tsvalue)
      {
	if($tsvalue>0)
	{
	  print "<font size=\"2\" color=\"red\">[$tsname]=$tsvalue sec</font><br>";
	}
      }
    }

  }
?>
