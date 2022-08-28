from owlready2 import *
from .classes.axiom import LogicalAxiom
from .classes.atom import Atom, AtomConcept, AtomRole


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

    # – If g=A(x) 
    if isinstance(g, AtomConcept):

        #... and I = [something] ⊑ A
        if (g.get_name() == I_right.name) and (isinstance(I_right, ThingClass)):
           
            # – If g=A(x)   and I = A1 ⊑ A,     then gr(g,I) = A1(x)
            if (isinstance(I_left, ThingClass)):             
                return AtomConcept(I_left.name, g.get_var1())


            # – If g=A(x)   and I = ∃P ⊑ A,     then gr(g,I) = P(x,_);
            if (isinstance(I_left, ObjectPropertyClass)):
                return AtomRole(I.left.name, g.get_var1(), None)

            # – If g=A(x)   and I = ∃P−⊑ A,     then gr(g,I) = P(_,x);
            if (isinstance(I_left, Inverse)):
                return AtomRole(I.left.property.name, None, g.get_var1())


    
    elif isinstance(g, AtomRole):

        if (g.get_name() == I_right.name) and (isinstance(I_right, ObjectPropertyClass)):
           
            # – If g=P(x,_) and I = A ⊑ ∃P,     then gr(g,I) = A(x);
            if (isinstance(I_left, ThingClass)):
                return AtomConcept(I_left.name, g.get_var1())

            # – If g=P(x,_) and I = ∃P1 ⊑ ∃P,   then gr(g,I) = P1(x,_);
            if (isinstance(I_left, ObjectPropertyClass)):
                return AtomRole(I_left.name, g.get_var1(), None)

            # – If g=P(x,_) and I = ∃P1− ⊑ ∃P,  then gr(g,I) = P1(_,x);
            if (isinstance(I_left, Inverse)):
                return AtomRole(I.left.name, None, g.get_var1())

        elif ((isinstance(I_right, Inverse) and g.get_name() == I_right.property.name)):

            # – If g=P(_,x) and I = A ⊑ ∃P−,    then gr(g,I) = A(x);
            if (isinstance(I_left, ThingClass)):
                return AtomConcept(I_left.name, g.get_var2())

            # – If g=P(_,x) and I = ∃P1 ⊑ ∃P−,  then gr(g,I) = P1(x,_);
            if (isinstance(I_left, ObjectPropertyClass)):
                return AtomRole(I_left.name, g.get_var2(), None)

            # – If g=P(_,x) and I = ∃P1− ⊑∃P−,  then gr(g,I) = P1(_,x);
            if (isinstance(I_left, Inverse)):
                return AtomRole(I.left.name, None, g.get_var2())

        else:
            pass
        # – If g=P(x1,x2) and either I = P1 ⊑ P or I = P1− ⊑ P−, then gr(g,I) = P1(x1, x2);
        # – If g=P(x1,x2) and either I = P1 ⊑ P− or P1− ⊑ P,     then gr(g,I) = P1(x2, x1).

    else:
        pass

    return

def new_query(q, g, I):
    new_atom = atoms_obtained(q, g, I)
    new_body = list()

    for at in q:
        if (at.get_name() == g.get_name()):
            new_body.append(new_atom)
        else:
            new_body.append(at)
    

    return new_body