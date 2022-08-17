import owlready2
from .atoms import atom

#q(?x) :- Pizza(?x)^hasIngredient(?x, ?y)

class QueryParser:
	def __init__(self, ontology, query):
		self.query = query
		self.ontology = ontology

		#Split into head and tail
		try:
			head, tail = self.query.split(':-')
			self.head = head.strip()
			self.tail = tail.strip()
		except:
			print("Could not find QuerySymbol: :- .")

		#separate Atoms
		atom_list = self.tail.split('^')
		for g in atom_list:
			current = atom(g)


		#print(atoms)
			




