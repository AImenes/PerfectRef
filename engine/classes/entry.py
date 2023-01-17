#Superclass
class Entry:
	def __init__(self, entry_name):
		self.original_entry_name = entry_name

	def __repr__(self):
		return repr(vars(self))

	def __eq__(self, other_instance):
		return self.represented_name == other_instance.represented_name

	def get_org_name(self):
		return self.original_entry_name


#Subclass Variable
class Variable(Entry):
	def __init__(self, entry_name, dict_for_states):
		super().__init__(entry_name)
		self.distinguished = dict_for_states['is_distinguished']
		self.body = dict_for_states['in_body']
		self.shared = dict_for_states['is_shared']
		self.bound = self.shared or self.distinguished
		self.unbound = not self.bound

		if self.unbound:
			self.represented_name = "?_"
		else:
			self.represented_name = self.original_entry_name

	def get_represented_name(self):
		return self.represented_name

	def get_distinguished(self):
		return self.distinguished
	
	def get_body(self):
		return self.body

	def get_shared(self):
		return self.shared

	def get_bound(self):
		return self.bound

	def get_unbound(self):
		return self.unbound

	def update_values(self, distinguished, body, shared):
		self.distinguished = distinguished
		self.body = body
		self.shared = shared
		self.bound = self.shared or self.distinguished
		self.unbound = not self.bound

		if self.unbound:
			self.represented_name = "?_"
		else:
			self.represented_name = self.original_entry_name


#Subclass Constant
class Constant(Entry):
	def __init__(self, entry_name):
		super().__init__(entry_name)
		self.bound = True

