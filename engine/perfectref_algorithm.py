from .utils.reduce import reduce
from .utils.unify import unifiable
from .atoms_obtained import new_query
from .query_parser import update_processed_status
import itertools
import copy

def perfectref(q_instance, T):
	PR = [q_instance]
	PR_prime = list()

	while (PR_prime != PR):
		
		PR_prime = copy.deepcopy(PR)

		#equality-tester
		if (PR_prime == PR):
			print("yey")

		for q in PR_prime:

			if not q.is_processed():

				query_body = q.get_body()

				#This is needed if the query originally contains duplicates, s.t, we dont receive a nested error	
				if not q.contains_duplicates():

					# a
					for g in query_body:

						for PI in T:

							#Needs to implement: is not a query already and not equal on both sides
							if PI.is_applicable(g, PR):

								new_q = new_query(q, g, PI)

								#If it is not already entailed
								if not new_q in PR:
									PR.append(new_q)

				# b
				#if g1 and g2 unify
				if len(query_body) > 1:
					
					# for every 
					for pair in itertools.combinations(query_body, 2):

						if unifiable(pair):

							#If it is not already entailed
							new_q = reduce(query_body, pair)
							if not new_q in PR:
								PR.append(new_q)

				update_processed_status(q, PR, True)
				

	return PR