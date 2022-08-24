def create_logical_axioms(classes, properties):
    axioms = {}

    for class in classes:
        axioms.add(get_superclass())

    for prop in properties:
        
