#
# Support code for dealing with Verse object node methods and method groups.
#

import verse as v

class Method:
	def __init__(self, id, name, params):
		self.id     = int(id)
		self.name   = name
		self.params = params

	def call(self, node_id, group_id, args):
		v.send_o_method_call(node_id, group_id, self.id, 0, tuple(args))

class MethodGroup:
	def __init__(self, id):
		self.id    = int(id)
		self.methods = {}

	def add(self, id, name, params):
		self.methods[name] = Method(id, name, params)

	def has(self, name):
		try:	m = self.methods[name]
		except:	return False
		return True

	def get(self, id):
		for m in self.methods.values():
			if m.id == id:
				return m.name
		return ""

	def call(self, name, node_id, args):
		try:	m = self.methods[name]
		except: return
		m.call(node_id, self.id, args)
