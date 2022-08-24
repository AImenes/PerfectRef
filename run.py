# IMPLEMENTATION OF ALGORITHM: PERFECTREF
# 
# This code is written by Anders Imenes
from engine.utils.ontology_parser import loadOntology
from engine.query_parser import parse_query
from engine.ontology_parser import import_ontology
from engine.ontology_parser import get_axioms
from engine.logic import atom_obtained

import owlready2

def main():
	#Load Ontology
	path = "engine/ontologies/Test3.owl"
	onto = import_ontology(path)
	PIs = get_axioms(onto)
	query_string = "q(?x) :- Professor(?x)^teachesTo(?x, ?y)"
	q = parse_query(query_string)
	print(q)

	#Get input. Example query q: q(?x) :- Pizza(?x)^hasIngredient(?x, 5)
	PR = PerfectRef(q, onto)

	#Run Algorithm

	#Save output



def PerfectRef(q, T):
	PR = [q]
	PR_prime = list()

	while (PR_prime != PR):
		
		PR_prime = PR

		for q in PR_prime:

			for g in q.get_body():

				for PI in T:

					if PI.is_applicable(g):

						PR.append(atom_obtained(g, PI))

			#if g1 and g2 unify

				#PR.append(tau(reduced(q, g1, g2)))
	return PR



if __name__ == "__main__":
	main()
else:
	print("Please run the PerfectRef-file.")