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
from unidecode import unidecode
import httplib
import urllib
import shelve
import json
import sys
import os


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
	self.houses=defaultdict(list)
	self.roads=defaultdict(list)
	self.suburbs=defaultdict(list)
	self.districts=defaultdict(list)
	self.cities=defaultdict(list)
	self.counties=defaultdict(list)
	self.administratives=defaultdict(list)
	self.countries=defaultdict(list)
	self.hosts=defaultdict(tuple)
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
		cur_city=None
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
			    elif detail=='city': cur_city=i
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
#It looks crazy? Yes, because IT IS crazy! Can you realize a city with 7 completely different roads, officialy carrying one and the same name? Or how many Moscows exist on Earth? 
#Even Paris has a "twin" in the Urals. And it does not end here! Many big cities in ex-USSR have a "Moscow district". And what about something as a state or province? 
#Searching for "just" California will give you three states in two different countries. Much as "just" Washington may stubbornly show some city called Seattle.
#Portugal had a province called "Estremadura", which some use till today and sounding nearly as the Spanish "Extremadura". Mozambique has a "Gaza" province.
#And even countries are not far from this, just try to look for "Guinea" or "Korea".

	    for host in self.locations[location]:
		self.hosts[host]=(cur_lat,cur_lon,cur_bbox,cur_country_code,cur_country,cur_administrative,
		    cur_state,cur_county,cur_city,cur_city_district,cur_suburb,cur_road,cur_house_number,cur_postcode)
		self.houses[(cur_country_code,cur_administrative,cur_state,cur_county,cur_city,cur_city_district,cur_suburb,cur_road,cur_house_number,cur_postcode)].append(host)
		if postcode: self.roads[(cur_country_code,cur_administrative,cur_state,cur_county,cur_city,cur_road,cur_postcode)].append(host)
		else: self.roads[(cur_country_code,cur_administrative,cur_state,cur_county,cur_city,cur_road)].append(host)
		self.suburbs[(cur_country_code,cur_administrative,cur_state,cur_county,cur_city,cur_city_district,cur_suburb)].append(host)
		self.districts[(cur_country_code,cur_administrative,cur_state,cur_county,cur_city,cur_city_district)].append(host)
		self.cities[(cur_country_code,cur_administrative,cur_state,cur_county,cur_city)].append(host)
		self.counties[(cur_country_code,cur_administrative,cur_state,cur_county)].append(host)
		self.administratives[(cur_country_code,cur_administrative)].append(host)
		self.countries[cur_country].append(host)
	f.close()

    def MakeGeneric(self):
	outcasts='outcasts.txt'
	locations='locations.txt'
	f=open(outcasts,'w')
	g=open(locations,'w')
	for location in self.locations:
	    for host in self.locations[location]:
		if location in self.lat:
		    nagvis=(host,location,str(self.lat[location]),str(self.lon[location]))
		    print(';'.join(nagvis),file=g)
		else: print(host,file=f)
	g.close()
	f.close()

    def Experimental(self):
	maps='./maps'
	geo='./geomap'
	if not os.path.exists(maps): os.makedirs(maps)
	if not os.path.exists(geo): os.makedirs(geo)
	for road in self.roads:
	    if road[-3]: roadname=str(road[-3])+'-'+str(road[-1])
	    else: roadname=str(road[-4])+'-'+str(road[-1])
	    u_roadname=unidecode(roadname.decode('utf8'))
	    u_roadname=u_roadname.replace("'","")
	    u_roadname=u_roadname.replace(".","")
	    u_roadname=u_roadname.replace(' ','')
	    m=open(maps+'/'+u_roadname+'.cfg','w')
	    print('define global {',file=m)
	    print('    sources=geomap',file=m)
	    print('    alias='+roadname,file=m)
	    print('    iconset=std_medium',file=m)
	    print('    backend_id=live_1',file=m)
	    print('    source_file='+u_roadname,file=m)
	    print('    width=1600',file=m)
	    print('    height=1400',file=m)
	    print('    geomap_border=0.0',file=m)
	    print('    geomap_zoom=10',file=m)
	    print('}',file=m)
	    m.close()
	    g=open(geo+'/'+u_roadname+'.csv','w')
	    for host in self.roads[road]:
		nagvis=(host,roadname,str(self.hosts[host][0]),str(self.hosts[host][1]))
		print(';'.join(nagvis),file=g)
	    g.close()

    def Experimental2(self):
	maps='./maps'
	geo='./geomap'
	if not os.path.exists(maps): os.makedirs(maps)
	if not os.path.exists(geo): os.makedirs(geo)
	for district in self.districts:
	    if district[-2]: districtname=str(district[-2])+'-'+str(district[-1])
	    else: districtname=str(district[-3])+'-'+str(district[-1])
	    u_districtname=unidecode(districtname.decode('utf8'))
	    u_districtname=u_districtname.replace("'","")
	    u_districtname=u_districtname.replace(".","")
	    u_districtname=u_districtname.replace(' ','')
	    m=open(maps+'/'+u_districtname+'.cfg','w')
	    print('define global {',file=m)
	    print('    sources=geomap',file=m)
	    print('    alias='+districtname,file=m)
	    print('    iconset=std_small',file=m)
	    print('    backend_id=live_1',file=m)
	    print('    source_file='+u_districtname,file=m)
	    print('    width=1600',file=m)
	    print('    height=1400',file=m)
	    print('    geomap_border=0.0',file=m)
#	    print('    geomap_zoom=10',file=m)
	    print('}',file=m)
	    m.close()
	    g=open(geo+'/'+u_districtname+'.csv','w')
	    for host in self.districts[district]:
		nagvis=(host,districtname,str(self.hosts[host][0]),str(self.hosts[host][1]))
		print(';'.join(nagvis),file=g)
	    g.close()

if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf-8') 
    bit=GenerateCoordinates()
    bit.GrabAddresses()
    bit.FillData()
    bit.MakeGeneric()
    bit.Experimental2()
    bit.__del__()


