class Atom:
	def __init__(self, name, entry_list):
		self.name = name
		self.entries = entry_list

	def __repr__(self):
		return repr(vars(self))

	def get_name(self):
		return self.name

	def get_entries(self):
		return self.entries
