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

from vanyad_nagcinga import *
from vanyad_shelves import *
from vanyad_comms import *

p_base=0


class TheGrid(ConnectProlog):
    """This is the real gem of this system. We pick up all parent dependencies from Nagios/Icinga and turn them over Prolog.
    """
    config=None
    addresses={}
    jabber=None
    blacklist=None
    def __init__(self):
	self.config=ReadConf()
	global p_base
	self.sender=SendMsg(['jabber'])
	ConnectProlog.__init__(self)
	if not p_base:
	    p_base=1
	    self.blacklist=OpenShelves('blacklist')
	    status=self.get_query('hosts',('host_name','address','custom_variables','state','parents'),())
	    for host_name, address, custom_variables, state, parents in status:
		self.addresses[host_name]=address
		if 'CONNECTED' in custom_variables:
		    self.prolog.assertz("ports('"+host_name+"','"+custom_variables['CONNECTED']+"')")
		if state==0: s_state='UP'
		elif state==1: s_state='DOWN'
		elif state==2: s_state='UNREACHABLE'
		self.prolog.assertz("state('"+host_name+"','"+s_state+"')")
		for parent in parents:
		    self.prolog.assertz("parent('"+parent+"','"+host_name+"')")

    def GridDamage(self):
	is_block=1
	bl_hosts=[]
	warn_lines=[]
	state_list=list(self.prolog.query("state(X,'DOWN')"))
	for host in state_list:
	    if host['X'] not in self.blacklist.lsts:
		blocks=0
		affects=0
		warning="Host "+host['X']+" is DOWN"
		descendants=list(self.prolog.query("descendants('"+host['X']+"',X)"))
		for descendant in descendants:
		    blocked=list(self.prolog.query("blocked(X,'"+descendant['X']+"')"))
		    if blocked:
			for blocker in blocked:
			    if blocker['X']!=host['X']: is_block=0
			    else: is_block=1;
		    if is_block: blocks+=1
		    else:  affects+=1
		if affects>0: warning+=", affecting "+str(affects)+" nodes"
		if blocks>0: warning+=" and blocking "+str(blocks)+" nodes"
		warning+="!"
		warn_lines.append(warning)
	msg='ALERT:\n'+'\n'.join(warn_lines)+'\n\nTime:'+time.asctime(time.localtime(time.time()))+'\n'
	self.sender.send(msg,self.config.contacts)


    def GridParadoxes(self):
	warn_lines=[]
	paradoxes=list(self.prolog.query("paradoxes(X,Y)"))
	for paradox in paradoxes:
	    if paradox['X'] not in self.blacklist.lsts:
		warning='Host '+paradox['Y']+' is UP while parent '+paradox['X']+' is DOWN/UNREACHABLE!'
		warn_lines.append(warning)
	msg='ALERT:\n'+'\n'.join(warn_lines)+'\n\nTime:'+time.asctime(time.localtime(time.time()))+'\n'
	self.sender.send(msg,self.config.contacts)
