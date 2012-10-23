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

from xmpp import *
from vanyad_nagcinga import *
from vanyad_shelves import *

#These separate functions are needed for Jabber. Including them inside a class is problematic as they are passed as handlers
def iq_handler(conn,iq_node):
    """ Handler for processing some "get" query from custom namespace"""
    reply=iq_node.buildReply('result')
    conn.send(reply)
    raise NodeProcessed

def message_handler(conn,mess_node): pass

def presence_handler(cl,msg):
    prs_type=msg.getType()
    who=msg.getFrom()
    if prs_type == "subscribe":
        cl.send(Presence(to=who,typ='subscribed'))
        cl.send(Presence(to=who,typ='subscribe'))


#These are the output classes.
#While they shall not carry a Livestatus inheritance, still, they have to do some basic queries to send results.
#In the future there could be some changes here, if things get more intricated.

class ConnectJabber:
    address=None
    live=None
    cl=None

    def __init__(self):
	config=ReadConf()
	self.address=config.address
	self.live=ConnectLivestatus()
	self.cl=Client(config.xmpp_server,debug=[])
	if not self.cl.connect(): raise IOError('Can not connect to server.')
	if not self.cl.auth(config.xmpp_user,config.xmpp_passwd,'bot'): raise IOError('Can not auth with server.')
	self.cl.RegisterHandler('iq',iq_handler)
	self.cl.RegisterHandler('message',message_handler)
	self.cl.RegisterHandler('presence',presence_handler)
	self.cl.sendInitPresence()
	self.cl.Process(1)

    def send(self,msg,contacts):
	contact_list=[]
	for contact in contacts:
	    contact_list.append('name = '+str(contact))
	cnt=len(contacts)
	status=self.live.get_query('contacts',[self.address],tuple(contact_list),'Or: '+str(cnt))
	for user in status:
	    if user[0]!='':
		print(user[0],' ',msg)
#		self.cl.send(Message(to=user[0],body=msg,typ='chat'))
	self.cl.Process(1)

    def __del__(self):
	self.cl.disconnect()

class SendSMS:
    live=None
    script=None
    def __init__(self):
	"""Here, we have a problem with the SMS daemon: he loves to zombie from time to time. So, we first check its status.
	Of course, our Icinga daemon checks it.
	"""
	config=ReadConf()
	self.script=config.script

	self.live=ConnectLivestatus()
	if config.check_smsd:
	    status=self.live.get_query('services',['state'],['description = '+config.sms_zombies])
	    if status!=[[0]]:
		print('A serious technical problem ocurred - zombies are on the wild and thus no sms can be sent')
		return 1

    def send(self,msg,contacts):
	contact_string=''
	contact_list=[]
	for contact in contacts:
	    contact_list.append('name = '+str(contact))
	cnt=len(contacts)
	status=self.live.get_query('contacts',['pager'],tuple(contact_list),'Or: '+str(cnt))
	for pager in status:
	    if pager[0]!='':
		print(pager[0],' ',msg)
#		call([self.script,pager[0],msg],stdout=None,stderr=None)

