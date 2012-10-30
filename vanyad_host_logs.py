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

import time
from vanyad import *
from collections import Counter


class CheckHostsLogs(ConnectLivestatus):
    t_lapse=86400
    status=None
    blacklist=None
    go_black=1
    config=None
    hdowns=Counter()
    hups=Counter()
    hunreachs=Counter()
    hcommon_states=Counter()
    sdowns=Counter()
    sups=Counter()
    sunreachs=Counter()
    scommon_states=Counter()

    def __init__(self):
	ConnectLivestatus.__init__(self)
	self.config=ReadConf()
	t_check=time.time()-self.t_lapse
	t_stamp=str(round(t_check)).rstrip('0').rstrip('.')
        self.status=self.get_query('log',['host_name','state','state_type','type','attempt','current_host_max_check_attempts'],['time >= '+t_stamp,'class = 1'],'WaitTrigger: log')
        if self.go_black: self.blacklist=OpenShelves('blacklist')

    def states(self):
	host_alert='HOST ALERT'
	record_state={}
	for host_name,state,state_type,type,attempt,current_host_max_check_attempts in self.status:
	    if self.go_black and host_name in self.blacklist.lsts: continue
	    if type==host_alert:
		if state_type=='HARD':
		    if state==0:
			if attempt<current_host_max_check_attempts and attempt>1: print("Houston, we have a problem: ", host_name, attempt)
			self.hups[host_name]+=1
			self.hcommon_states['UP']+=1
		    elif state==1:
			if attempt<current_host_max_check_attempts: print("Houston, we have a problem: ", host_name, attempt,state)
			self.hdowns[host_name]+=1
			self.hcommon_states['DOWN']+=1
		    elif state==2:
			self.hunreachs[host_name]+=1
			self.hcommon_states['UNREACHABLE']+=1
		if state_type=='SOFT' and attempt==1:
		    if state==0: self.sups[host_name]+=1
		    elif state==1: self.sdowns[host_name]+=1
		    elif state==2: self.sunreachs[host_name]+=1
	for host in self.hups: del(self.sups[host])
	for host in self.hdowns: del(self.sdowns[host])
	for host in self.hunreachs: del(self.sunreachs[host])

	for host in self.sups: self.scommon_states['UP']+=self.sups[host]
	for host in self.sdowns: self.scommon_states['DOWN']+=self.sdowns[host]
	for host in self.sunreachs: self.scommon_states['UNREACHABLE']+=self.sunreachs[host]

    def report_hardstates(self):
	d_list=[]
	u_list=[]
	nope_list=[]
	comment=''
	netcon=3
	sender=SendMsg()
	for host in self.hdowns: 
	    if self.hdowns[host]>1:
		h_string=host+': '+str(self.hdowns[host])+' alerts'
		d_list.append(h_string)
	if d_list:
	    comment='These hosts have had repeated failures during the past '+str(self.t_lapse/3600)+' hours:\n'
	    down_string='\n'.join(d_list)
	    comment+=down_string+'\n\n'

	for host in self.hunreachs: 
	    if self.hunreachs[host]>1: u_list.append(host)
	if u_list:
	    comment+='These hosts have been repeatedly unreachable during the past '+str(self.t_lapse/3600)+' hours:\n'
	    unreach_string='\n'.join(u_list)
	    comment+=unreach_string+'\n\n'

	for host in self.hdowns:
	    if host not in self.hups or self.hups[host]<self.hdowns[host]: nope_list.append(host)
	for host in self.hunreachs:
	    if host not in self.hups and host not in self.hdowns: nope_list.append(host)
	if nope_list:
	    comment+='These hosts may have not recovered during the past '+str(self.t_lapse/3600)+' hours:\n'
	    nope_string='\n'.join(nope_list)
	    comment+=nope_string


	msg='ALERT - HOSTS WITH REPEATED FAILURES\n'+ \
                '\nHosts affected:\n'+comment+  \
            '\n\nTime:'+time.asctime(time.localtime(time.time()))+'\n'

	sender.send(msg,self.config.contacts,netcon)

    def report_softstates(self):
	d_list=[]
	u_list=[]
	nope_list=[]
	comment=''
	netcon=2
	sender=SendMsg()

	top_ten=self.sdowns.most_common(10)
	for host,alerts in top_ten:
	    if alerts>1:
		h_string=host+': '+str(alerts)+' alerts'
		d_list.append(h_string)
	if d_list:
	    comment='These hosts have had most soft failures during the past '+str(self.t_lapse/3600)+' hours:\n'
	    down_string='\n'.join(d_list)
	    comment+=down_string+'\n\n'

	top_ten=self.sunreachs.most_common(10)
	for host,alerts in top_ten:
	    if alerts>1: u_list.append(host)
	if u_list:
	    comment+='These hosts have been frequently unreachable during the past '+str(self.t_lapse/3600)+' hours:\n'
	    unreach_string='\n'.join(u_list)
	    comment+=unreach_string+'\n\n'


	msg='ALERT - HOSTS WITH POSSIBLE FAILURES\n'+ \
                '\nHosts affected:\n'+comment+  \
            '\n\nTime:'+time.asctime(time.localtime(time.time()))+'\n'

	sender.send(msg,self.config.contacts,netcon)

bit=CheckHostsLogs()
bit.states()
bit.report_hardstates()
bit.report_softstates()

