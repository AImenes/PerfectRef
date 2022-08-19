class Query:
	def __init__(self, head, body):
		self.head = head
		self.body = body
	
	def __repr__(self):
		return repr(vars(self))

	def get_head(self):
		return self.head

	def get_body(self):
		return self.body
