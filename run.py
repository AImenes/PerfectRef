# IMPLEMENTATION OF ALGORITHM: PERFECTREF
# 
# This code is written by Anders Imenes
from engine.query_parser import parse_query
from engine.ontology_parser import import_ontology
from engine.ontology_parser import get_axioms
from engine.perfectref_algorithm import perfectref


import owlready2

def main():
	#Load Ontology
	path = "engine/ontologies/Test3.owl"
	onto = import_ontology(path)
	PIs = get_axioms(onto, True)
	query_string = "q(?x) :- Professor(?x)^teachesTo(?x, ?y)"
	q = parse_query(query_string)
	print(q)

	#Get input. Example query q: q(?x) :- Pizza(?x)^hasIngredient(?x, 5)
	#PR = perfectref(q, onto)

	#Run Algorithm

	#Save output


if __name__ == "__main__":
	main()
else:
	print("Please run the PerfectRef-file.")