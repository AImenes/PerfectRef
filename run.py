# IMPLEMENTATION OF ALGORITHM: PERFECTREF
# 
# This code is written by Anders Imenes
from engine.algorithm.ontologyParser import *
from engine.logic.queryParser import *
from engine.structure
import owlready2

def main():
	#Load Ontology
	onto = loadOntology("ontologies/mytest.owl")
	q = "q(?x) :- Pizza(?x)^hasIngredient(?x, ?y)"
	p = QueryParser(onto, q)
	#p.showTail()

	#Get input. Example query q: q(?x) :- Pizza(?x)^hasIngredient(?x, ?y)


	#Run Algorithm

	#Save output


if __name__ == "__main__":
	main()
else:
	print("Please run the PerfectRef-file.")