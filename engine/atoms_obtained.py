from owlready2 import *
from .classes.query import QueryBody
from .classes.axiom import LogicalAxiom
from .classes.atom import AtomConcept, AtomRole
from .classes.entry import Variable
from copy import deepcopy

# Importing the PIs from the T-box
def get_axioms(ontology, only_PIs):
    classes = list(ontology.classes())
    properties = list(ontology.properties())
    list_of_axioms = list()

    # Add sub- and superclasses
    for cl in classes:
        superclasses = cl.is_a
        
        for sup in superclasses:

            if not sup.name == "Thing":
                
                list_of_axioms.append(LogicalAxiom((cl), (sup)))

    #Properties
    for prop in properties:
        super_property = prop.is_a

        for sup in super_property:

            if not sup.name == "ObjectProperty":
                
                list_of_axioms.append(LogicalAxiom(prop, sup))

        if not prop.domain is None:
            
            for dom in prop.domain:
                list_of_axioms.append(LogicalAxiom(dom, prop))

        if not prop.range is None:

            for ran in prop.range:
                list_of_axioms.append(LogicalAxiom(Inverse(prop), ran))

    #Select PIs from the CIs
    if only_PIs:
        for ax in list_of_axioms:
            if (isinstance(ax.get_left(), Not) and not isinstance(ax.get_right(), Not)) or (not isinstance(ax.get_left(), Not) and isinstance(ax.get_right(), Not)):
                list_of_axioms.remove(ax)         

    return list_of_axioms


def atoms_obtained(q, g, I):

    I_left = I.get_left()
    I_right = I.get_right()
    dummy_dict_unbound = {'is_distinguished': False, 'in_body': False, 'is_shared': False, 'is_bound': False}
    dummy_unbound_variable = Variable("?_", dummy_dict_unbound)

    # – If g=A(x) 
    if isinstance(g, AtomConcept):

        #... and I = [something] ⊑ A
        if (g.get_name() == I_right.name) and (isinstance(I_right, ThingClass)):
           
            # – If g=A(x)   and I = A1 ⊑ A,     then gr(g,I) = A1(x)
            if (isinstance(I_left, ThingClass)):             
                return AtomConcept(I_left.name, g.get_var1())

            # – If g=A(x)   and I = ∃P ⊑ A,     then gr(g,I) = P(x,_);
            if (isinstance(I_left, ObjectPropertyClass)):
                return AtomRole(I.left.name, g.get_var1(), dummy_unbound_variable)

            # – If g=A(x)   and I = ∃P−⊑ A,     then gr(g,I) = P(_,x);
            if (isinstance(I_left, Inverse)):
                return AtomRole(I.left.property.name, dummy_unbound_variable, g.get_var1())


    
    elif isinstance(g, AtomRole):

        if (g.get_name() == I_right.name) and g.get_var2().get_unbound() and (isinstance(I_right, ObjectPropertyClass)):

            # – If g=P(x,_) and I = A ⊑ ∃P,     then gr(g,I) = A(x);
            if (isinstance(I_left, ThingClass)):
                return AtomConcept(I_left.name, g.get_var1())

            # – If g=P(x,_) and I = ∃P1 ⊑ ∃P,   then gr(g,I) = P1(x,_);
            if (isinstance(I_left, ObjectPropertyClass)):
                return AtomRole(I_left.name, g.get_var1(), dummy_unbound_variable)

            # – If g=P(x,_) and I = ∃P1− ⊑ ∃P,  then gr(g,I) = P1(_,x);
            if (isinstance(I_left, Inverse)):
                return AtomRole(I.left.name, dummy_unbound_variable, g.get_var1())

        elif ((isinstance(I_right, Inverse) and g.get_var1().get_unbound() and g.get_name() == I_right.property.name)):
            # – If g=P(_,x) and I = A ⊑ ∃P−,    then gr(g,I) = A(x);
            if (isinstance(I_left, ThingClass)):
                return AtomConcept(I_left.name, g.get_var2())

            # – If g=P(_,x) and I = ∃P1 ⊑ ∃P−,  then gr(g,I) = P1(x,_);
            if (isinstance(I_left, ObjectPropertyClass)):
                return AtomRole(I_left.name, g.get_var2(), dummy_unbound_variable)

            # – If g=P(_,x) and I = ∃P1− ⊑∃P−,  then gr(g,I) = P1(_,x);
            if (isinstance(I_left, Inverse)):
                return AtomRole(I_left.name, dummy_unbound_variable, g.get_var2())

         # – If g=P(x1,x2)
        elif (g.get_var1().get_bound() and g.get_var2().get_bound() and not (isinstance(I_left, ThingClass))): 
       
        # – If g=P(x1,x2) and either I = P1 ⊑ P or I = P1− ⊑ P−, then gr(g,I) = P1(x1, x2);
            if (isinstance(I_left, ObjectPropertyClass) and isinstance(I_right, ObjectPropertyClass) and (g.get_name() == I_right.name)) or (isinstance(I_left, Inverse) and isinstance(I_right, Inverse) and g.get_name() == I_right.property.name):
                return AtomRole(I_left.name, g.get_var1(), g.get_var2())
                

        # – If g=P(x1,x2) and either I = P1 ⊑ P− or P1− ⊑ P,     then gr(g,I) = P1(x2, x1).
            if (isinstance(I_left, ObjectPropertyClass) and isinstance(I_right, Inverse) and (g.get_name() == I_right.property.name)) or (isinstance(I_left, Inverse) and isinstance(I_right, ObjectPropertyClass) and g.get_name() == I_right.name):
                return AtomRole(I_left.name, g.get_var2(), g.get_var1())

    else:
        return None


def new_query(q, g, I):
    new_q = deepcopy(q)
    new_g = deepcopy(g)

    entailed_atom = atoms_obtained(new_q, new_g, I)
    
    new_body = list()

    for at in new_q.get_body():
        if (at.get_name() == g.get_name()):
            new_body.append(entailed_atom)
        else:
            new_body.append(at)
    
    return QueryBody(new_body)