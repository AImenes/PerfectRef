from owlready2 import *

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
    


    