class Query:
	def __init__(self, head, body, dict_of_variables):
		self.head = head
		self.body = body
		self.dict_of_variables = dict_of_variables
	
	def __repr__(self):
		return repr(vars(self))

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

		def __repr__(self):
			return repr(vars(self))

		def get_body(self):
			return self.body
