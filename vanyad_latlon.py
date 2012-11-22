#!/usr/bin/python
# -*- coding: utf-8; py-indent-offset: 4 -*-
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

#from __future__ import unicode_literals
from vanyad_nagcinga import *
from vanyad_shelves import *
from collections import defaultdict
import httplib
import urllib
import shelve
import json
import sys


class GenerateCoordinates(ConnectLivestatus):
    """This class grabs addresses from custom variable _physaddr...
    """

    config=None
    latlon=None
    status=[]
    def __init__(self):
	self.config=ReadConf()
	ConnectLivestatus.__init__(self)

    def GrabAddresses(self):
	self.latlon=OpenShelves('latlon')
	
	locations=defaultdict(list)
	conn=httplib.HTTPConnection("nominatim.openstreetmap.org")
	status=self.get_query('hosts',('host_name','custom_variables'),())
	for host_name,custom_variables in status:
	    if 'LOCATION' in custom_variables: locations[custom_variables['LOCATION']].append(host_name)
	for location in locations:
	    if locations[location] in self.latlon.lat: continue
	    road=location.split(',')[0]
	    house_number=location.split(',')[1]
	    loc=location.replace(',','+')
	    url='/search?q=+'+loc+',+'+self.config.city+'&format=json&countrycodes=ru&polygon=0&addressdetails=1'
	    url=urllib.quote(url.encode('utf-8'),',/+=&?')
	    conn.request('GET',url)
	    response=conn.getresponse()
	    if response.status==200:
		data=response.read()
		data=json.loads(data)
		if data:
		    for item in data:
			for item2 in item:
			    if item2=='address':
				for detail in item[item2]: 
				    i=item[item2][detail].decode('utf-8')
				    if detail=='road': rd=i
				    if detail=='house_number':
					if i!=house_number: i=house_number
			    if item2=='lat': self.latlon.lat[locations[location]]=item[item2]
			    if item2=='lon': self.latlon.lon[locations[location]]=item[item2]
#			    else: print(item2,item[item2])
	conn.close()

    def TestLoc(self):
	for host in self.latlon.lat:
	    print(host,self.latlon.lat[host])
	    print(host,self.latlon.lon[host])

if __name__ == '__main__':
    reload(sys) 
    sys.setdefaultencoding('utf-8') 
    bit=GenerateCoordinates()
    bit.GrabAddresses()
    bit.TestLoc()


"""

>>> conn.close()


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

"""