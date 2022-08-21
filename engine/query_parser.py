from .classes.query import Query
from .classes.atom import Atom
from .classes.entry import Entry
from .classes.entry import Variable
from .classes.entry import Constant

"""
	METHODS FOR PARSING

		parse_query					Splits head and body, creates a dictionary for variables (which is within the object). Return type Class:Query

		parse_head					Since the head per definition contains distinguished variables, the boolean variable is_distinguised is set to True. 
 									This is passed to Atom-parser. It returns a Class:Atom, 

		parse_body					Since the head per definition contains distinguished variables, the boolean variable in the body is_distinguised is set to False. 
									This is passed to Atom-parser. It returns a list of Class:Atom.

		parse_atom					Extracts entry tokens from a Atom, and returns an Atom with a list of entries. Returns either 

		parse_entry					Parses each entry as either a Variable or Constant. Returns a Class:Variable or Class:Constant


	METHODS FOR UTILITIES

		extract_entry_tokens		Parses the entire atom, and extracts the variables or constants
	
		parse_dict_of_variables		Checks if variable already exists. That is, a shared (bound) variable. Returns Boolean value.

		update_entries				After the recursion is complete, all the entries are detected and decided whether its bound, shared or unbound. This updates those objects.

"""

## PARSING
def parse_query(query_string):
	# Split head and body
	head_string, body_string = query_string.split(":-")
	dictionary_of_variables = {}

	# Remove trailing spaces
	head_string = head_string.strip()
	body_string = body_string.strip()

	# Recurse
	head = parse_head(head_string, dictionary_of_variables)
	body = parse_body(body_string, dictionary_of_variables)

	#Update the Boolean variables after the recursion
	update_entries(head, dictionary_of_variables)
	[update_entries(b, dictionary_of_variables) for b in body]

	#Return a Query-object
	return Query(head, body, dictionary_of_variables)

def parse_head(head_string,dictionary_of_variables):
	is_distinguished = True 
	return parse_atom(head_string,is_distinguished, dictionary_of_variables) 

def parse_body(body_string, dictionary_of_variables):
	is_distinguished = False
	atom_str_list = body_string.split("^")
	return [parse_atom(atom_str,is_distinguished, dictionary_of_variables) for atom_str in atom_str_list] 

def parse_atom(atom_string, is_distinguished, dictionary_of_variables):
	#print(atom_string)
	name, arity, entry_str_list = extract_entry_tokens(atom_string)
	#print(name, arity, entry_str_list)
	return Atom(name, [parse_entry(token, is_distinguished, dictionary_of_variables) for token in entry_str_list])

def parse_entry(entry_string, is_distinguished, dictionary_of_variables):
	if entry_string.startswith("?"):
		return Variable(entry_string, parse_dict_of_variables(entry_string, is_distinguished, dictionary_of_variables))
	return Constant(entry_string)


#UTILITIES
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


def parse_dict_of_variables(entry_string, is_distinguished, dictionary_of_variables):
	
	# If the variable is known
	if entry_string in dictionary_of_variables:
		if dictionary_of_variables[entry_string]['in_body']:
			dictionary_of_variables[entry_string]['is_shared'] = True
		else:
			dictionary_of_variables[entry_string]['in_body'] = True

	#If the variable is new
	else:
		if is_distinguished:
			dictionary_of_variables[entry_string] = {'is_bound':False, 'is_distinguished':True, 'in_body': False, 'is_shared':False }
		else:
			dictionary_of_variables[entry_string] = {'is_bound':False, 'is_distinguished':False, 'in_body': True, 'is_shared':False }
		
	if dictionary_of_variables[entry_string]['is_shared'] or dictionary_of_variables[entry_string]['is_distinguished']:
		dictionary_of_variables[entry_string]['is_bound'] = True

	return dictionary_of_variables[entry_string]

def update_entries(atom, dict_of_variables):
	
	for entry in atom.get_entries():
		e = dict_of_variables[entry.get_org_name()]
		entry.update_values(e['is_distinguished'], e['in_body'], e['is_shared'], e['is_bound'])
