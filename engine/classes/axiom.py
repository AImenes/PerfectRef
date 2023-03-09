from owlready2 import *
from .atom import AtomConstant, AtomConcept, AtomRole, AtomInverse

class Axiom:
    def __init__(self):
        pass

class LogicalAxiom(Axiom):
    def __init__(self, left, right):
        super().__init__()
        self.left = left
        self.right = right
        
    def get_left(self):
        return self.left

    def get_right(self):
        return self.right
    
    def is_applicable(self, atom, queries):

        #Check if the query it proposes does not already exist

        #Verify that we dont create rules that are completely equal on both sides.
        #if atom.get_name() == self.right.name and 

        #if atom != 
        #CONCEPTS - SUBCLASSES
        # A PI, I, is applicable to an atom A(x) if I has A in its right-hand side.
        if isinstance(atom, AtomConcept):        
            if isinstance(self.right, ThingClass) and (atom.get_iri() == self.right.iri):
                return True
                
        #ROLES - DOMAINS, RANGES and SUB PROPERTIES
        if isinstance(atom, AtomRole):
            if type(self.right) == Or:
                print(self.right.Classes[0])

            # A PI I is applicable to an atom P(x1, x2) if x1 =_ and the right-hand side of I is ∃P−
            if isinstance(self.right, Inverse):
                if self.right.property.iri == atom.get_iri():
                    if (atom.get_var1().get_unbound()):
                        return True

            # A PI I is applicable to an atom P(x1, x2) if  x2 = _ and the right-hand side of I is ∃P
            elif (atom.get_iri() == self.right.iri):        
                if (atom.get_var2().get_unbound()) and isinstance(self.right, ObjectPropertyClass):
                    return True

        # I is a role inclusion assertion and its right-hand side is either P or P−   
            if (atom.get_var1().get_bound() and atom.get_var2().get_bound()):
                if (isinstance(self.left, ObjectPropertyClass) or isinstance(self.left, Inverse)):
                
                    if isinstance(self.right, Inverse):
                        if atom.get_iri() == self.right.property.iri:
                            return True
                    
                    if isinstance(self.right, ObjectPropertyClass):
                        if atom.get_iri() == self.right.iri:
                            return True


        return False
