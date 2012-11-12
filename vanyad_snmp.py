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

import netsnmp
from vanyad_shelves import ReadConf

class SNMPCrawler:
    community=None
    snmpIfDescr='.1.3.6.1.2.1.2.2.1.2';
    snmpIfAlias='.1.3.6.1.2.1.31.1.1.1.18';
    snmpIfSpeed='.1.3.6.1.2.1.2.2.1.5';
    snmpIfHighSpeed='.1.3.6.1.2.1.31.1.1.1.15';
    snmpIfAdminStatus='.1.3.6.1.2.1.2.2.1.7';
    states_IfAdminStatus={ '1':'up', '2':'down', '3':'testing'}
    snmpIfOperStatus='.1.3.6.1.2.1.2.2.1.8';
    states_IfOperStatus={ '1':'up', '2':'down', '3':'testing', '4':'unknown','5':'dormant','6':'notPresent','7':'lowerLayerDown'}
    snmpIfLastChange='.1.3.6.1.2.1.2.2.1.9';
    snmpIfInErrors='.1.3.6.1.2.1.2.2.1.14';
    snmpIfOutErrors='.1.3.6.1.2.1.2.2.1.20';
    snmpIfInDiscards='.1.3.6.1.2.1.2.2.1.13';
    snmpIfOutDiscards='.1.3.6.1.2.1.2.2.1.19';
    snmpIfInOctets='.1.3.6.1.2.1.2.2.1.10';
    snmpIfOutOctets='.1.3.6.1.2.1.2.2.1.16';
    snmpdot1dTpFdbAddress='.1.3.6.1.2.1.17.4.3.1.1'
    snmpdot1dTpFdbPort='.1.3.6.1.2.1.17.4.3.1.2'
    snmpdot1dTpFdbStatus='.1.3.6.1.2.1.17.4.3.1.3'
    states_dot1dTpFdbStatus={ '1':'other', '2':'invalid', '3':'learned', '4':'self','5':'mgmt'}
    session=None
    iid=None
    port=None

    def __init__(self,host):
	config=ReadConf()
	self.community=config.snmp_community
	self.session=netsnmp.Session(DestHost=host,Version=2,Community=self.community)

    def identify_port(self,port):
	ports=netsnmp.VarList(netsnmp.Varbind(self.snmpIfDescr))
	self.session.walk(ports)
	for var in ports:
	    if var.val==port:
		self.iid=var.iid

    def port_state(self):
	keys=['alias','admin_status','oper_status','last_change','speed']
	pstate=netsnmp.VarList(netsnmp.Varbind(self.snmpIfAlias,self.iid),
				netsnmp.Varbind(self.snmpIfAdminStatus,self.iid),
				netsnmp.Varbind(self.snmpIfOperStatus,self.iid),
				netsnmp.Varbind(self.snmpIfLastChange,self.iid),
				netsnmp.Varbind(self.snmpIfHighSpeed,self.iid)
				)
	self.session.get(pstate)
	ps=[p.val for p in pstate]
	state=dict(zip(keys,ps))
	return state

    def port_stats(self):
	keys=['ingress','egress','in_errors','out_errors','in_discards','out_discards']
	pstats=netsnmp.VarList(netsnmp.Varbind(self.snmpIfInOctets,self.iid),
				netsnmp.Varbind(self.snmpIfOutOctets,self.iid),
				netsnmp.Varbind(self.snmpIfInErrors,self.iid),
				netsnmp.Varbind(self.snmpIfOutErrors,self.iid),
				netsnmp.Varbind(self.snmpIfInDiscards,self.iid),
				netsnmp.Varbind(self.snmpIfOutDiscards,self.iid)
				)
	self.session.get(pstats)
	ps=[p.val for p in pstats]
	stats=dict(zip(keys,ps))
	return stats

    def port_arptable(self):
	macs=[]
	pmacs=netsnmp.VarList(netsnmp.Varbind(self.snmpdot1dTpFdbPort))
	self.session.walk(pmacs)
	for p in pmacs:
	    if p.val==self.iid:
		addr=p.tag.rsplit('.',6)
		s_addr=':'.join([hex(int(addr[i]))[2:].zfill(2) for i in range(1,6)])
		macs.append(s_addr)
	return macs

    def device_arptable(self):
	device_macs=[]
	dmacs=netsnmp.VarList(netsnmp.Varbind(self.snmpdot1dTpFdbAddress))
	self.session.walk(dmacs)
	device_macs=[]
	for d in dmacs:
	    address=struct.unpack('!BBBBBB',d.val)
	    s_addr=':'.join([hex(int(addr))[2:].zfill(2) for addr in address])
	    device_macs.append(s_addr)
	return device_macs

    def device_freshness(self):
	port_macs={}
	pmacs=netsnmp.VarList(netsnmp.Varbind(self.snmpdot1dTpFdbStatus))
	self.session.walk(pmacs)
	for p in pmacs:
	    addr=p.tag.rsplit('.',6)
	    s_addr=':'.join([hex(int(addr[i]))[2:].zfill(2) for i in range(1,6)])
	    port_macs[s_addr]=p.val
	return port_macs

