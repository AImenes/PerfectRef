from .classes.atom import AtomConcept, AtomConstant, AtomRole
from .classes.entry import Constant, Variable
from .classes.query import QueryBody
from .query_parser import update_body
import copy

#ReduceMethod
# Should return the most general unifier between g1 and g2
# Recursively written in accordance with PerfectRef Paper

def unify_entries(e1,e2):
    if e1.get_bound() and e2.get_bound() and e1 == e2:
        return e1
    elif e1.get_bound() and not e2.get_bound():
        return e1
    elif not e1.get_bound() and e2.get_bound():
        return e2
    else:
        return Variable("?_", {'is_distinguished': False, 'in_body': False, 'is_shared': False})
    

# Unifiying atoms. Top of the tree. Initiated by the method "reduce". Takes two atoms and returns an object of the most general unifier
def unify_atoms(g1,g2):

    #if both are Concepts
    if isinstance(g1, AtomConcept) and isinstance(g2, AtomConcept):
        return AtomConcept(g1.get_name(), unify_entries(g1.get_var1(), g2.get_var1()), g1.get_iri())

    #if both are Roles
    elif isinstance(g1, AtomRole) and isinstance(g2, AtomRole):
        return AtomRole(g1.get_name(), unify_entries(g1.get_var1(), g2.get_var1()), unify_entries(g1.get_var2(), g2.get_var2()), g1.get_inversed(), g1.get_iri())

    # if both are constants
    elif isinstance(g1, AtomConstant) and isinstance(g2, AtomConstant):
        return AtomConstant(g1.get_name(), g1.get_value(), g1.get_iri())

    else:
        print("Error unifying atoms")
        return None


# Reducing the pair of two atoms
def reduce(q, pair):
    new_pair = copy.deepcopy(pair)
    new_q = copy.deepcopy(q)
    # Split atoms
    g1, g2 = new_pair

    # Start recursion for getting the most general unifier
    new_atom = unify_atoms(g1, g2)
    
    new_body = list()
    for g in new_q:
        if not (g == g1 or g == g2):
            new_body.append(g)
    
    new_body.append(new_atom)

    ##need to update entries variables
    new_body = update_body(QueryBody(new_body))
    
    return new_body

