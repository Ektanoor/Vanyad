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
from scipy import stats
from collections import defaultdict
from matplotlib import pyplot
"""The mathplotlib insertion here is temporary
"""
from vanyad_nagcinga import *

#class IncidentFrequencies()

class CheckGroupDelays(ConnectLivestatus):
    status=[]
    def __init__(self):
	ConnectLivestatus.__init__(self)

    def check_latencies(self):
	latencies=defaultdict(list)
	self.status=self.get_query('hosts',
			('host_name','groups','latency','execution_time','contacts'),
			()
			)
	for host_name,groups,latency,execution_time,contacts in self.status:
	    for group in groups:
		latencies[group].append(execution_time)

	for group in latencies: 
	    hl=numpy.array(latencies[group])
	    lmedian=numpy.median(hl)
	    lm=stats.mode(hl)
	    for a in lm[0]:
		lmode=a
	    laverage=numpy.average(hl)
	    lmin=numpy.min(hl)
	    lmax=numpy.max(hl)
	    print(group,round(lmedian,2),round(lmode,2),round(laverage,2),round(lmin,2),round(lmax,2))



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
	    latencies.append(current_service_latency)
#	print(latencies)
	hl=numpy.array(latencies)
	lmedian=round(numpy.median(hl))
	lm=stats.mode(hl)
	for a in lm[0]:
	    lmode=round(a)
	laverage=round(numpy.average(hl))
	lmin=round(numpy.min(hl))
	lmax=round(numpy.max(hl))
	print(round(lmedian,2),round(lmode,2),round(laverage,2),round(lmin,2),round(lmax,2))

class CheckPerfICMP(ConnectLivestatus):
    perf_data=None

    def __init__(self):
	ConnectLivestatus.__init__(self)

    def check_icmp(self):
	rta_series=[]
	self.status=self.get_query('hosts',
			('host_name','perf_data','contacts'),
			()
			)
	for host_name,perf_data,contacts in self.status:
	    line=perf_data.split(';')
	    for data in line:
		if 'rta' in data:
		    rta=float(data[4:-2])
		    rta_series.append(rta)
	rta_array=numpy.array(rta_series)
	rmedian=numpy.median(rta_array)
	r=stats.mode(rta_array)
	for a in r[0]:
	    rmode=a
	raverage=numpy.average(rta_array)
	rmin=numpy.min(rta_array)
	rmax=numpy.max(rta_array)
	print(round(rmedian,2),round(rmode,2),round(raverage,2),round(rmin,2),round(rmax,2))

class CheckPerfICMPGroups(ConnectLivestatus):
    perf_data=None

    def __init__(self):
	ConnectLivestatus.__init__(self)

    def check_icmp(self):
	rta_series=defaultdict(list)
	self.status=self.get_query('hosts',
			('host_name','groups','perf_data','contacts'),
			()
			)
	for host_name,groups,perf_data,contacts in self.status:
	    line=perf_data.split(';')
	    for data in line:
		if 'rta' in data: rta=float(data[4:-2])
	    for group in groups: rta_series[group].append(rta)

	for group in rta_series:
	    rta_array=numpy.array(rta_series[group])
	    rmedian=numpy.median(rta_array)
	    r=stats.mode(rta_array)
	    for a in r[0]:
		rmode=a
	    raverage=numpy.average(rta_array)
	    rmin=numpy.min(rta_array)
	    rmax=numpy.max(rta_array)
	    print(group,round(rmedian,2),round(rmode,2),round(raverage,2),round(rmin,2),round(rmax,2))

#[u'cube-zorge47-3', u'rta=0.766ms;3000.000;5000.000;0; pl=0%;80;100;; rtmax=0.816ms;;;; rtmin=0.724ms;;;;', 

if __name__ == '__main__':
    bit=CheckGroupDelays()
    bit.check_latencies()
    bit=CheckDelays2()
    bit=CheckPerfICMP()
    bit.check_icmp()
    bit=CheckPerfICMPGroups()
    bit.check_icmp()
    