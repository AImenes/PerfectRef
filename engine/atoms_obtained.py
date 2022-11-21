from owlready2 import *
from .classes.query import QueryBody
from .classes.axiom import LogicalAxiom
from .classes.atom import AtomConcept, AtomRole, AtomInverse
from .classes.entry import Variable
from copy import deepcopy

# Importing the PIs from the T-box
def get_axioms(ontology, only_PIs):
    classes = list(ontology.classes())
    properties = list(ontology.properties())
    list_of_axioms = list()

    #Remove restrictions
    for cl in classes:
        if not (type(cl) == ThingClass or type(cl) == ObjectPropertyClass):
            classes.remove(cl)


    for pt in properties:
        if not (type(pt) == ThingClass or type(pt) == ObjectPropertyClass):
            properties.remove(pt)

    # Add sub- and superclasses
    for cl in classes:
        superclasses = cl.is_a
        
        for sup in superclasses:
            if (type(sup) == ObjectPropertyClass or type(sup) == ThingClass or type(sup) == Inverse or type(sup) == InverseFunctionalProperty) and not sup.name == "Thing":

            #if not a restriction
            #if not (type(sup) == Restriction):

                #if not superclass is top domain
                #if (not sup.name == "Thing"):
                    
                    #if not type(sup) == Or:
                list_of_axioms.append(LogicalAxiom((cl), (sup)))
                    #else:
                    #    for cc in sup.Classes:
                    #        list_of_axioms.append(LogicalAxiom((cl), (cc)))


    #Properties
    for prop in properties:

        super_property = prop.is_a

        for sup in super_property:
            if (type(sup) == ObjectPropertyClass or type(sup) == ThingClass or type(sup) == Inverse or type(sup) == InverseFunctionalProperty) and not (sup.name == "topObjectProperty" or sup.name == "ObjectProperty"):
           # if type(sup) == InverseFunctionalProperty:
            #    print("ggß")


            #if not (type(sup) == Restriction or type(sup) == And):
            #    if not sup.name == "ObjectProperty" or sup.name == "InverseFunctionalProperty":
            #        if not type(sup) == Or:
                #print(sup.inverse_property)
                list_of_axioms.append(LogicalAxiom(prop, sup))
            #    list_of_axioms.append(LogicalAxiom(AtomInverse(prop), AtomInverse(sup)))
            #        else:
            #            for cc in sup.Properties:
            #                list_of_axioms.append(LogicalAxiom(prop, cc))


        if not prop.domain is None:

            for dom in prop.domain:

                if (type(dom) == ObjectPropertyClass or type(dom) == ThingClass or type(dom) == Inverse or type(dom) == InverseFunctionalProperty) and not dom.name == "Thing":
                    new_axiom = LogicalAxiom(prop, dom)
                    if not new_axiom in list_of_axioms:
                        list_of_axioms.append(new_axiom)


        if not prop.range is None:
            for ran in prop.range:
                if (type(ran) == ObjectPropertyClass or type(ran) == ThingClass or type(ran) == Inverse or type(ran) == InverseFunctionalProperty) and not ran.name == "Thing":
                        
                        #If an inverse of the property actually exists
                        if type(Inverse(prop)) == Inverse:
                            new_axiom = LogicalAxiom(AtomInverse(prop), ran)
                            if not new_axiom in list_of_axioms:
                                list_of_axioms.append(new_axiom)
                        else:
                            new_axiom = LogicalAxiom(Inverse(prop), ran)
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
        if (g.get_name() == I_right.name) and (isinstance(I_right, ThingClass)):
           
            # – If g=A(x)   and I = A1 ⊑ A,     then gr(g,I) = A1(x)
            if (isinstance(I_left, ThingClass)):             
                return AtomConcept(I_left.name, g.get_var1())

            # – If g=A(x)   and I = ∃P ⊑ A,     then gr(g,I) = P(x,_);
            if (isinstance(I_left, ObjectPropertyClass)):
                return AtomRole(I_left.name, g.get_var1(), dummy_unbound_variable, False)

            # – If g=A(x)   and I = ∃P−⊑ A,     then gr(g,I) = P(_,x);
            if (isinstance(I_left, AtomInverse)):
                return AtomRole(I_left.get_atom().name, dummy_unbound_variable, g.get_var1(), True)


    
    elif isinstance(g, AtomRole):

#        if (g.get_name() == I_right.name) and g.get_var2().get_unbound() and (isinstance(I_right, ObjectPropertyClass)):
        if (g.get_name() == I_right.name) and g.get_var2().get_unbound() and (isinstance(I_right, ObjectPropertyClass)):

            # – If g=P(x,_) and I = A ⊑ ∃P,     then gr(g,I) = A(x);
            if (isinstance(I_left, ThingClass)):
                return AtomConcept(I_left.name, g.get_var1())

            # – If g=P(x,_) and I = ∃P1 ⊑ ∃P,   then gr(g,I) = P1(x,_);
            if (isinstance(I_left, ObjectPropertyClass)):
                return AtomRole(I_left.name, g.get_var1(), dummy_unbound_variable, False)

            # – If g=P(x,_) and I = ∃P1− ⊑ ∃P,  then gr(g,I) = P1(_,x);
            if (isinstance(I_left, AtomInverse)):
                return AtomRole(I_left.get_atom().name, dummy_unbound_variable, g.get_var1(), True)

        elif ((isinstance(I_right, AtomInverse) and g.get_var1().get_unbound() and g.get_name() == I_right.get_atom().name)):
            
            # – If g=P(_,x) and I = A ⊑ ∃P−,    then gr(g,I) = A(x);
            if (isinstance(I_left, ThingClass)):
                return AtomConcept(I_left.name, g.get_var2())

            # – If g=P(_,x) and I = ∃P1 ⊑ ∃P−,  then gr(g,I) = P1(x,_);
            if (isinstance(I_left, ObjectPropertyClass)):
                return AtomRole(I_left.name, g.get_var2(), dummy_unbound_variable, False)

            # – If g=P(_,x) and I = ∃P1− ⊑ ∃P−,  then gr(g,I) = P1(_,x);
            if (isinstance(I_left, AtomInverse)):
                return AtomRole(I_left.get_atom().name, dummy_unbound_variable, g.get_var2(), True)

        # - Added special case since ∃P1 ⊑ ∃P applies to g=P(_,x) since ∃P1- ⊑ ∃P- is implied by ∃P1 ⊑ ∃P
        elif ((isinstance(I_right, ObjectPropertyClass) and g.get_var1().get_unbound() and g.get_name() == I_right.name)):

            # – If g=P(_,x) and I = ∃P1 ⊑ ∃P,   then gr(g,I) = P1(_,x);
            if (isinstance(I_left, ObjectPropertyClass)):
                return AtomRole(I_left.name, g.get_var1(), dummy_unbound_variable, True)

         # – If g=P(x1,x2)
        elif (g.get_var1().get_bound() and g.get_var2().get_bound() and not (isinstance(I_left, ThingClass))): 
       
        # – If g=P(x1,x2) and either I = P1 ⊑ P or I = P1− ⊑ P−, then gr(g,I) = P1(x1, x2);
            if (isinstance(I_left, ObjectPropertyClass) and isinstance(I_right, ObjectPropertyClass) and (g.get_name() == I_right.name)):
                return AtomRole(I_left.name, g.get_var1(), g.get_var2(), False)

            if (isinstance(I_left, AtomInverse) and isinstance(I_right, AtomInverse) and g.get_name() == I_right.get_atom().name):
                return AtomRole(I_left.get_atom().name, g.get_var1(), g.get_var2(), False)


        # – If g=P(x1,x2) and either I = P1 ⊑ P− or P1− ⊑ P,     then gr(g,I) = P1(x2, x1).
            if (isinstance(I_left, ObjectPropertyClass) and isinstance(I_right, AtomInverse) and (g.get_name() == I_right.get_atom().name)):
                return AtomRole(I_left.name, g.get_var2(), g.get_var1(), True)

            if (isinstance(I_left, AtomInverse) and isinstance(I_right, ObjectPropertyClass) and g.get_name() == I_right.name):
                return AtomRole(I_left.get_atom().name, g.get_var2(), g.get_var1(), True)

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

    for at in new_q.get_body():
        if (at.get_name() == g.get_name()):
            new_body.append(entailed_atom)
        else:
            new_body.append(at)

    return QueryBody(new_body)