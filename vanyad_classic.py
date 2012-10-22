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

#From here we start the secondary series of classes

class FastChecks(ConnectLivestatus):
    """This class is a base for many small checks on hosts. 
       Most of the work is made with help of Pythons's internal datatypes
    """
    status=[]
    def __init__(self,state,acknowledge,notification_period,notification):
	ConnectLivestatus.__init__(self)
	self.status=self.get_query('hosts',
			('host_name','parents','last_state_change','contacts'),
			('state = '+str(state),'acknowledged = '+str(acknowledge),'in_notification_period = '+str(notification_period),'notifications_enabled = '+str(notification))
			)

    def parents_affected(self,lapse):
	downs={}
	t_check=time.time()-lapse
	for host_name, parents,last_state_change,contacts in self.status:
	    if last_state_change>=t_check:
		downs[host_name]=parents
	return downs

    def hosts_changes(self,lapse):
	downs=[]
	t_check=time.time()-lapse
	for host_name, parents,last_state_change,contacts in self.status:
	    if last_state_change<=t_check:
		downs.append(host_name)
	return downs

    def which_contacts(self):
	cnts=set()
	for host_name, parents,last_state_change,contacts in self.status:
	    for contact in contacts:
		cnts.add(contact)
	return cnts

class Blacklist(ConnectLivestatus):
    """ A class to determine and cleanup nodes that are considered superfluous.
    """
    bl=None
    nagcinga=None
    comment='In blacklist'
    def __init__(self):
	ConnectLivestatus.__init__(self)
	self.bl=OpenShelves('blacklist')
	self.nagcinga=ConnectNagCinga()

    def ack_host(self):
	noacks=self.get_query('hosts',['host_name'],('state = 1','acknowledged = 0'))
	for host_name in noacks:
	    if host_name[0] in self.bl.lsts:
		self.nagcinga.acknowledge_host(host_name[0],1,0,0,self.comment)

    def ack_svc(self):
	noacks=self.get_query('services',['host_name','description'],('state = 1','acknowledged = 0'))
	for host_name, description in noacks:
	    if description in self.bl.lsts:
		self.nagcinga.acknowledge_service(host_name,description,1,0,0,self.comment)


