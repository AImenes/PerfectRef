from turtle import left


class Axiom:
    def __init__(self):
        pass

class LogicalAxiom(Axiom):
    def __init__(self, left, right):
        super().__init__()
        self.left = left
        self.right = right
        
    def is_applicable(self, atom):
        pass