# IMPLEMENTATION OF ALGORITHM: PERFECTREF
# 
# This code is written by Anders Imenes
from engine.query_parser import parse_query
from engine.ontology_parser import import_ontology
from engine.atoms_obtained import get_axioms
from engine.perfectref_algorithm import perfectref


import owlready2

def main():
	#Load Ontology
	path = "engine/ontologies/Test4.owl"
	onto = import_ontology(path)
	t_box = get_axioms(onto, True)
#	query_string = "q(?x) :- Professor(?x)^teachesTo(?x, ?y)"
	query_string = "q(?x) :- Person(?x)^teachesTo(?x, ?y)"
	q = parse_query(query_string)
	q_body = q.get_body()
	print(q)

	PR = perfectref(q_body, t_box)


if __name__ == "__main__":
	main()
else:
	print("Please run the PerfectRef-file.")