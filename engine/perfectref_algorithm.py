from .utils.tau import tau
from .utils.reduce import reduce
from .utils.unify import unify
from .utils.atoms_obtained import atoms_obtained

def perfectref(q, T):
	PR = [q]
	PR_prime = list()

	while (PR_prime != PR):
		
		PR_prime = PR

		for q in PR_prime:

			for g in q.get_body():

				for PI in T:

					if PI.is_applicable(g):

						PR.append(atom_obtained(g, PI))

			#if g1 and g2 unify

				#PR.append(tau(reduced(q, g1, g2)))
	return PR