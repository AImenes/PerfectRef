
from engine.classes.atom import AtomConcept, AtomRole

def unifiable(pair):
    g1, g2 = pair

    #If they are different class-types
    if type(g1) != type(g2):
        return False

    #If they are class, but are different concepts or roles
    if g1.get_name() != g2.get_name():
        return False

    #If they are concept (doesnt need to check g2 as then first if-statement would have triggered)
    if isinstance(g1, AtomConcept):

        # and both entries are bound but not the same one.
        if (g1.get_var1().get_bound() and g2.get_var1().get_bound() and g1 != g2):
            return False

    #If they are roles (doesnt need to check g2 as then first if-statement would have triggered)
    if isinstance(g1, AtomRole):

        #and all variables are bound
        if (g1.get_var1().get_bound() and g1.get_var2().get_bound() and g2.get_var1().get_bound() and g2.get_var2().get_bound()):
            
            #and they are not the same
            if not (g1.get_var1() == g2.get_var1() and g1.get_var2() == g2.get_var2()):
                return False

    return True
