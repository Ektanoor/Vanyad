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
    status=[]
    lat={}
    lon={}
    mapdata=None
    default_lat=None
    default_lon=None

    def __init__(self):
	self.config=ReadConf()
	ConnectLivestatus.__init__(self)
	self.mapdata=OpenShelves('osm')
	coors=self.config.no_data.split(',')
	self.default_lat=float(coors[0])
	self.default_lon=float(coors[1])

    def __del__(self):
	self.mapdata.__del__()

    def GrabAddresses(self):
	location_keys=None
	postcode=None

#We need these keys to avoid beating OSM with repeated queries
	if self.mapdata: location_keys=self.mapdata.osm.keys()

#Get data from Nagios/Icinga through livestatus.
#String format is country_code,state,city/county,street/road,<postcode>
#postcode is a safeguard for ambiguities on some cities, ex. 7 streets with the same name.
#Other identificators are too weak to solve such ambiguities.
#It shall be used only when such ambiguities occur.
	self.locations=defaultdict(list)
	status=self.get_query('hosts',('host_name','custom_variables'),())
	for host_name,custom_variables in status:
	    if 'LOCATION' in custom_variables:
		self.locations[custom_variables['LOCATION']].append(host_name)

#No maps here. These requests get OSM data only.
	conn=httplib.HTTPConnection("nominatim.openstreetmap.org")
	for location in self.locations:
	    if location in location_keys: continue	#Avoid requests for data we already have
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
		    self.mapdata.osm[location]=data
	conn.close()

#On Nominatim fields inside records do not seem to be strictly positioned. Besides, the system is flexible enough to give data that partially fits the query.
#So, to avoid multiple conflicts, first we read a whole record and then check.
#The gathering algorithm here corresponds to the way Nominatim stores data on Russian entities. In other countries your mileage may vary.
    def FillData(self):
	postcode=None
	ambiguous_data='ambiguous_data.txt'
#Check ambiguous_data.txt for unexact or questionable data
	f=open(ambiguous_data,'w')
	for location in self.mapdata.osm:
	    loc_details=location.split(',')
	    road=loc_details[3]
	    house_number=loc_details[4]
	    if len(loc_details)==6: postcode=loc_details[5]
	    for item in self.mapdata.osm[location]:
		cur_country_code=None
		cur_country=None
		cur_administrative=None
		cur_state=None
		cur_county=None
		cur_city_district=None
		cur_suburb=None
		cur_road=None
		cur_house_number=None
		cur_postcode=None
		for item2 in item:
		    other_fields={}
		    if item2=='lat': cur_lat=float(item[item2])
		    if item2=='lon': cur_lon=float(item[item2])
		    if item2=='boundingbox': cur_bbox=item[item2]
		    if item2=='address':
			for detail in item[item2]:
			    i=item[item2][detail].decode('utf-8')
			    if detail=='country_code': cur_country_code=i
			    elif detail=='country': cur_country=i
			    elif detail=='administrative': cur_administrative=i
			    elif detail=='state': cur_state=i
			    elif detail=='county': cur_county=i
			    elif detail=='city_district': cur_city_district=i
			    elif detail=='suburb': cur_suburb=i
			    elif detail=='road': cur_road=i
			    elif detail=='house_number': cur_house_number=i
			    elif detail=='postcode': cur_postcode=i
#Some records have custom fields. We still have to study them.
			    else: other_fields[detail]=i

		self.lat[location]=cur_lat
		self.lon[location]=cur_lon

		if other_fields:
		    print('Custom fields found for '+str(location)+':\n',file=f)
		    for field in other_fields: print(field+': '+other_fields[field]+'\n',file=f)
		    print(str(self.mapdata.osm[location])+'\n',file=f)

		if not cur_road: print('No road for: '+str(location)+'\n'+str(self.mapdata.osm[location])+'\n',file=f)
		elif road not in cur_road: print('Wrong road for: '+str(location)+'\n'+str(cur_road)+'\n'+str(self.mapdata.osm[location])+'\n',file=f)
		if not cur_house_number: msg='No house number for: '+str(location)+'\n'+str(self.mapdata.osm[location])+'\n'
		elif house_number!=cur_house_number: msg='Wrong house number for: '+str(location)+'\n'+str(cur_house_number)+'\n'+str(self.mapdata.osm[location])+'\n'
		elif postcode and postcode!=cur_postcode: pass
		else: continue
		print(msg,file=f)
	f.close()

#u'house_number': u'1', u'country': u'Russian Federation', u'county': u'Казань', u'suburb': u'Козья слобода', u'state': u'Татарстан', u'city_district': u'Киро
#вский район', u'road': u'улица Декабристов', u'country_code': u'ru', u'administrative': u'Volga Federal District', u'bank': u'АК БАРС БАНК', u'postcode': u'420066'

    def MakeGeneric(self):
	outcasts='outcasts.txt'
	f=open(outcasts,'w')
	for location in self.locations:
	    for host in self.locations[location]:
		if location in self.lat:
		    nagvis=(host,location,str(self.lat[location]),str(self.lon[location]))
		    print(';'.join(nagvis))
		else: print(host,file=f)
	f.close()

    def MakeSynthetic(self):
	for location in self.locations:
	    if self.lat[location]>self.default_lat+self.config.step: lat=self.default_lat+self.config.step
	    elif self.lat[location]<self.default_lat-self.config.step: lat=self.default_lat-self.config.step
	    else: lat=self.lat[location]
	    if self.lon[location]>self.default_lon+self.config.step: lon=self.default_lon+self.config.step
	    elif self.lon[location]<self.default_lon-self.config.step: lon=self.default_lon-self.config.step
	    else: lon=self.lon[location]
	    for host in self.locations[location]:
		nagvis=(host,location,str(lat),str(lon))
		print(';'.join(nagvis))


if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf-8') 
    bit=GenerateCoordinates()
    bit.GrabAddresses()
    bit.FillData()
    bit.MakeGeneric()
#    bit.MakeSynthetic()
    bit.__del__()


