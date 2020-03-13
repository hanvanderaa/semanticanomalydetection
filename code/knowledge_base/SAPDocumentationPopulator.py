from knowledge_base.KnowledgeBase import KnowledgeBase
from knowledge_base.KnowledgeRecord import Observation

import csv

class SAPDocumentationPopulator:

    def __init__(self):
        pass

    def populate(self, knowledge_base: KnowledgeBase, path_to_csv):
        # Parses csv and stores content in knowledge base
        with open(path_to_csv, newline='') as csvfile:
            content = csv.reader(csvfile, delimiter=";")
            for row in content:
                object = row[0]
                verb1 = row[1]
                verb2 = row[2]
                type = vars(Observation)[row[3]]
                weight = int(row[4])
                for i in range(weight):
                    knowledge_base.add_observation(verb1, verb2, type)

        return