import sympy

#Inputs: Conjunctive query cg_q, TBox T
def perfectRef(cg_q, T):

	#Adding to list-variable
	PR = [cg_q]

	#Working variable
	PR_prime = PR

	#Start loop
	while (PR_prime != PR):

		#For every query object in the list PR_prime
		for q in PR_prime:

			#For each atom in the query
			for g in q:

				#For each positive inclusion PI, I, in the TBox. That is, rules domains and ranges.
				for I in T:

					#If positive inclusion, I, is applicable to the Tbox T
					If something:

						#then we include it in the new union of conjunctive queries
						PR += something_that_depends_on_format

					



	#Outputs union of Conjunctive Queries PR
	return PR

