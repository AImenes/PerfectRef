import owlready2
from .classes.query import Query
from .classes.atom import Atom
from .classes.entry import Entry
from .classes.entry import Variable
from .classes.entry import Constant

#q(?x) :- Pizza(?x)^hasIngredient(?x, ?y)

def query_parser(query_string):
	q = Query(query_string)
	head = Atom(q.get_head())
	body = list()
	
	for g in q.get_body():
		body.append(Atom(g))

	return True
	




