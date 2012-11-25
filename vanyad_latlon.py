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
from __future__ import print_function
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
    default_lat=None
    default_lon=None

    def __init__(self):
	self.config=ReadConf()
	ConnectLivestatus.__init__(self)
	coors=self.config.no_data.split(',')
	self.default_lat=float(coors[0])
	self.default_lon=float(coors[1])

    def __del__(self):
	self.latlon.__del__()

    def GrabAddresses(self):
	location_keys=None
	postcode=None
	ambiguous_data='ambiguous_data.txt'

	f=open(ambiguous_data,'w')
	self.latlon=OpenShelves('latlon')
	if self.latlon: location_keys=self.latlon.osm.keys()
	self.locations=defaultdict(list)
	conn=httplib.HTTPConnection("nominatim.openstreetmap.org")
	status=self.get_query('hosts',('host_name','custom_variables'),())
	for host_name,custom_variables in status:
	    if 'LOCATION' in custom_variables:
		self.locations[custom_variables['LOCATION']].append(host_name)
	for location in self.locations:
	    if location in location_keys: continue
	    #String format is country_code,state,city/county,street/road,<postcode>
	    #postcode is a safeguard for ambiguities on some cities, ex. 7 streets with the same name.
	    #Other identificators are too weak to solve such ambiguities.
	    #It shall be used only when such ambiguities occur.
	    loc_details=location.split(',')
	    country=loc_details[0]
	    state=loc_details[1]
	    county=loc_details[2]
	    road=loc_details[3]
	    house_number=loc_details[4]
	    if len(loc_details)==6: postcode=loc_details[5]
	    url='/search?q=+'+house_number+'+'+road+',+'+county
	    if postcode: url+=',+'+postcode
	    url+='&format=json&countrycodes='+country+'&polygon=0&addressdetails=1'
	    url=urllib.quote(url.encode('utf-8'),',/+=&?')
	    conn.request('GET',url)
	    response=conn.getresponse()
	    if response.status==200:
		data=response.read()
		if not data: print('No data for: '+str(location)+'\n',file=f)
		else:
		    data=json.loads(data)
		    self.latlon.osm[location]=data
		    for item in data:
			have_house=0
			for item2 in item:
			    if item2=='lat' and not have_house: self.latlon.lat[location]=float(item[item2])
			    if item2=='lon' and not have_house: self.latlon.lon[location]=float(item[item2])
			    if item2=='address':
				for detail in item[item2]:
				    i=item[item2][detail].decode('utf-8')
				    if detail=='road':
					if road not in i: print('Wrong road for: '+str(location)+'\n'+str(i)+'\n'+str(data)+'\n',file=f)
				    if detail=='house_number':
					if i==house_number: have_house=1
					else: msg='Wrong house number for: '+str(location)+'\n'+str(i)+'\n'+str(data)+'\n'
				    else: msg='No house number for: '+str(location)+'\n'+str(i)+'\n'+str(data)+'\n'
				    if postcode and detail=='postcode': have_house=1
			if not have_house: print(msg,file=f)
	conn.close()
	f.close()

    def MakeGeneric(self):
	outcasts='outcasts.txt'
	f=open(outcasts,'w')
	for location in self.locations:
	    for host in self.locations[location]:
		if location in self.latlon.lat:
		    nagvis=(host,location,str(self.latlon.lat[location]),str(self.latlon.lon[location]))
		    print(';'.join(nagvis))
		else: print(host,file=f)
	f.close()

    def MakeSynthetic(self):
	for location in self.locations:
	    if self.latlon.lat[location]>self.default_lat+self.config.step: lat=self.default_lat+self.config.step
	    elif self.latlon.lat[location]<self.default_lat-self.config.step: lat=self.default_lat-self.config.step
	    else: lat=self.latlon.lat[location]
	    if self.latlon.lon[location]>self.default_lon+self.config.step: lon=self.default_lon+self.config.step
	    elif self.latlon.lon[location]<self.default_lon-self.config.step: lon=self.default_lon-self.config.step
	    else: lon=self.latlon.lon[location]
	    for host in self.locations[location]:
		nagvis=(host,location,str(lat),str(lon))
		print(';'.join(nagvis))


if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf-8') 
    bit=GenerateCoordinates()
    bit.GrabAddresses()
    bit.MakeGeneric()
#    bit.MakeSynthetic()
    bit.__del__()


