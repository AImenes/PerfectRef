# IMPLEMENTATION OF ALGORITHM: PERFECTREF
# 
# This code is written by Anders Imenes
from .engine.query_parser import parse_query
from .engine.ontology_parser import import_ontology
from .engine.atoms_obtained import get_axioms
from .engine.perfectref_algorithm import perfectref
from .engine.extractor import export_query_to_file


def get_entailed_queries(ontology, string):

	t_box = get_axioms((import_ontology(ontology)), True)
	q = parse_query(string)
	q_head = q.get_head()
	q_body = q.get_body()
	PR = perfectref(q_body, t_box)
	
	#Exporting the results
	export_query_to_file(PR, string, q_head)
	return PR

def main():
	#Load Ontology
	path = "engine/ontologies/Test2.owl"

	#Different queries for testing
#	query_string = "q(?x) :- Student(?x)"
#	query_string = "q(?x) :- Student(?x)^Student(?x)^Student(?x)"
#	query_string = "q(?x) :- Professor(?x)^teachesTo(?x, ?y)"
	query_string = "q(?x) :- teachesTo(?x,?y)^hasTutor(?y,?_)"

	PR = get_entailed_queries(path, query_string)

