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
from collections import defaultdict


class CheckServicesLogs(ConnectLivestatus):
    t_lapse=86400
    status=None
    blacklist=None
    go_black=1
    config=None
    hwarnings=Counter()
    hcritical=Counter()
    hups=Counter()
    hunknowns=Counter()
    hcommon_states=Counter()
    swarnings=Counter()
    scritical=Counter()
    sups=Counter()
    sunknowns=Counter()
    scommon_states=Counter()

    def __init__(self):
	ConnectLivestatus.__init__(self)
	self.config=ReadConf()
	t_check=time.time()-self.t_lapse
	t_stamp=str(round(t_check)).rstrip('0').rstrip('.')
        self.status=self.get_query('log',['host_name','service_description','state','state_type','type','attempt','current_service_max_check_attempts'],
				    ['time >= '+t_stamp,'class = 1'],'WaitTrigger: log')
        if self.go_black: self.blacklist=OpenShelves('blacklist')


    def states(self):
	service_alert='SERVICE ALERT'
	record_state={}
	for host_name,service_description,state,state_type,type,attempt,current_service_max_check_attempts in self.status:
	    if self.go_black and service_description in self.blacklist.lsts: continue
	    key=service_description+'@'+host_name
	    if type==service_alert:
		if state_type=='HARD':
		    if state==0:
			if attempt<current_service_max_check_attempts and attempt>1: print("Houston, we have a problem: ", host_name,service_description,attempt)
			self.hups[key]+=1
			self.hcommon_states['UP']+=1
		    if state==1:
			if attempt<current_service_max_check_attempts and attempt>1: print("Houston, we have a problem: ", host_name,service_description,attempt)
			self.hwarnings[key]+=1
			self.hcommon_states['WARNING']+=1
		    elif state==2:
			if attempt<current_service_max_check_attempts: print("Houston, we have a problem: ", host_name,service_description,attempt,state)
			self.hcritical[key]+=1
			self.hcommon_states['CRITICAL']+=1
		    elif state==3:
			self.hunknowns[key]+=1
			self.hcommon_states['UKNOWN']+=1
		if state_type=='SOFT' and attempt==1:
		    if state==0: self.sups[key]+=1
		    elif state==1: self.sunknowns[key]+=1
		    elif state==2: self.scritical[key]+=1
		    elif state==3: self.sunknowns[key]+=1
	for host in self.hups: del(self.sups[key])
	for host in self.hwarnings: del(self.swarnings[key])
	for host in self.hcritical: del(self.scritical[key])
	for host in self.hunknowns: del(self.sunknowns[key])

	for host in self.sups: self.scommon_states['UP']+=self.sups[key]
	for host in self.swarnings: self.scommon_states['WARNING']+=self.swarnings[key]
	for host in self.scritical: self.scommon_states['CRITICAL']+=self.scritical[key]
	for host in self.sunknowns: self.scommon_states['UNKNOWN']+=self.sunknowns[key]


    def report_hardstates(self):
	d_list=[]
	u_list=[]
	nope_list=[]
	comment=''
	netcon=3
	sender=SendMsg()

	top=self.hcritical.most_common()
	for host,alerts in top:
	    if alerts>1:
		h_string=host+': '+str(alerts)+' alerts'
		d_list.append(h_string)
	if d_list:
	    comment='These services have had repeated failures during the past '+str(self.t_lapse/3600)+' hours:\n'
	    critical_string='\n'.join(d_list)
	    comment+=critical_string+'\n\n'

	top=self.hunknowns.most_common()
	for host,alerts in top: 
	    if alerts>1: u_list.append(host)
	if u_list:
	    comment+='These services stayed repeatedly on unknown state during the past '+str(self.t_lapse/3600)+' hours:\n'
	    unknown_string='\n'.join(u_list)
	    comment+=unknown_string+'\n\n'

	for host in self.hcritical:
	    if host not in self.hups or self.hups[host]<self.hcritical[host]: nope_list.append(host)
	for host in self.hunknowns:
	    if host not in self.hups and host not in self.hcritical: nope_list.append(host)
	if nope_list:
	    comment+='These services may have not recovered during the past '+str(self.t_lapse/3600)+' hours:\n'
	    nope_string='\n'.join(nope_list)
	    comment+=nope_string


	msg='ALERT - SERVICES WITH REPEATED FAILURES\n'+ \
                '\nServices@Hosts affected:\n'+comment+  \
            '\n\nTime:'+time.asctime(time.localtime(time.time()))+'\n'

	sender.send(msg,self.config.contacts,netcon)

    def report_softstates(self):
	d_list=[]
	u_list=[]
	nope_list=[]
	comment=''
	netcon=2
	sender=SendMsg()

	top_ten=self.scritical.most_common(10)
	for host,alerts in top_ten:
	    if alerts>1:
		h_string=host+': '+str(alerts)+' alerts'
		d_list.append(h_string)
	if d_list:
	    comment='These services have had most soft failures during the past '+str(self.t_lapse/3600)+' hours:\n'
	    critical_string='\n'.join(d_list)
	    comment+=critical_string+'\n\n'

	top_ten=self.sunknowns.most_common(10)
	for host,alerts in top_ten:
	    if alerts>1: u_list.append(host)
	if u_list:
	    comment+='These services stayed frequently on unknown state during the past '+str(self.t_lapse/3600)+' hours:\n'
	    unknown_string='\n'.join(u_list)
	    comment+=unknown_string+'\n\n'


	msg='ALERT - SERVICES WITH POSSIBLE FAILURES\n'+ \
                '\nServices@Hosts affected:\n'+comment+  \
            '\n\nTime:'+time.asctime(time.localtime(time.time()))+'\n'

	sender.send(msg,self.config.contacts,netcon)

if __name__ == '__main__':
	bit=CheckServicesLogs()
	bit.states()
	bit.report_hardstates()
	bit.report_softstates()
