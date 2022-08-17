import owlready2

def loadOntology(path):
	onto = owlready2.get_ontology(path).load()
	return onto