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

import os
import time
import argparse
import pipes
import syslog
from vanyad_daemon import *

try:
    working_dir='/opt/vanyad'
    max_length=256
    pid_file='/var/run/icinga/vanyad.pid'
    pipe_file='/var/run/icinga/vanyad.cmd'
    parser = argparse.ArgumentParser(prog='vanyad_handler',description='A special handler to connect Nagios/Icinga to Vanyad.')
    parser.add_argument('--host',help='Host name')
    parser.add_argument('--address',help='Host name')
    parser.add_argument('--state',help='Host state')
    parser.add_argument('--type', help='Host state type')
    parser.add_argument('--attempt', help='Attempt number')
    args = parser.parse_args()
    if not args.host and not address and not args.state and not args.type and not args.attempt:
	parser.error("Not enough arguments to launch parser!")
	raise Exception('Error on parser')

except Exception, e:
    print("Error: %s" % str(e))

try:
    pid=0
    os.chdir(working_dir)
    if os.path.exists(pid_file):
	pidf=open(pid_file,'r')
	pid=int(pidf.readline())
    if not os.path.exists('/proc/'+str(pid)):
	os.system('./vanyad_daemon.py')
	MakeDetach()
	time.sleep(0.5)
    msg=';'+args.host+';'+args.address+';'+args.state+';'+args.type+';'+args.attempt
    if len(msg)>max_length: raise Exception('Message too large to be processed!')
    msg=msg.zfill(max_length)
    t=pipes.Template()
    f=t.open(pipe_file,'w')
    f.write(msg)
    f.close()

except Exception, e:
    print("Error: %s" % str(e))

