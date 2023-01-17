#Imports
from .reduce import reduce
from .unify import unifiable
from .atoms_obtained import new_query
from .query_parser import update_processed_status
import itertools
import copy

# # # PERFECTREF # # # 
def perfectref(q_instance, T):

	#Making the initial query iterable
	PR = [q_instance]

	#Working list PR_prime of the entailes queries in PR.
	PR_prime = list()

	#Run until there are no changes
	while (PR_prime != PR):
		
		#Make a deep copy for each iteration (is necessary in order not to mess up bounded variables for previous queries)
		PR_prime = copy.deepcopy(PR)

		#For every query in the list 
		for q in PR_prime:

			#Check if the query is already processed by the algorithm
			if not q.is_processed():

				#Extract the body from the query
				query_body = q.get_body()

				#This is needed if the query originally contains duplicates (i.e., is not efficiently written), s.t, we dont receive a nested error.
				if not q.contains_duplicates():

					# Task A: Add new entailed queries
					# for every atom the query´s body
					for g in query_body:

						#For every positive inclusion in the T-Box
						for PI in T:
							
							#Validate if the PI is applicable with the atom g
							if PI.is_applicable(g, PR):

								#Construct the new query
								new_q = new_query(q, g, PI)

								#If the query is not already entailed from previous processes nor it is None
								if not (new_q in PR or new_q is None):

									# Add new query to PR
									PR.append(new_q)



				# Task B: Unify atoms of the same kind (as a result of entailments)

				#if the query contains more than 1 atom, which is a requirement for unifying
				if len(query_body) > 1:
					
					# for every possible pair within the body of the query
					for pair in itertools.combinations(query_body, 2):

						# checks if they are unifiable
						if unifiable(pair):

							# construct new query by reducing it
							new_q = reduce(query_body, pair)

							# If it is not already entailed in PR
							if not new_q in PR:

								# Add it.
								PR.append(new_q)


				# Set the query q in PR_prime as processed, s.t., it wont be processed again
				update_processed_status(q, PR, True)


	# return the list of queriess
	return PR