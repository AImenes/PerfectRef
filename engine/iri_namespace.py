from .classes.query import Query, QueryBody
from .classes.atom import AtomParser, AtomConcept, AtomRole, AtomConstant
from .classes.entry import Variable, Constant

def get_iri_and_namespace(q, tbox):
    classes = list(tbox.classes())
    properties = list(tbox.properties())

    #for every atom in q
    for g in q.get_body().get_body():
        
        
        #Classes
        matches = list()
        counter = 0

        #for every class
        for cl in classes:

            #if atom name equals class name
            if g.get_name() == cl.name:

                #save class
                matches.append(cl)

                #add to counter
                counter += 1

        #if counter is 1
        if counter == 1:

            #set namespace and iri
            #g.set_namespace(matches[0].namespace.ontology)
            g.set_iri(matches[0].iri)

        #elif counter > 1
        elif counter > 1:

            for i in range(len(matches)):
                print(str(i) + ":\t" + matches[i].iri)

            option = None
            while not (isinstance(option, int) and option < len(matches)):
                option = int(input("Select the ID of the wanted IRI (0-" + str(len(matches)-1) + "): "))

            #set namespace and iri
           #g.set_namespace(matches[option].namespace.ontology)
            g.set_iri(matches[option].iri)



        #Properties
        matches = list()
        counter = 0
        #for every property
        for pp in properties:

            #if atom name equals class name
            if g.get_name() == pp.name:

                #save class
                matches.append(pp)

                #add to counter
                counter += 1

        #if counter is 1
        if counter == 1:

            #set namespace and iri
            #g.set_namespace(matches[0].namespace.ontology)
            g.set_iri(matches[0].iri)

        #elif counter > 1
        elif counter > 1:

            for i in range(len(matches)):
                print(str(i) + ":\t" + matches[i].iri)

            option = None
            while not (isinstance(option, int) and option < len(matches)):
                option = int(input("Select the ID of the wanted IRI (0-" + str(len(matches)-1) + "): "))

            #set namespace and iri
           #g.set_namespace(matches[option].namespace.ontology)
            g.set_iri(matches[option].iri)