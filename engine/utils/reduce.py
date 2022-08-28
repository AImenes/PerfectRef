#ReduceMethod

# Should return the most general unifier between g1 and g2
def reduce(q, pair):
    g1, g2 = pair

    #Concepts

    #Roles
    
    new_body = list()

    for at in q:
        if (at.get_name() == g.get_name()):
            new_body.append(new_atom)
        else:
            new_body.append(at)

    return new_body
