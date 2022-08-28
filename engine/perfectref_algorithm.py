from .utils.tau import tau
from .utils.reduce import reduce
from .utils.unify import unify
from .atoms_obtained import atoms_obtained
from .atoms_obtained import new_query

def perfectref(q_instance, T):
	PR = [q_instance]
	PR_prime = list()

	while (PR_prime != PR):
		
		PR_prime = PR

		for q in PR_prime:

			for g in q:

				for PI in T:

					if PI.is_applicable(g):

						PR.append(new_query(q, g, PI))

			#if g1 and g2 unify

				#PR.append(tau(reduced(q, g1, g2)))
	return PR