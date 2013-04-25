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

from vanyad_functions import *
from vanyad_classic import *
from vanyad_comms import *
from vanyad_snmp import *
from vanyad_grid import *
from vanyad_host_logs import *
import pwd, os

class AlienNodes(TheGrid):
    """These nodes are hardware that somehow is "out of reach" for regular monitoring.
	Besides we really don't need to regularly monitor them.
	We only need to check their state if something goes wrong on their parents
    """
    status=None
    check_group='vip_clients'
    def __init__(self):
	TheGrid.__init__(self)
	self.members=self.get_query('hostgroups',
			['members'],
			['name = '+str(self.check_group)]
			)


    def ProcessAliens(self):
	state='PENDING'
	processor=ConnectNagCinga()
	for member in self.members[0][0]:
	    s1=list(self.prolog.query("parent_state('"+member+"',X)"))
	    for s2 in s1:
		if s2['X']=='UP' and state!='UP': state='UP'
		elif (s2['X']=='DOWN' or s2['X']=='UNREACHABLE') and state!='UP': state='UNREACHABLE'
	    if state=='UP':
		processor.process_host(member,'0','Parent Available')
	    elif state=='UNREACHABLE':
		processor.process_host(member,'2','Parent Unreachable')

class PortChecks(TheGrid):

    def __init__(self):
	TheGrid.__init__(self)

    def show_state(self):
	paradoxes=set()
	ancestors=set()
	warn_lines=[]
	netcon=4
	paradox_list=list(self.prolog.query("paradoxes(X,Y)"))
	for para_dict in paradox_list:
	    paradoxes.add(para_dict['X'])
	for paradox in paradoxes:
	    if paradox not in self.blacklist.lsts and paradox not in self.ack_list: 
		ancestor=list(self.prolog.query("ancestor('"+paradox+"',X,P)"))
		for host in ancestor:
		    if host['X'] not in ancestors:
			ancestors.add(host['X'])
			port=host['P']
			snmp=SNMPCrawler(self.addresses[host['X']])
			snmp.identify_port(port)
			state=snmp.port_state()
			if not state['alias']:
			    warn_lines.append('MAJOR ALERT - NO SNMP REPLY!')
			    warn_lines.append('Ancestor: '+host['X']+' for host '+paradox)
			else:
			    stats=snmp.port_stats()
			    macs=snmp.port_arptable()

			    warn_lines.append('These are the port states for the closest reachable ancestors of host '+paradox)
			    warn_lines.append('Ancestor: '+host['X'])
			    warn_lines.append('Port: '+host['P']+' aka '+state['alias'])
			    if bool(state['admin_status']) and bool(state['oper_status']): port_state='Port is UP.'
			    elif not bool(state['admin_status']): port_state='Port is administratively DOWN!'
			    elif not bool(state['oper_status']): port_state='Port is DOWN!'
			    warn_lines.append('State: '+port_state)
			    last_change=int(state['last_change'])
			    if last_change>3600:
				last_change/=3600
				change_str=str(last_change)+' hours'
			    else:
				last_change/=60
				change_str=str(last_change)+' minutes'
			    warn_lines.append('Last change: '+change_str)
			    speed=int(state['speed'])
			    #speed/=1000000
			    warn_lines.append('Statistics: ')
			    warn_lines.append('Speed='+str(speed)+'Mbps')
			    warn_lines.append('Ingress='+stats['ingress']+' octets')
			    warn_lines.append('Egress='+stats['egress']+' octets')
			    if int(stats['in_errors']) or int(stats['out_errors']):
				warn_lines.append('There are errors on port: '+stats['in_errors']+' octets in, '+stats['out_errors']+' octets out.')
			    else: warn_lines.append('No errors on port')
			    if int(stats['in_discards']) or int(stats['out_discards']):
				warn_lines.append('There are packets discarded on port: '+stats['in_discards']+' octets in, '+stats['out_discards']+' octets out.')
			    else: warn_lines.append('No packets discarded')
			    if macs: warn_lines.append('There are registered MACs on this port.')
			    else: warn_lines.append('No MACs registered on this port!')
			
			    msg='INFO - PORT STATUS'+ \
				'\n'.join(warn_lines)+  \
				'\n\nTime:'+time.asctime(time.localtime(time.time()))+'\n'
			self.sender.send(msg,self.config.contacts,netcon)

class TakeAction:
    """ A class to test ready objects and some prototype tasks
    """
    fchecks=None
    nagcinga=None
    sender=None
    def __init__(self):
	self.fchecks=FastChecks(1,0,1,1)
	self.nagcinga=ConnectNagCinga()
	self.sender=SendMsg()

    def check_massive_downs(self,top,lapse):
	down_string=''
	parent_string=''
	d_list=[]
	p_list=[]
	netcon=6
	parents=self.fchecks.parents_affected(lapse)
	contacts=self.fchecks.which_contacts()
	downed=parents.keys()
	if len(downed)>=top:
	    comment='Turned off by admin'
	    for host in downed:
		self.nagcinga.acknowledge_host(host,1,0,0,comment)
		d_list.append(host)
		for parent in parents[host]:
		    if parent_string.find(parent)==-1:
			p_list.append(parent)
		parent_string='\n'.join(p_list)
	    down_string='\n'.join(d_list)
	    msg='MAJOR ALERT - MASSIVE BLACKOUT:\n'+str(len(downed))+' hosts down in '+str(lapse/60)+' minutes.\n'
	    t_msg='\n\nTime:'+time.asctime(time.localtime(time.time()))+'\n'

	    j_msg=msg+'\nHosts down:\n'+down_string+'\n\nParents affected:\n'+parent_string+t_msg
	    self.sender.send(j_msg,contacts,netcon)


    def check_long_downs(self,lapse):
	host_string=''
	d_list=[]
	netcon=5
	changes=self.fchecks.hosts_changes(lapse)
	if changes:
	    contacts=self.fchecks.which_contacts()
	    comment='This host has been down for too long (>'+str(lapse/3600)+' hours)'
	    for host in changes:
		self.nagcinga.acknowledge_host(host,1,0,0,comment)
		d_list.append(host)
	    host_string='\n'.join(d_list)
	    msg='ALERT - HOSTS TOO LONG DOWN. No ACK for >'+str(lapse/3600)+' hours.\n'+ \
		'\nHosts affected:\n'+host_string+  \
	    '\n\nTime:'+time.asctime(time.localtime(time.time()))+'\n'
	    self.sender.send(msg,contacts,netcon)



if __name__ == '__main__':
    uid = pwd.getpwnam('icinga')[2]
    os.setuid(uid)
    guard=Blacklist()
    guard.ack_host()
    guard.ack_svc()
    action=TakeAction()
    action.check_long_downs(28800)
    action.check_massive_downs(5,600)
    JA307020=TheGrid()
    JA307020.GridDamage()
    JA307020.GridParadoxes()
    recognizer=AlienNodes()
    recognizer.ProcessAliens()
    bit=PortChecks()
    bit.show_state()
    clu=CheckHostsLogs()
    clu.states()
    clu.report_hardstates()
    clu.report_softstates()
