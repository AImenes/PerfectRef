import owlready2
from .classes.query import Query
from .classes.atom import Atom
from .classes.entry import Entry
from .classes.entry import Variable
from .classes.entry import Constant

#Example
# q(?x) :- Pizza(?x),hasIngredient(?x,?y)
	
def parse_query(query_string):
	#Split head and body
	head_string, body_string = query_string.split(":-")
	#Remove trailing spaces
	head_string = head_string.strip()
	body_string = body_string.strip()
	#Return a Query-object
	return Query(parse_head(head_string), parse_body(body_string))

def parse_head(head_string):
	return parse_atom(head_string) 

def parse_body(body_string):
	atom_str_list = body_string.split("^")
	return [parse_atom for atom_str in atom_str_list] 

def parse_atom(atom_string):
	print(atom_string)
	name, arity, entry_str_list = extract_entry_tokens(atom_string)
	print(name, arity, entry_str_list)
	return Atom(name, [parse_entry for token in entry_str_list])

def parse_entry(entry_string):
	if entry_string.starts_with("?"):
		return Variable(entry_string)
	return Constant(entry_string)

#Utils
def extract_entry_tokens(atom_string):
	entries_list = list()
	arity = 0
	name = ""

	#if a atom with arity = 0 (a constant)
	if (not ("(") in atom_string):
		arity = 0
		name = atom_string

	#if a atom with arity = 0, but with empty parantheses
	elif (("()") in atom_string):
		arity = 0
		name = atom_string.split(("("))[0]

	else:
	#if the atom contains entries
	#else if ((("(") in atom_string) and (("?" in atom_string) or ("_" in atom_string))):
		name, entries = atom_string.split("(", 1)
		entries = entries.replace(" ", "")
		entries = entries.rstrip(")")

		if not ((",") in entries):
			arity = 1
			entries_list.append(entries)
		else:
			entries = entries.split(",")
			for e in entries:
				entries_list.append(e)
			arity = len(entries)

	return name,arity,entries_list





