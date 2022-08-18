import owlready2
from .classes.query import Query
from .classes.atom import Atom
from .classes.entry import Entry
from .classes.entry import Variable
from .classes.entry import Constant

#q(?x) :- Pizza(?x)^hasIngredient(?x, ?y)

def query_parser(query_string):
	q = Query(query_string)
	head = q.get_head()
	body = q.get_body()
	print(body)

	return True
	




