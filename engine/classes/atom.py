class AtomParser:
	def __init__(self, name, entry_list):
		self.name = name
		self.entries = entry_list
		self.num_of_entries = len(self.entries)

		if self.num_of_entries == 0:
			self.type = "CONSTANT"
			self.var1 = None
			self.var2 = None

		elif self.num_of_entries == 1:
			self.type = "CONCEPT"
			self.var1 = self.entries[0]
			self.var2 = None

		else:
			self.type = "ROLE"
			self.var1 = self.entries[0]
			self.var2 = self.entries[1]

	def __repr__(self):
		return repr(vars(self))

	def get_name(self):
		return self.name

	def get_entries(self):
		return self.entries

	def get_type(self):
		return self.type

	def get_var1(self):
		return self.var1
	
	def get_var2(self):
		return self.var2

class Atom:
	def __init__(self, name):
		self.name = name

	def __repr__(self):
		return repr(vars(self))

	def get_name(self):
		return self.name


class AtomConstant(Atom):
	def __init__(self, name, value):
		super().__init__(name)
		self.value = value

	def get_value(self):
		return self.value

class AtomConcept(Atom):
	def __init__(self, name, var1):
		super().__init__(name)
		self.var1 = var1

	def get_var1(self):
		return self.var1

class AtomRole(Atom):
	def __init__(self, name, var1, var2):
		super().__init__(name)
		self.var1 = var1
		self.var2 = var2

	def get_var1(self):
		return self.var1

	def get_var2(self):
		return self.var2