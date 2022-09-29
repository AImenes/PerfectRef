#from copy import deepcopy
from engine.classes.atom import AtomConcept, AtomConstant, AtomRole
from engine.classes.entry import Constant, Variable
from engine.classes.query import QueryBody
from engine.query_parser import update_body

#ReduceMethod
# Should return the most general unifier between g1 and g2

def unify_entries(e1,e2):
    if e1.get_bound() and e2.get_bound() and e1 == e2:
        return e1
    elif e1.get_bound() and not e2.get_bound():
        return e1
    elif not e1.get_bound() and e2.get_bound():
        return e2
    else:
        return Variable("?_", {'is_distinguished': False, 'in_body': False, 'is_shared': False})
    


def unify_atoms(g1,g2):

    if isinstance(g1, AtomConcept) and isinstance(g2, AtomConcept):
        return AtomConcept(g1.get_name(), unify_entries(g1.get_var1(), g2.get_var1()))

    elif isinstance(g1, AtomRole) and isinstance(g2, AtomRole):
        return AtomRole(g1.get_name(), unify_entries(g1.get_var1(), g2.get_var1()), unify_entries(g1.get_var2(), g2.get_var2()))

    elif isinstance(g1, AtomConstant) and isinstance(g2, AtomConstant):
        return AtomConstant(g1.get_name(), g1.get_value())

    else:
        print("Error unifying atoms")
        return None



def reduce(q, pair):
    g1, g2 = pair
    new_atom = unify_atoms(g1, g2)
    
    new_body = list()
    for g in q:
        if not (g == g1 or g == g2):
            new_body.append(g)
    
    new_body.append(new_atom)

    ##need to update entries variables
    new_body = update_body(QueryBody(new_body))
    
    ##

    return new_body

