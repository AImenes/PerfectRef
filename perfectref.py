# IMPLEMENTATION OF ALGORITHM: PERFECTREF
# 
# This code is written by Anders Imenes
from .engine.query_parser import parse_query
from .engine.ontology_parser import import_ontology
from .engine.atoms_obtained import get_axioms
from .engine.perfectref_algorithm import perfectref
from .engine.extractor import export_query_to_file, print_query
from .engine.classes.atom import AtomConcept, AtomConstant, AtomRole


def get_entailed_queries(ontology, string):

	t_box = get_axioms((import_ontology(ontology)), True)
	q = parse_query(string)
	q_head = q.get_head()
	q_body = q.get_body()
	PR = perfectref(q_body, t_box)
	
	#Exporting the results
	#export_query_to_file(PR, string, q_head)
	print_query(PR, string, q_head)
	return PR

def parse_output(unparsed_query, PR):
	queries = {}
	queries['original'] = unparsed_query
	queries['entailed'] = []
	q = parse_query(unparsed_query)
	q_head = q.get_head()
	
	for cq in PR:
		head = q_head.get_name() + "(" + q_head.get_var1().get_represented_name() + ") :- "
		body = ""

		length_of_q = len(cq.get_body())
		counter = 0

		for g in cq.get_body():
			
			if isinstance(g, AtomConstant):
				pass
			elif isinstance(g, AtomConcept):
				body += g.get_name() + "(" + g.get_var1().get_represented_name() + ")"
			else:
				body += g.get_name() + "(" + g.get_var1().get_represented_name() + "," + g.get_var2().get_org_name() + ")"

			if (counter < length_of_q - 1):
				body += "^"

			counter += 1
		query = head + body
		queries["entailed"].append(query)
	return queries

def main():
	#Load Ontology
	path = "engine/ontologies/Test2.owl"

	#Different queries for testing
#	query_string = "q(?x) :- Student(?x)"
#	query_string = "q(?x) :- Student(?x)^Student(?x)^Student(?x)"
#	query_string = "q(?x) :- Professor(?x)^teachesTo(?x, ?y)"
	query_string = "q(?x) :- teachesTo(?x,?y)^hasTutor(?y,?_)"

	PR = get_entailed_queries(path, query_string)
	print("hey")