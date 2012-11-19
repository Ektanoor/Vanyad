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

from __future__ import print_function
import os
import time
import fcntl
import syslog
import resource
from vanyad_comms import *
#from vanyad_nagcinga import *
#from vanyad_shelves import *

#class VerifyLive(ConnectLivestatus):
#    status=None
#
#    def __init__(self):
#	ConnectLivestatus.__init__(self)
#	self.status=self.get_query('hosts',
#			('host_name','state','state_type','current_attempt','last_state_change','check_options'),
#			('state = '+str(state))
#			)
#	for host_name,state,state_type,current_attempt,last_state_change,check_options in self.status:

class VerifyLiveClassic():
    config=None
    sender=None
    ready_time=0
    hosts={}
    msgs={}
    hosts_alerted=[]
    contacts=['icingaadmin']

    def __init__(self):
	self.config=ReadConf()
	self.sender=SendMsg()
	self.ready_time=time.time()

    def check_state(self,host,address,state,state_type,attempt):
	min_time=55
	cur_time=time.time()
	if (state=='DOWN' or state=='UNREACHABLE') and state_type=='SOFT':
	    if host in self.hosts and host not in self.hosts_alerted:
		diff_time=cur_time-self.hosts[host]
		if diff_time>min_time and int(attempt)>1: 
		    self.hosts_alerted.append(host)
		    h_time=time.asctime(time.localtime(time.time()))
		    msg=host+' - '+address+' - '+h_time
		    self.msgs[host]=msg
	    else: self.hosts[host]=cur_time
	elif state=='UP' and host in self.hosts_alerted and host in self.hosts:
	    self.hosts_alerted.remove(host)
	    del self.hosts[host]

    def send_msg(self):
	max_time=70
	netcon=3
	final_msg='\n'
	if time.time()-self.ready_time>max_time and self.msgs:
	    for host in self.msgs: final_msg+=self.msgs[host]+'\n'
	    self.sender.send(final_msg,self.config.monitors,netcon)
	    self.ready_time=time.time()
	    self.msgs={}
	    syslog.syslog(final_msg)

class GoDaemon():
    pipe=None
    t_lapse=600

    def __init__(self):
	fh=None
	system='icinga'
	dev_null='/dev/null'

	max_length=256
	max_fd=1024
	working_dir='/opt/vanyad'
	pid_file='/var/run/icinga/vanyad.pid'
	pipe_file='/var/run/icinga/vanyad.cmd'
	os.chdir(working_dir)
	os.umask(0)
	result=resource.getrlimit(resource.RLIMIT_NOFILE)[1]
	if result==resource.RLIM_INFINITY: result=max_fd
	for fd in range(0,result):
	    try:
		os.close(fd)
	    except OSError: pass
	os.open(dev_null,os.O_RDWR)
	os.dup2(0,1)
	os.dup2(0,2)

	pid=os.getpid()
	if os.path.exists(pid_file):
	    pidf=open(pid_file, 'r')
	    pid_old=int(pidf.readline())
	    if pid!=pid_old:
		if not os.path.exists('/proc/'+str(pid_old)):
		    os.remove(pid_file)
		    fh=open(pid_file, 'w')
		    print(pid,file=fh)
		    fh.close()
		else:
		    syslog.syslog('Error: Daemon already launched')
		    exit(1)

	if os.path.exists(pipe_file): os.remove(pipe_file)
	os.mkfifo(pipe_file)
	self.pipe=os.open(pipe_file,os.O_RDONLY|os.O_NONBLOCK)
	syslog.syslog('Daemon launched')
	verify=VerifyLiveClassic()
	t_point=time.time()
	while 1:
	    command=os.read(self.pipe,max_length)
	    if command:
		(trash,host,address,state,state_type,attempt)=command.split(';')
		verify.check_state(host,address,state,state_type,attempt)
		t_point=time.time()
	    verify.send_msg()
	    time.sleep(0.5)
	    if time.time()-t_point>self.t_lapse: break

    def __del__(self):
	if self.pipe: 
	    self.pipe.close()
	    os.remove(pid_file)

def MakeDetach():
    try: pid = os.fork()
    except OSError,e: raise Exception, "%s [%d]" % (e.strerror, e.errno)
    if pid==0:
	os.setsid()
	try: pid = os.fork()
	except OSError,e: raise Exception, "%s [%d]" % (e.strerror, e.errno)
	if pid==0:
	    bit=GoDaemon()
	else: os._exit(0)
    else: os._exit(0)

if __name__ == '__main__':
    MakeDetach()

