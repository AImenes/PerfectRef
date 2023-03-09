import itertools

class Query:
	def __init__(self, head, body, dict_of_variables, query_structure = None):
		self.head = head
		self.body = body
		self.dict_of_variables = dict_of_variables
		self.query_structure = query_structure
	
	def __repr__(self):
		return repr(vars(self))

	def __eq__(self, other_instance):
		return self.original_entry_name == other_instance.original_entry_name

	def get_head(self):
		return self.head

	def get_body(self):
		return self.body

	def get_dict_of_variables(self):
		return self.dict_of_variables

	def modify_body(self, body):
		self.body = body


class QueryBody:
		def __init__(self, body):
			self.body = body
			self.processed = False

		def __repr__(self):
			return repr(vars(self))

		def __eq__(self, other_body):
			return self.body == other_body

		def get_body(self):
			return self.body

		def set_process_status(self, processed):
			self.processed = processed

		def is_processed(self):
			return self.processed

		def contains_duplicates(self):
			for pair in itertools.combinations(self.body, 2):
				g1, g2 = pair
				if g1 == g2:
					return True
			return False

		
				
