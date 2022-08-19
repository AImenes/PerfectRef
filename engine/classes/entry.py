#Superclass
class Entry:
	def __init__(self, name):
		self.name = name
		self.isBound = True

	def __repr__(self):
		return repr(vars(self))


#Subclass Variable
class Variable(Entry):
	def __init__(self, name):
		super().__init__(name)
	#	self.bound = True
	#	self.bind = True
	#	self.unbind = False


	def to_string(self):
		if self.bound:
			return "?" + self.name
		else:
			return "_"


#Subclass Constant
class Constant(Entry):
	def __init__(self, name):
		super().__init__(name)

