import os
from knowledge_base.KnowledgeBase import KnowledgeBase
from knowledge_base.PetriNetKBPopulator import PetriNetKBPopulator
from pm4py.objects.log.importer.xes import factory as xes_import_factory
from knowledge_base.WorkItemPopulator import WorkItemPopulator
import labelparser.labelparser as lp
import warnings
import pickle
import csv
from collections import Counter

from knowledge_base.SAPDocumentationPopulator import SAPDocumentationPopulator

# load serialized KB rather than populating (RECOMMENDED = True)
load_serialized_kb = True
kb_serial_file = "input/knowledgebase/serializedkb.ser"

# strictness of matching predicate as veried in PoC
STRICT_MATCHING_PREDICATE = True

# expert settings
EQUAL_BOS_IN_POPULATION = False
HEURISTIC_PARSER = True



# Stores which tag is used in respective log to capture the event name
logs = {
    "Hospital Billing - Event Log.xes": "concept:name",
    "BPIC15_1.xes": "activityNameEN",
    "BPIC15_2.xes": "activityNameEN",
    "BPIC15_3.xes": "activityNameEN",
    "BPIC15_4.xes": "activityNameEN",
    "BPIC15_5.xes": "activityNameEN",
    "BPI_2014.xes": "concept:name",
    "BPI_2018.xes": "concept:name",
    "Road_Traffic_Fine_Management_Process.xes": "concept:name",
    "financial_log_modified.xes": "concept:new_name",
    "admission/admission tu munich.xes": "concept:name",
    "admission/admission cologne.xes": "concept:name",
    "admission/admission frankfurt.xes": "concept:name",
    "admission/admission wuerzburg.xes": "concept:name",
    "admission/admission muenster.xes": "concept:name",
    "admission/admission potsdam.xes": "concept:name",
    "admission/admission hohenheim.xes": "concept:name",
    "admission/admission iis erlangen.xes": "concept:name",
    "admission/admission fu berlin.xes": "concept:name"
}


parser = lp.load_default_parser()


def obtain_knowledge_base():
    if not load_serialized_kb:
        kb = KnowledgeBase()
        _populate_knowledge_base(kb)
        pickle.dump(kb, open(kb_serial_file, "wb"))
        return kb
    else:
        kb = pickle.load(open(kb_serial_file, "rb"))
        print("loaded knowledge base from", kb_serial_file)
        return kb


def _populate_knowledge_base(knowledge_base):
    # Ignore deprication warnings from pm4py net import
    def warn(*args, **kwargs):
        pass

    warnings.warn = warn

    # from process model collection.
    populator = PetriNetKBPopulator(equal_bos=EQUAL_BOS_IN_POPULATION, heuristic_parser=HEURISTIC_PARSER)
    dir = "input/knowledgebase/telecommodels/"
    files = os.listdir(dir)
    files = [f for f in files if f.endswith("pnml")]
    for i, file in enumerate(files):
        print(f"({i}) --------------")
        print(dir + file)
        # populator.populate(knowledge_base, os.path.abspath(dir) + "/" + file)

    # from SAP collection
    dir = "input/knowledgebase/sapmodels/"
    files = os.listdir(dir)
    files = [f for f in files if f.endswith("pnml")]
    for i, file in enumerate(files):
        print(f"({i}) --------------")
        print(dir + file)
        populator.populate(knowledge_base, os.path.abspath(dir) + "/" + file)

    # from SAP lifecycles
    populator = SAPDocumentationPopulator()
    populator.populate(knowledge_base, "input/knowledgebase/lifecycles/lifecycles.csv")

    # from work pattern work items
    populator = WorkItemPopulator(10)
    populator.populate(knowledge_base)


def main():
    knowledgebase = obtain_knowledge_base()

    #Create new output file
    with open("output/" + get_output_file_name(), 'w', newline='') as csvfile:
        pass

    for log_file in logs.keys():
        filepath = f"input/logs/{log_file}"
        if os.path.exists(filepath):
            print("loading event log", log_file)
            log = xes_import_factory.apply(filepath)
            analyze_event_log(knowledgebase, log, log_file, logs[log_file], STRICT_MATCHING_PREDICATE)
    print('done')


def analyze_event_log(knowledgebase, log, log_name, event_key, equal_bos):
    violation_counter = Counter()
    parse_map = {}
    paired_violation_map = {}
    coocc_pairs = set()
    print("checking for anomalies in", log_name, "with", len(log), "traces")
    for id in range(len(log)):
        trace = log[id]
        for i in range(len(trace) - 1):
            event1_name = str(trace[i][event_key]).lower()

            for j in range(i + 1, len(trace)):
                event2_name = str(trace[j][event_key]).lower()

                # Check event pair ...
                if event1_name != event2_name:
                    violations = set()
                    # check if event pair already observed
                    if (event1_name, event2_name) in paired_violation_map:
                        violations = paired_violation_map[(event1_name, event2_name)]
                    else:
                        if not HEURISTIC_PARSER:
                        # Parse events
                            e1_parse = parse_event(event1_name, parse_map)
                            e2_parse = parse_event(event2_name, parse_map)

                            # If both contain an action, extract them ...
                            if not equal_bos or e1_parse.bos == e2_parse.bos:
                                if len(e1_parse.actions) > 0 and len(e2_parse.actions) > 0:
                                    verb1 = e1_parse.actions[0]
                                    verb2 = e2_parse.actions[0]
                                    # ... and identify anomalies.
                                    if knowledgebase.exclusion_violation(verb1, verb2):
                                        if verb1 <  verb2:
                                            violations.add("XOR: " + event1_name + "---" + event2_name + " (verbs: " + verb1 + "---" + verb2 + ")")
                                        else:
                                            violations.add("XOR: " + event2_name + "---" + event1_name + " (verbs: " + verb2 + "---" + verb1 + ")")
                                    if knowledgebase.ordering_violation(verb1, verb2):
                                        violations.add(
                                            "order: " + event1_name + "---" + event2_name + " (verbs: " + verb1 + "---" + verb2 + ")")
                                    if knowledgebase.co_occurrence_violation(verb1, verb2):
                                        coocc_pairs.add((event1_name, event2_name))
                                        coocc_pairs.add((event2_name, event1_name))

                        if HEURISTIC_PARSER:
                            if lp.differ_by_one_word(event1_name, event2_name):
                                (verb1, verb2) = lp.get_differences(event1_name, event2_name)
                                if knowledgebase.exclusion_violation(verb1, verb2) or lp.differ_by_negation(event1_name, event2_name):
                                    if event1_name < event2_name:
                                        violations.add("XOR: " + event1_name + "---" + event2_name + " (verbs: " + verb1 + "---" + verb2 + ")")
                                    else:
                                        violations.add("XOR: " + event2_name + "---" + event1_name + " (verbs: " + verb2 + "---" + verb1 + ")")
                                if knowledgebase.ordering_violation(verb1, verb2):
                                    violations.add(
                                        "order: " + event1_name + "---" + event2_name + " (verbs: " + verb1 + "---" + verb2 + ")")
                                if knowledgebase.co_occurrence_violation(verb1, verb2):
                                    coocc_pairs.add((event1_name, event2_name))
                                    coocc_pairs.add((event2_name, event1_name))
                        paired_violation_map[(event1_name, event2_name)] = violations
                    for violation in violations:
                        violation_counter[violation] += 1
    # check for co-occurrence violations
    for id in range(len(log)):
        trace = log[id]
        event_names = [str(event[event_key]).lower() for event in trace]
        for event in event_names:
            for (e1, e2) in coocc_pairs:
                if event == e1 and e2 not in event_names:
                    if e1 < e2:
                        violation = "co-occ: " + e1 + "---" + e2
                        violation_counter[violation] += 1
                    else:
                        violation = "co-occ: " + e2 + "---" + e1
                        violation_counter[violation] += 1

    # write results to file (and stdout)
    file_name = ""
    with open("output/" + get_output_file_name(), 'a', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=';')
        for violation in violation_counter:
            writer.writerow([log_name,equal_bos,HEURISTIC_PARSER,
                             violation[:violation.find(":")],
                             violation[violation.find(": ")+2:violation.find("---")],
                             violation[violation.find("---")+3:],
                             violation_counter[violation]])
            print(violation, "count:", violation_counter[violation])

def parse_event(event_name, parse_map):
    if event_name not in parse_map:
        parse_map[event_name] = parser.parse_label(event_name)
    return parse_map[event_name]


def get_output_file_name():
    output_string = "Violations_"
    if EQUAL_BOS_IN_POPULATION:
        output_string = output_string + "EqBosInPop_"
    else:
        output_string = output_string + "NoEqBosInPop_"
    if STRICT_MATCHING_PREDICATE:
        output_string = output_string + "EqBosInCheck_"
    else:
        output_string = output_string + "NoEqBosInCheck_"
    if HEURISTIC_PARSER:
        output_string = output_string + "Heuristic.csv"
    else:
        output_string = output_string + "NoHeuristic.csv"
    return output_string

if __name__ == '__main__':
    main()
