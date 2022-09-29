# IMPLEMENTATION OF ALGORITHM: PERFECTREF
# 
# This code is written by Anders Imenes
from engine.query_parser import parse_query
from engine.ontology_parser import import_ontology
from engine.atoms_obtained import get_axioms
from engine.perfectref_algorithm import perfectref
from engine.extractor import export_query_to_file


def main():
	#Load Ontology
	path = "engine/ontologies/Test2.owl"
	onto = import_ontology(path)
	t_box = get_axioms(onto, True)

	#Different queries for testing
	query_string = "q(?x) :- Professor(?x)^teachesTo(?x, ?y)"
#	query_string = "q(?x) :- Person(?x)^teachesTo(?x, ?y)"
#	query_string = "q(?x) :- Student(?x)" #this works
#	query_string = "q(?x) :- Student(?x)^Student(?x)^Student(?x)"
#	query_string = "q(?x) :- teachesTo(?x,?y)^hasTutor(?y,?_)"

	#Parsing
	q = parse_query(query_string)
	q_head = q.get_head()
	q_body = q.get_body()

	#Running the algorithm
	PR = perfectref(q_body, t_box)

	#Exporting the results
	export_query_to_file(PR, query_string, q_head)


if __name__ == "__main__":
	main()
else:
	print("Please run the PerfectRef-file.")