from enum import Enum, auto
from collections import Counter



class Observation(Enum):
    XOR = 1,
    CO_OCC = 2,
    ORDER = 3

class KnowledgeRecord:

    def __init__(self, verb1, verb2, record_type, count = 1):
        # Instance of KnowledgeRecord consists of two verbs and optionally the specification of an object
        self.verb1 = verb1
        self.verb2 = verb2
        self.record_type = record_type
        self.count = count

    def increment_count(self, count):
        self.count += count

    def __repr__(self):
        return str(self.record_type) + ": " + self.verb1 + " - " + self.verb2 + " count: " + str(self.count)
