#!/usr/bin/python
# -*- encoding: utf-8; py-indent-offset: 4 -*-
#
# VanyaD - Copyright - Ektanoor <ektanoor@bk.ru> 2012
#
# This is free software;  you can redistribute it and/or modify it
# under the  terms of the  GNU General Public License  as published by
# the Free Software Foundation in version 2.  VanyaD is  distributed
# in the hope that it will be useful, but WITHOUT ANY WARRANTY;  with-
# out even the implied warranty of  MERCHANTABILITY  or  FITNESS FOR A
# PARTICULAR PURPOSE. See the  GNU General Public License for more de-
# ails.  You should have  received  a copy of the  GNU  General Public
# License along with GNU Make; see the file  COPYING.  If  not,  write
# to the Free Software Foundation, Inc., 51 Franklin St,  Fifth Floor,
# Boston, MA 02110-1301 USA.


import numpy
import time
import shelve
from matplotlib import pyplot
"""The mathplotlib insertion here is temporary
"""
from vanyad_functions import *
from vanyad_classic import *
from vanyad_comms import *
from vanyad_snmp import *
from vanyad_grid import *
from vanyad_host_logs import *


#class IncidentFrequencies()

class CheckDelays1(ConnectLivestatus):
    status=[]
    def __init__(self):
	ConnectLivestatus.__init__(self)
	self.status=self.get_query('hosts',
			('host_name','last_check','latency','contacts'),
			()
			)

#    def check_latencies(self)
#	for host_name,last_check,latency,contacts in self.status:
#	    
#	return latencies

class CheckDelays2(ConnectLivestatus):
    t_lapse=86400
    status=[]
    def __init__(self):
	latencies=[]
	t_check=time.time()-self.t_lapse
	t_stamp=str(round(t_check)).rstrip('0').rstrip('.')
	ConnectLivestatus.__init__(self)
	self.status=self.get_query('log',
			['host_name','current_host_last_check','current_service_last_check','current_host_latency','current_service_latency'],
			['time >= '+t_stamp]
			)
	for host_name,current_host_last_check,current_service_last_check,current_host_latency,current_service_latency in self.status:
	    latencies.append(current_host_latency)
#	    latencies.append(current_service_latency)
	print(latencies)
	hl=numpy.array(latencies)
	lmedian=numpy.median(hl)
	lmode=numpy.mode(hl)
	laverage=numpy.average(hl)
	lmin=numpy.min(hl)
	lmax=numpy.max(hl)
	print(lmedian,lmode,laverage,lmin,lmax)

if __name__ == '__main__':
    bit=CheckDelays2()
