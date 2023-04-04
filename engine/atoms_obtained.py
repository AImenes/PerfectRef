from owlready2 import *
from .classes.query import QueryBody
from .classes.axiom import LogicalAxiom
from .classes.atom import AtomConcept, AtomRole, AtomInverse
from .classes.entry import Variable
from copy import deepcopy

# Importing the PIs from the T-box
def get_axioms(ontology, only_PIs):
    classes = list(ontology.classes())
    properties = list(ontology.object_properties())
    list_of_axioms = list()

    # Add sub- and superclasses
    for cl in classes:
        superclasses = cl.is_a
        
        for sup in superclasses:
            if (type(sup) == ThingClass and not sup.name == "Thing"):
                list_of_axioms.append(LogicalAxiom(cl, sup))

            if(type(sup) == Restriction):
                #OWLReady2 ID for SOME-Restriction is 24
                if sup.type == 24:
                    list_of_axioms.append(LogicalAxiom(cl, sup.property))
                

    #Properties
    for prop in properties:
        super_property = prop.is_a

        #Super Property
        for sup in super_property:
            if (type(sup) == ObjectPropertyClass or type(sup) == ThingClass or type(sup) == Inverse or type(sup) == InverseFunctionalProperty) and not (sup.name == "topObjectProperty" or sup.name == "ObjectProperty"):
                list_of_axioms.append(LogicalAxiom(prop, sup))


        #Domain
        if not prop.domain is None:
            for dom in prop.domain:
                if (type(dom) == ObjectPropertyClass or type(dom) == ThingClass or type(dom) == Inverse or type(dom) == InverseFunctionalProperty) and not dom.name == "Thing":
                    new_axiom = LogicalAxiom(prop, dom)
                    if not new_axiom in list_of_axioms:
                        list_of_axioms.append(new_axiom)

        #Range
        if not prop.range is None:
            for ran in prop.range:
                if (type(ran) == ObjectPropertyClass or type(ran) == ThingClass or type(ran) == Inverse or type(ran) == InverseFunctionalProperty) and not ran.name == "Thing":
                    new_axiom = LogicalAxiom(Inverse(prop, simplify=False), ran)
                    if not new_axiom in list_of_axioms:
                        list_of_axioms.append(new_axiom)

        #Inverse
        if not prop.inverse is None:
            if (type(prop.inverse) == ObjectPropertyClass or type(prop.inverse) == ThingClass or type(prop.inverse) == Inverse or type(prop.inverse) == InverseFunctionalProperty) and not prop.inverse.name == "Thing":
                new_axiom = LogicalAxiom(Inverse(prop,simplify=False),prop)
                if not new_axiom in list_of_axioms:
                    list_of_axioms.append(new_axiom)


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
        if (g.get_iri() == I_right.iri) and (isinstance(I_right, ThingClass)):
           
            # – If g=A(x)   and I = A1 ⊑ A,     then gr(g,I) = A1(x)
            if (isinstance(I_left, ThingClass)):             
                return AtomConcept(I_left.name, g.get_var1(), I_left.iri)

            # – If g=A(x)   and I = ∃P ⊑ A,     then gr(g,I) = P(x,_);
            if (isinstance(I_left, ObjectPropertyClass)):
                return AtomRole(I_left.name, g.get_var1(), dummy_unbound_variable, False, I_left.iri)

            # – If g=A(x)   and I = ∃P−⊑ A,     then gr(g,I) = P(_,x);
            if (isinstance(I_left, Inverse)):
                return AtomRole(I_left.property.name, dummy_unbound_variable, g.get_var1(), True, I_left.property.iri)


    
    elif isinstance(g, AtomRole):

        if ((not isinstance(I_right, Inverse)) and g.get_iri() == I_right.iri) and g.get_var2().get_unbound() and (isinstance(I_right, ObjectPropertyClass)):


            # – If g=P(x,_) and I = A ⊑ ∃P,     then gr(g,I) = A(x);
            if (isinstance(I_left, ThingClass)):
                return AtomConcept(I_left.name, g.get_var1(), I_left.iri)

            # – If g=P(x,_) and I = ∃P1 ⊑ ∃P,   then gr(g,I) = P1(x,_);
            if (isinstance(I_left, ObjectPropertyClass)):
                return AtomRole(I_left.name, g.get_var1(), dummy_unbound_variable, False, I_left.iri)

            # – If g=P(x,_) and I = ∃P1− ⊑ ∃P,  then gr(g,I) = P1(_,x);
            if (isinstance(I_left, Inverse)):
                return AtomRole(I_left.property.name, dummy_unbound_variable, g.get_var1(), True, I_left.property.iri)

        elif ((isinstance(I_right, Inverse) and g.get_var1().get_unbound() and g.get_iri() == I_right.property.iri)):
            
            # – If g=P(_,x) and I = A ⊑ ∃P−,    then gr(g,I) = A(x);
            if (isinstance(I_left, ThingClass)):
                return AtomConcept(I_left.name, g.get_var2(), I_left.iri)

            # – If g=P(_,x) and I = ∃P1 ⊑ ∃P−,  then gr(g,I) = P1(x,_);
            if (isinstance(I_left, ObjectPropertyClass)):
                return AtomRole(I_left.name, g.get_var2(), dummy_unbound_variable, False, I_left.iri)

            # – If g=P(_,x) and I = ∃P1− ⊑ ∃P−,  then gr(g,I) = P1(_,x);
            if (isinstance(I_left, Inverse)):
                return AtomRole(I_left.property.name, dummy_unbound_variable, g.get_var2(), True, I_left.property.iri)


         # – If g=P(x1,x2) - ROLE INCLUSION
        elif (g.get_var1().get_bound() and g.get_var2().get_bound() and not (isinstance(I_left, ThingClass))): 
       
        # – If g=P(x1,x2) and either I = P1 ⊑ P or I = P1− ⊑ P−, then gr(g,I) = P1(x1, x2);
            if (isinstance(I_left, ObjectPropertyClass) and isinstance(I_right, ObjectPropertyClass) and (g.get_iri() == I_right.iri)):
                return AtomRole(I_left.name, g.get_var1(), g.get_var2(), False, I_left.iri)

            if (isinstance(I_left, Inverse) and isinstance(I_right, Inverse) and g.get_iri() == I_right.property.iri):
                return AtomRole(I_left.property.name, g.get_var1(), g.get_var2(), False, I_left.property.iri)


        # – If g=P(x1,x2) and either I = P1 ⊑ P− or P1− ⊑ P,     then gr(g,I) = P1(x2, x1).
            if (isinstance(I_left, ObjectPropertyClass) and isinstance(I_right, Inverse) and (g.get_iri() == I_right.property.iri)):
                return AtomRole(I_left.name, g.get_var2(), g.get_var1(), True, I_left.iri)

            if (isinstance(I_left, Inverse) and isinstance(I_right, ObjectPropertyClass) and g.get_iri() == I_right.iri):
                return AtomRole(I_left.property.name, g.get_var2(), g.get_var1(), True, I_left.property.iri)

        else:
            print("something went wrong")
            return None
    else:
        return None


def new_query(q, g, I):
    new_q = deepcopy(q)
    new_g = deepcopy(g)

    entailed_atom = atoms_obtained(new_q, new_g, I)

    if entailed_atom is None:
        return None

    new_body = list()

    for atom in new_q.get_body():
        #For roles
        if isinstance(atom, AtomRole):
            if atom.get_iri() == g.get_iri() and atom.var1 == g.var1 and atom.var2 == g.var2:
                new_body.append(entailed_atom)
            else:
                new_body.append(atom)
        #For concepts
        elif isinstance(atom, AtomConcept):
            if atom.get_iri() == g.get_iri() and atom.var1 == g.var1:
                new_body.append(entailed_atom)
            else:
                new_body.append(atom)

    return QueryBody(new_body)