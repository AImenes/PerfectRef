from .classes.atom import AtomConcept, AtomRole

def unifiable(pair):
    g1, g2 = pair

    #If they are different class-types
    if type(g1) != type(g2):
        return False

    #If they are class, but are different concepts or roles
    if g1.iri != g2.iri:
        return False

    #If they are concept (doesnt need to check g2 as then first if-statement would have triggered)
    if isinstance(g1, AtomConcept):

        # and both entries are bound but not the same one.
        if (g1.var1.bound and g2.var1.bound and g1 != g2):
            return False

    #If they are roles (doesnt need to check g2 as then first if-statement would have triggered)
    if isinstance(g1, AtomRole):

        # If the variable 1 position in atom g1 and g2 are bound, but not the same variable
        if (g1.var1.bound and g2.var1.bound) and (g1.var1.original_entry_name != g2.var1.original_entry_name):
            return False
        
        # If the variable 2 position in atom g1 and g2 are bound, but not the same variable
        if (g1.var2.bound and g2.var2.bound) and (g1.var2.original_entry_name != g2.var2.original_entry_name):
            return False

    #It non of the previous steps are triggered, the atoms are unifiable.
    return True
