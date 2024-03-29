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

	def __eq__(self, other_instance):
		return self.iri == other_instance.iri

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
	def __init__(self, name, iri, answer = None):
		self.name = name
		self.iri = iri
		self.answer = answer
		self.namespace = None

	def __repr__(self):
		return repr(vars(self))

	def __eq__(self, other_instance):
		return self.iri == other_instance.iri

	def get_name(self):
		return self.name
	
	def set_name(self, name):
		self.name = name
	
	def get_iri(self):
		return self.iri
	
	def set_iri(self, iri):
		self.iri = iri

	def get_answer(self):
		return self.answer
	
	def set_answer(self, answer):
		self.answer = answer

	def set_namespace(self, namespace):
		self.namespace = namespace

	def get_namespace(self):
		return self.namespace


class AtomConstant(Atom):
	def __init__(self, name, value, iri = None):
		super().__init__(name, iri)
		self.value = value

	def get_value(self):
		return self.value

class AtomConcept(Atom):
	def __init__(self, name, var1, iri = None):
		super().__init__(name, iri)
		self.var1 = var1
	
	def __eq__(self, other_instance):
		return super().__eq__(other_instance) and self.var1 == other_instance.var1


	def get_var1(self):
		return self.var1

	def modify(self, test):
		self.var1 = test

	def get_entries(self):
		return [self.var1]

class AtomRole(Atom):
	def __init__(self, name, var1, var2, inversed, iri = None):
		super().__init__(name, iri)
		self.var1 = var1
		self.var2 = var2
		self.inversed = inversed

	def __eq__(self, other_instance):
		if isinstance(other_instance, AtomRole):
			return super().__eq__(other_instance) and self.var1 == other_instance.var1 and self.var2 == other_instance.var2
		return False

	def get_var1(self):
		return self.var1

	def get_var2(self):
		return self.var2

	def get_inversed(self):
		return self.inversed

	def get_entries(self):
		return [self.var1, self.var2]

class AtomInverse(AtomRole):
	def __init__(self, atom):
		self.atom = atom
	
	def get_atom(self):
		return self.atom



