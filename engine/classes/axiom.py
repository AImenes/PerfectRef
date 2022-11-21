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
            if isinstance(self.right, ThingClass) and (atom.get_name() == self.right.name):
                return True
                
        #ROLES - DOMAINS, RANGES and SUB PROPERTIES
        # A PI I is applicable to an atom P(x1, x2) if  x2 = _ and the right-hand side of I is ∃P
        if isinstance(atom, AtomRole):
            if type(self.right) == Or:
                print(self.right.Classes[0])
            if (atom.get_name() == self.right.name):        
                if (atom.get_var2().get_unbound()) and isinstance(self.right, ObjectPropertyClass) and isinstance(self.left, ThingClass):
                    return True

            # A PI I is applicable to an atom P(x1, x2) if x1 =_ and the right-hand side of I is ∃P−
            if isinstance(self.right, Inverse):
                if self.right.property.name == atom.get_name():
                    if (atom.get_var1().get_unbound() and isinstance(self.left, ThingClass)):
                        return True

        # I is a role inclusion assertion and its right-hand side is either P or P−   
            if (atom.get_name() == self.right.name) and ((isinstance(self.right, ObjectPropertyClass)) or isinstance(self.right, AtomInverse)) and isinstance(self.left, ObjectPropertyClass):
                return True

        return False
