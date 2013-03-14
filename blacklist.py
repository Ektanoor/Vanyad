#!/usr/bin/python
# -*- encoding: utf-8; py-indent-offset: 4 -*-
#
# This is free software;  you can redistribute it and/or modify it
# under the  terms of the  GNU General Public License  as published by
# the Free Software Foundation in version 2.  Vanya is  distributed
# in the hope that it will be useful, but WITHOUT ANY WARRANTY;  with-
# out even the implied warranty of  MERCHANTABILITY  or  FITNESS FOR A
# PARTICULAR PURPOSE. See the  GNU General Public License for more de-
# ails.  You should have  received  a copy of the  GNU  General Public
# License along with GNU Make; see the file  COPYING.  If  not,  write
# to the Free Software Foundation, Inc., 51 Franklin St,  Fifth Floor,
# Boston, MA 02110-1301 USA.

import os
import sys
import time
import pipes
import shelve
import argparse
import livestatus
from subprocess import call

socket_path = 'unix:/run/icinga/rw/live'

try:
    parser = argparse.ArgumentParser(prog='blacklist',description='Blacklist constantly unstable devices.')
    parser.add_argument('--host',help='add host to blacklist')
    parser.add_argument('--service', help='add service to blacklist')
    parser.add_argument('--match',action='store_true',help='match host/service options as substrings')
    parser.add_argument('--remove',action='store_true',help="remove host/service from blacklist (reverses -h and -s actions)")
    args = parser.parse_args()
    if args.host and args.service:
	parser.error("options host and service are mutually exclusive")
	raise

except Exception, e:
    print("Error1: %s" % str(e))


try:
    sv = shelve.open('blacklist')
except:
    sys.stderr.write("Error opening shelve\n")
    sys.exit(1)

try:
    if sv.has_key('hosts'):
        hosts=sv['hosts']
    else: hosts=[]
    if sv.has_key('services'):
        services=sv['services']
    else: services=[]

except:
    sys.stderr.write("Error opening lists\n")
    sys.exit(1)



try:
    if not args.remove:
	if args.host:
	    if not args.match:
		if args.host not in hosts: hosts.append(args.host)
	    else:
		status = livestatus.SingleSiteConnection(socket_path).query_table(
			"GET hosts\n"
			"Columns: host_name\n"
			"Filter: host_name ~ "+args.host+"\n"
		)
		for host_name in status: hosts.append(host_name[0])
	if args.service:
	    if not args.match:
		if args.service not in services: services.append(args.service)
	    else:
		status = livestatus.SingleSiteConnection(socket_path).query_table(
			"GET services\n"
			"Columns: description\n"
			"Filter: description ~ "+args.service+"\n"
		)
		for description in status: services.append(description[0])
    else:
	if args.host:
	    if not args.match:
		if args.host in hosts: filter(lambda a: a != args.host, hosts)
	    else:
		status = livestatus.SingleSiteConnection(socket_path).query_table(
			"GET hosts\n"
			"Columns: host_name\n"
			"Filter: host_name ~ "+args.host+"\n"
		)
		for host_name in status: filter(lambda a: a != args.host, hosts)
	if args.service:
	    if not args.match:
		if args.service in services: filter(lambda a: a != args.service, services)
	    else:
		status = livestatus.SingleSiteConnection(socket_path).query_table(
			"GET services\n"
			"Columns: description\n"
			"Filter: description ~ "+args.service+"\n"
		)
		for description in status: filter(lambda a: a != args.service, services)


except Exception, e:
    print("Error: %s" % str(e))


sv['hosts']=hosts
sv['services']=services

sv.close()






