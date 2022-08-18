# IMPLEMENTATION OF ALGORITHM: PERFECTREF
# 
# This code is written by Anders Imenes
from engine.utils.ontology_parser import loadOntology
from engine.query_parser import query_parser

import owlready2

def main():
	#Load Ontology
	#onto = loadOntology("ontologies/mytest.owl")
	query_string = "q(?x) :- Pizza(?x)^hasIngredient(?x, ?y)"
	q = query_parser(query_string)

	#p = QueryParser(onto, q)
	#p.showTail()

	#Get input. Example query q: q(?x) :- Pizza(?x)^hasIngredient(?x, ?y)


	#Run Algorithm

	#Save output


if __name__ == "__main__":
	main()
else:
	print("Please run the PerfectRef-file.")