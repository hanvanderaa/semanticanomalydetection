from knowledgebase.knowledgebase import KnowledgeBase
from knowledgebase.knowledgerecord import Observation

import csv

rel_to_observation = {"antonymy": Observation.XOR,
                      "opposite-of": Observation.XOR,
                      "can-result-in": Observation.CO_OCC,
                      "happens-before": Observation.ORDER}


def populate(knowledge_base, input_file, count_per_record = 1):
    # Parses csv and stores content in knowledge base
    candidates = set()
    with open(input_file) as f:
        line = f.readline()
        while line:
            if not line.startswith("#"):
                (verb1, rel, verb2, conf) = _line_to_tuple(line)
                if rel in rel_to_observation:
                    observation_type = rel_to_observation[rel]
                    candidates.add((verb1, verb2, observation_type))
            line = f.readline()
    added = set()
    # filter out false antonyms
    for (verb1, verb2, observation_type) in candidates:
        if observation_type in (Observation.ORDER, Observation.CO_OCC):
            print('adding VO_rel:', verb1, verb2)
            knowledge_base.add_observation(verb1, verb2, observation_type, count = count_per_record)
        if observation_type is Observation.XOR:
            if (verb1, verb2, Observation.ORDER) not in candidates and (
            verb2, verb1, Observation.ORDER) not in candidates:
                if (verb2, verb1, observation_type) not in added:
                    print('adding VO_rel:', verb1, verb2)
                    knowledge_base.add_observation(verb1, verb2, observation_type, count = count_per_record)
                    added.add( (verb1, verb2, observation_type))
    print('finished populating based on VerbOcean')


# def _add_rel_to_kb(knowledgebase, verb1, rel, verb2):
#     rel_to_observation = {"antonymy": Observation.XOR,
#                           "opposite-of": Observation.XOR,
#                           "can-result-in": Observation.CO_OCC,
#                           "happens-before": Observation.V1_BEFORE_V2}
#     if rel in rel_to_observation:
#         knowledgebase.add_observation(verb1, verb2, rel_to_observation[rel])


def _line_to_tuple(line):
    start_br = line.find('[')
    end_br = line.find(']')
    conf_delim = line.find('::')
    verb1 = line[:start_br].strip()
    rel = line[start_br + 1: end_br].strip()
    verb2 = line[end_br + 1: conf_delim].strip()
    conf = line[conf_delim: len(line)].strip()
    return (verb1, rel, verb2, conf)
