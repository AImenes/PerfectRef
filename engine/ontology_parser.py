from owlready2 import *
from .classes.axiom import Axiom
from .classes.axiom import LogicalAxiom


def import_ontology(path):
    onto = get_ontology(path).load()
    #print(onto.base_iri)
    #print(onto.imported_ontologies)
    classes = list(onto.classes())
    print("These are the classes: %s. They are of type %s" % (classes, type(classes[0])))
    print(classes[1].is_a)
    print(classes[1].is_instance_of)
    properties = list(onto.properties())
    print("These are the properties: %s. They are of type %s" % (properties, type(properties[0])))

    print("Example property and its domains and ranges: ")
    dom = properties[0].domain
    ran = properties[0].range
    print("Property: %s, of type %s" % (properties[0], type(properties[0])))
    print("Domain: %s, of type %s" % (properties[0].domain, type(dom)))
    print("Range: %s, of type %s" % (properties[0].range, type(ran)))

    return onto 
    
def get_axioms(ontology):
    classes = list(ontology.classes())
    properties = list(ontology.properties())
    list_of_axioms = list()

    # Add sub- and superclasses
    for cl in classes:
        superclasses = cl.is_a
        
        for sup in superclasses:

            if not sup.name == "Thing":
                
                list_of_axioms.append(LogicalAxiom(cl, sup))


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
                list_of_axioms.append(LogicalAxiom(ran, prop))
    
    print("halt")
    return list_of_axioms


    