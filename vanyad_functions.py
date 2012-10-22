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

#Some special functions for quite extravagant situations

def port_convert(port):
    """ Convert port names from short to long names.

	Under some circumstances, ports are written in their "short form" as they are more familiar to admins.
	However, SNMP does not understand such shortenings, so we have to convert them.
    """
    edge=re.compile('eth [0-9]',re.IGNORECASE)
    hw_cs_ge=re.compile('ge|i[0-9]',re.IGNORECASE)
    hw_cs_xge=re.compile('xge|i[0-9]',re.IGNORECASE)
    p1=edge.match(port)
    p2=hw_cs_ge.match(port)
    p3=hw_cs_xge.match(port)
    if p1:
        name,nums=port.split()
        unit_num,port_num=port.split('/')
        port="Ethernet Port on unit "+unit_num+", port "+port_num
    elif p2:
        slot_num,adapter_num,port_num=port.split('/')
        port="GigabitEthernet"+slot_num[-1]+"/"+adapter_num+"/"+port_num
    elif p3:
        slot_num,adapter_num,port_num=port.split('/')
        port="XGigabitEthernet"+slot_num[-1]+"/"+adapter_num+"/"+port_num
    return port

def convert_time(change):
    """ Convert time to human readable form.
    """
    change=int(change)
    text=''
    t=change//86400
    if t>0:
	change-=t*86400
	text+=str(t)+' day(s) '
    t=change//3600
    if t>0:
	change-=t*3600
	text+=str(t)+' hour(s) '
    t=change//60
    if t>0:
	change-=t*60
	text+=str(t)+' minutes(s) '
    if change>0:
	text+=str(change)+' second(s)'
    return text

