#Superclass
class Entry:
	def __init__(self, entry_name):
		self.original_entry_name = entry_name

	def __repr__(self):
		return repr(vars(self))


#Subclass Variable
class Variable(Entry):
	def __init__(self, entry_name, dict_for_states):
		super().__init__(entry_name)
		self.distinguished = dict_for_states['is_distinguished']
		self.body = dict_for_states['in_body']
		self.shared = dict_for_states['is_shared']
		self.bound = dict_for_states['is_bound']
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

