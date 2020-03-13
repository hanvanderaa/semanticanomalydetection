from enum import Enum, auto
from collections import Counter


class Observation(Enum):
    XOR = 1,
    CO_OCC = 2,
    V1_BEFORE_V2 = 3,
    V2_BEFORE_V1 = 4


class KnowledgeRecord:

    def __init__(self, verb1, verb2, object=None):
        # Instance of KnowledgeRecord consists of two verbs and optionally the specification of an object
        self.verb1 = verb1
        self.verb2 = verb2
        self.object = object
        self.observation_counts = Counter()

    def add_observation(self, observation_type):
        self.observation_counts[observation_type] += 1

    def __str__(self):
        # Prints the record verbs and the number of its occurrence.
        # If same_object + True, the stricter notion is printed.
        return self.verb1 + " - " + self.verb2 + " " + str(self.observation_counts.values())
