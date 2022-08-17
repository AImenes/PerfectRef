class atom:
	def __init__(self, atomString):
		self.name = atomString.partition("(")[0]
		if "," in atomString:
			self.arity = len(atomString.split(","))
		else:
			self.arity = 1

		self.variable = atomString.partition("?")[2][0]

		print(self.name, self.arity, self.variable)

#Constant

#Unary

#Binary

#N-ary




