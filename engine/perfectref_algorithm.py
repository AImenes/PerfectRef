from .utils.tau import tau
from .utils.reduce import reduce
from .utils.unify import unify, unifiable
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

				# a
				for g in query_body:

					for PI in T:

						if PI.is_applicable(g):

							PR.append(new_query(q, g, PI))

				# b
				#if g1 and g2 unify
				if len(query_body) > 1:
					
					# for every 
					for pair in itertools.combinations(query_body, 2):

						if unifiable(pair):

							PR.append(tau(reduce(query_body, pair)))

				
				update_processed_status(q, PR, True)
				

	return PR