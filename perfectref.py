# IMPLEMENTATION OF ALGORITHM: PERFECTREF
# 
# This code is written by Anders Imenes
from .engine.query_parser import parse_query
from .engine.ontology_parser import import_ontology
from .engine.iri_namespace import get_iri_and_namespace
from .engine.atoms_obtained import get_axioms
from .engine.perfectref_algorithm import perfectref
from .engine.classes.atom import AtomConcept, AtomConstant, AtomRole


def get_entailed_queries(ontology, string, parse = True):
	onto = import_ontology(ontology)
	tbox = get_axioms(onto, True)
	
	if parse:
		q = parse_query(string)
		q_head = q.head
		q_body = q.body
		# get IRI and namespace
		get_iri_and_namespace(q,onto)
	else:
		q_head = string.get_head()
		q_body = string.get_body()

	PR = perfectref(q_body, tbox)
	
	#Exporting the results
	#export_query_to_file(PR, string, q_head)
	#print_query(PR, string, q_head)
	return PR

def parse_output(unparsed_query, PR):
	queries = {}
	queries['original'] = unparsed_query
	queries['entailed'] = []
	q = parse_query(unparsed_query)
	q_head = q.head
	
	for cq in PR:
		head = q_head.name + "(" + q_head.var1.represented_name + ") :- "
		body = ""

		length_of_q = len(cq.body)
		counter = 0

		for g in cq.body:
			
			if isinstance(g, AtomConstant):
				pass
			elif isinstance(g, AtomConcept):
				body += g.name + "(" + g.var1.represented_name + ")"
			else:
				body += g.name + "(" + g.var1.represented_name + "," + g.var2.original_entry_name + ")"

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