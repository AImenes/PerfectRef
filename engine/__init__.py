from owlready2 import *
from .classes.query import Query, QueryBody
from .classes.axiom import LogicalAxiom
from .classes.atom import AtomConcept, AtomRole, AtomConstant
from .classes.entry import Variable
from .reduce import reduce
from .unify import unifiable
from .atoms_obtained import new_query
from .query_parser import update_processed_status, update_body, update_role, update_concept, update_atom

