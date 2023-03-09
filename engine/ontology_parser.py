from owlready2 import *

def import_ontology(path):
    onto = get_ontology(path).load()
    #print(onto.base_iri)
    #print(onto.imported_ontologies)
    classes = list(onto.classes())
    #print("These are the classes: \n%s. They are of type %s\n" % (classes, type(classes[0])))

    properties = list(onto.properties())
    #print("These are the properties: \n%s. They are of type %s\n\n" % (properties, type(properties[0])))

    return onto 
    


    