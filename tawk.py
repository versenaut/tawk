#!/bin/env python
#
# This is tawk, a simplistic chat client for Verse.
#
# Requires a running instance of the tawkserv servlet connected to
# the Verse server.
#

VERSION = "0.1"

from Queue import Queue
import sys
from threading import Thread

import verse as v

from objmeth import Method,MethodGroup

global the_server_methods

the_avatar	   = -1L
the_channel	   = None
the_server_name	   = "tawksrv"
the_server	   = -1L
the_server_methods = None
the_client_methods = None

def cb_node_create(node_id, type, owner):
	if type == v.OBJECT:
		print "subscribing to", node_id
		v.send_node_subscribe(node_id)

def cb_node_name_set(node_id, name):
	global the_server_name, the_server
	if name == the_server_name:
		the_server = node_id
		print "** Found tawk servlet, it's node", node_id

def cb_o_method_group_create(node, group_id, name):
	global the_server, the_avatar, the_client_methods, the_server_methods
	if node == the_avatar:
		the_client_methods = MethodGroup(group_id)
		v.send_o_method_group_subscribe(node, group_id)
		v.send_o_method_create(node, group_id, ~0, "join",  [("channel", v.O_METHOD_PTYPE_STRING)])
		v.send_o_method_create(node, group_id, ~0, "leave", [("channel", v.O_METHOD_PTYPE_STRING)])
		v.send_o_method_create(node, group_id, ~0, "hear",  [("channel", v.O_METHOD_PTYPE_STRING), ("from", v.O_METHOD_PTYPE_STRING), ("msg", v.O_METHOD_PTYPE_STRING)])
	elif node == the_server:
		the_server_methods = MethodGroup(group_id)
		v.send_o_method_group_subscribe(node, group_id)

def cb_o_method_create(node_id, group_id, method_id, name, params):
	global the_avatar, the_server, the_server_methods, the_client_methods
	if node_id == the_avatar:
		the_client_methods.add(method_id, name, params)
	elif node_id == the_server:
		the_server_methods.add(method_id, name, params)
	else:
		print " unknown method", name

def cb_o_method_call(node_id, group_id, method_id, sender, params):
	global the_avatar, the_client_methods, the_channel
	if node_id == the_avatar and group_id == the_client_methods.id:
		name = the_client_methods.get(method_id)
		if name == "join":
			print "(Making", params[0][1], "the current channel)"
			the_channel = params[0][1]
		elif name =="leave":
			print "(No longer talking in", params[0][1] + ")"
		elif name == "hear":
			print params[0][1] + " " + params[1][1] + ": " + params[2][1]

def cb_connect_accept(my_avatar, address, host_id):	
	global the_avatar, the_methods
	print "--Connected as", my_avatar, "to", address
	v.send_node_index_subscribe(1 << v.OBJECT)
	v.send_node_name_set(my_avatar, "tawk")
	v.send_o_method_group_create(my_avatar, ~0, "tawk-client")
	the_avatar = my_avatar

_inputqueue = Queue()

def reader():
	try:
		line = ""
		while True:
			c = sys.stdin.read(1)
			if not c:	# EOF
				_inputqueue.put("QUIT", True)
				break
			elif c == "\n":
				_inputqueue.put(line, True)
				line = ""
			else:
				line += c
	except EOFError, e:
		print "blah"
		_inputqueue.put(EOFError)

if __name__ == "__main__":
	the_groups = []
	v.callback_set(v.SEND_CONNECT_ACCEPT,		cb_connect_accept)
	v.callback_set(v.SEND_NODE_CREATE,		cb_node_create)
	v.callback_set(v.SEND_NODE_NAME_SET,		cb_node_name_set)
	v.callback_set(v.SEND_O_METHOD_GROUP_CREATE,	cb_o_method_group_create)
	v.callback_set(v.SEND_O_METHOD_CREATE,		cb_o_method_create)
	v.callback_set(v.SEND_O_METHOD_CALL,		cb_o_method_call)

	server = "localhost"
	for a in sys.argv[1:]:
		if a.startswith("-ip="):
			server = a[4:]
		elif a.startswith("-help"):
			print "tawk client version %s written by Emil Brink." % VERSION
			print "Copyright (c) 2005 by PDC, KTH."
			print "Usage: tawk.py [-server=IP[:HOST]] [-help] [-version]"
			sys.exit(1)
		elif a.startswith("-version"):
			print VERSION
			sys.exit(0)
		else:
			print "Ignoring unknown option \"%s\"" % a
	v.send_connect("tawk", "<secret>", server, 0)

	t = Thread(target = reader)
	t.setDaemon(True)
	t.start()

	while True:
		v.callback_update(1000)
		l = ""
		try:
			l = _inputqueue.get(False)
		except:
			pass
		l = l.strip()
		if l == "QUIT":
			break
		if l != "":
#			print "got '%s'" % l
			if l.startswith("/info"):
				the_server_methods.call("info", the_server, l[5:].strip().split(' ', 1))
			elif l.startswith("/login"):
				the_server_methods.call("login", the_server, l[6:].strip().split(' ', 1))
			elif l.startswith("/logout"):
				the_server_methods.call("logout", the_server, l[7:].strip().split(' ', 1))
			elif l.startswith("/join"):
				the_server_methods.call("join", the_server, l[5:].strip().split(' ', 1))
			elif l.startswith("/leave"):
				the_server_methods.call("leave", the_server, l[6:].strip().split(' ', 1))
			elif the_channel != None:
				the_server_methods.call("say", the_server, [the_channel, l])
			else:
				print "Please first use /login to log in, then /join to join a channel."
