from .classes.atom import AtomConcept, AtomConstant


#Export the entailed queries to file.
def export_query_to_file(PR, query, q_head):
    
    f = open("demofile2.txt", "w")
    f.write("Original query: \n%s \n\n" % (query))
    f.write("Entailed query:\n")
    
    for q in PR:
        f.write(q_head.name + "(" + q_head.var1.represented_name + ") :- ")
        length_of_q = len(q.body)
        counter = 0
        for g in q.body:
            
            if isinstance(g, AtomConstant):
                pass
            elif isinstance(g, AtomConcept):
                f.write(g.name + "(" + g.var1.represented_name + ")")
            else:
                f.write(g.name + "(" + g.var1.represented_name + "," + g.var2.original_entry_name + ")")

            if (counter < length_of_q - 1):
                f.write("^")

            counter += 1

        f.write("\n")

    f.close()

def print_query(PR, query, q_head):
    print("Original query: \n%s \n\n" % (query))
    print("Entailed queries:\n")   

    for q in PR:
            print(q_head.name + "(" + q_head.var1.represented_name + ") :- ", end=" ")
            length_of_q = len(q.body)
            counter = 0
            for g in q.body:
                
                if isinstance(g, AtomConstant):
                    pass
                elif isinstance(g, AtomConcept):
                    print(g.name + "(" + g.var1.represented_name + ")",end="")
                else:
                    print(g.name + "(" + g.var1.represented_name + "," + g.var2.original_entry_name + ")",end="")

                if (counter < length_of_q - 1):
                    print("^",end="")

                counter += 1
            print("\n")
