class Query:
	def __init__(self, query_string):
		self.q = query_string
		try:
			head, body = self.q.split(":-")
			#head
			head = head.strip()
			self.head = head

			#body
			self.body = list()
			body = (body.strip()).split("^")
			for g in body:
				self.body.append(g)
		except:
			print("ERROR: The Query String should contain ':-' to separate head and body.")
			self.head = ""
			self.body = list()


	def get_head(self):
		return self.head

	def get_body(self):
		return self.body
