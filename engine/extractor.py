from .classes.atom import AtomConcept, AtomConstant


#Export the entailed queries to file.
def export_query_to_file(PR, query, q_head):
    
    f = open("demofile2.txt", "w")
    f.write("Original query: \n%s \n\n" % (query))
    f.write("Entailed query:\n")
    
    for q in PR:
        f.write(q_head.get_name() + "(" + q_head.get_var1().get_represented_name() + ") :- ")
        length_of_q = len(q.get_body())
        counter = 0
        for g in q.get_body():
            
            if isinstance(g, AtomConstant):
                pass
            elif isinstance(g, AtomConcept):
                f.write(g.get_name() + "(" + g.get_var1().get_represented_name() + ")")
            else:
                f.write(g.get_name() + "(" + g.get_var1().get_represented_name() + "," + g.get_var2().get_org_name() + ")")

            if (counter < length_of_q - 1):
                f.write("^")

            counter += 1

        f.write("\n")

    f.close()

def print_query(PR, query, q_head):
    print("Original query: \n%s \n\n" % (query))
    print("Entailed queries:\n")   

    for q in PR:
            print(q_head.get_name() + "(" + q_head.get_var1().get_represented_name() + ") :- ", end=" ")
            length_of_q = len(q.get_body())
            counter = 0
            for g in q.get_body():
                
                if isinstance(g, AtomConstant):
                    pass
                elif isinstance(g, AtomConcept):
                    print(g.get_name() + "(" + g.get_var1().get_represented_name() + ")")
                else:
                    print(g.get_name() + "(" + g.get_var1().get_represented_name() + "," + g.get_var2().get_org_name() + ")")

                if (counter < length_of_q - 1):
                    print("^")

                counter += 1
